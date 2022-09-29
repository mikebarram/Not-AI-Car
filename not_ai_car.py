# import the pygame module, so you can use it
from asyncio.windows_events import NULL
import pygame, sys
import numpy as np
import random
import math
from scipy.interpolate import splprep, splev
from scipy.ndimage.filters import uniform_filter1d

BLACK = (0, 0, 0)
WHITE = (200, 200, 200)
RED = (255, 0, 0)
START_COLOUR = (200, 200, 0)
SQUARE_SIZE = 130
ROWS = 6
COLS = 10
TRACK_MIN_WIDTH = 15
TRACK_MAX_WIDTH = 45
TRACK_CURVE_POINTS = ROWS * COLS * 10
TRACK_MIDLINE_COLOUR = WHITE

WINDOW_WIDTH = COLS * SQUARE_SIZE
WINDOW_HEIGHT = ROWS * SQUARE_SIZE

# cars can only look so far ahead. Needs to be somewhat larger than the maximum track width - try seting that distance to the size of a grid square
CAR_VISION_DISTANCE = round(2.5 * SQUARE_SIZE)
#CAR_VISION_ANGLES = (0, -10, 10, -20, 20, -30, 30, -45, 45, -60, 60, -80, 80, -90, 90) # 0 must be first
CAR_VISION_ANGLES = (0, -20, 20, -45, 45, -60, 60, -90, 90) # 0 must be first
CAR_SPEED_MIN = 2 # pixels per frame
CAR_SPEED_MAX = 15 # pixels per frame
CAR_ACCELERATION_MIN = -4 # change in speed in pixels per frame
CAR_ACCELERATION_MAX = 2 # change in speed in pixels per frame
CAR_PATH_COLOUR = RED
        
class Car():
    def __init__(self, screen, track):
        self.screen = screen
        self.track = track

        #if isinstance(position, tuple):
        #    if isinstance(position[0], int) and isinstance(position[1], int):
        #        self.position = (int(position[0]),int(position[1]))
        #    else:            
        #        raise (TypeError, "expected a tuple of integers")
        #else:
        #    raise (TypeError, "expected a tuple")
        
        # actual position is recorded as a tuple of floats
        # position is rounded just for display and to see if the car is still on the track
        self.position = (self.track.scaled_track[0][0],self.track.scaled_track[0][1]) #this should be a tuple of integers. interpolated_scaled_track[0] will be float
        self.position_rounded = (round(self.position[0]),round(self.position[1]))
        self.speed = SQUARE_SIZE/50  # pixels per frame
        self.direction_radians = track.GetInitialDirectionRadians()
        self.steering_radians = 0
        self.crashed = False

    def Drive(self):
        track_edge_distances = self.GetTrackEdgeDistances(False)
        if self.crashed:
            return
        # in future, do some neural network magic to decide how much to steer and how much to change speed
        # for now, get the change in speed, based on how clear the road is straight ahead
        distance_ahead = track_edge_distances[0][1] # how far is clear straight ahead
        speed_delta = 4 * (distance_ahead/CAR_VISION_DISTANCE) - 2

        if speed_delta < CAR_ACCELERATION_MIN:
            speed_delta = CAR_ACCELERATION_MIN
        
        if speed_delta > CAR_ACCELERATION_MAX:
            speed_delta = CAR_ACCELERATION_MAX

        speed_new = self.speed + speed_delta
        
        if speed_new < CAR_SPEED_MIN:
            speed_new = CAR_SPEED_MIN
        
        if speed_new > CAR_SPEED_MAX:
            speed_new = CAR_SPEED_MAX
        
        self.speed = speed_new

        steering_angle_new = 0
        if distance_ahead < CAR_VISION_DISTANCE / 1.8:        
            for ted in track_edge_distances:
                if ted[0] == 0:
                    continue
                steering_angle_new += ted[1] / ted[0]

        self.steering_radians = steering_angle_new / 20
        self.direction_radians += self.steering_radians #* self.speed # direction changes more per frame if you're goig faster

        self.position = (self.position[0] + self.speed * math.cos(self.direction_radians), self.position[1] + self.speed * math.sin(self.direction_radians))
        self.position_rounded = (round(self.position[0]),round(self.position[1]))    

        car_speed_colour = round(255 * self.speed / CAR_SPEED_MAX)
        car_colour = (255 - car_speed_colour, car_speed_colour, 0)
        self.screen.set_at(self.position_rounded, car_colour)


    def GetTrackEdgeDistances(self, draw_lines):    
        car_on_track = self.track.track_pixels[self.position_rounded]
        if not car_on_track:
            self.crashed = True
            self.DrawCrashedCar()
            return NULL

        # list of tuples: [(angle,distance)]
        track_edge_distances = []

        for vision_angle in CAR_VISION_ANGLES:
            track_edge_distance = self.GetTrackEdgeDistance(vision_angle, draw_lines)
            track_edge_distances.append((vision_angle, track_edge_distance))

        pygame.display.update()
        
        self.crashed = False
        return track_edge_distances
    
    def GetTrackEdgeDistance(self, vision_angle, draw_line):
        # from x,y follow a line at vision_angle until no longer on the track
        # or until CAR_VISION_DISTANCE has been reached
        search_angle_radians = self.direction_radians + math.radians(vision_angle)
        delta_x = math.cos(search_angle_radians)
        delta_y = math.sin(search_angle_radians)

        test_x, test_y = self.position_rounded
        edge_distance = 0

        for i in range(1, CAR_VISION_DISTANCE):
            edge_distance = i
            test_x += delta_x
            test_y += delta_y
            if self.track.track_pixels[round(test_x)][round(test_y)] == False:
                break
        
        if draw_line:
            pygame.draw.line(self.screen, RED, self.position_rounded, [round(test_x), round(test_y)])

        return edge_distance
    
    def DrawCrashedCar(self):
        pygame.draw.circle(self.screen, RED, self.position_rounded, TRACK_MAX_WIDTH, width=2)
        pygame.display.update()

class Track():
    def __init__(self, screen) -> None:
        self.screen = screen
        self.track = []
        self.scaled_track = []
        self.interpolated_scaled_track = []
        self.track_widths = []
        self.track_pixels = []
    
    def Create(self):
        self.GetNewTrack()
        self.SetScaledTrack()
        self.SetInterpolatedScaledTrack()
        self.SetTrackWidths()
        self.SetTrackPixels()
        self.DrawInterpolatedTrack()
        #self.DrawTrack()
        
    def GetNewTrack(self):
        # python version of the answer to this 
        # https://answers.unity.com/questions/394991/generate-closed-random-path-in-c.html
        
        start_row = random.randint(1, COLS-2)
        start_col = random.randint(1, ROWS-2)
        
        # create a list of the coordinates of 4 central points that make up a square
        track = [(start_row,start_col),(start_row+1,start_col),(start_row+1,start_col+1),(start_row,start_col+1)]
        
        # create 2D array of booleans for the vertices in the grid
        # Elements will be set to True to indicate the vertex is part of the track and so the track can't be expanded into it
        # Elements around the outside are also set to True, so that the track won't expand all the way to the edge
        # https://stackoverflow.com/questions/13614452/python-multidimensional-boolean-array
        grid_vertices = np.zeros((COLS+1,ROWS+1), dtype=bool)   

        # set the first and last rows
        for i in range(COLS):
            grid_vertices[i][0] = True        
            grid_vertices[i][ROWS] = True
    
        # set the first and last columns
        for i in range(1, ROWS-1):
            grid_vertices[0][i] = True        
            grid_vertices[COLS][i] = True

        # set the grid vertices for the starting square of track
        for track_vertex in track:
            grid_vertices[track_vertex] = True

        # keep expanding the track until it won't expand any more
        while True:
            # get a random track segment to expand but, if that won't expand, need to get another until all have been tested.
            # so, get a randomly sorted list of indices and work through the segments indexed by them until a segment can be expanded or none can be expanded and end the loop
            track_len = len(track)
            shuffled_indices = list(range(0,track_len))
            random.shuffle(shuffled_indices)

            # loop though the shuffled_indices until a segment can be expanded or all have been tried
            for track_segment_start_index in shuffled_indices:
                track_segment_end_index = track_segment_start_index + 1
                if track_segment_end_index > track_len-1:
                    track_segment_end_index = 0

                track_segment_start = track[track_segment_start_index]
                track_segment_end = track[track_segment_end_index]

                track_segment_start_x, track_segment_start_y = track_segment_start
                track_segment_end_x, track_segment_end_y = track_segment_end
                
                # the track started off going round clockwise and so always will
                # the track should expand outwards, which is always to the left of the current track segment (when looking from the start of the segment to the end of it)
                # coordinates start (0,0) at the top left
                # if the segment goes left to right, it will expand upwards and y will decrease by 1
                # if the segment goes up to down, it will expand to the right and x will increase by 1
                # if the segment goes right to left, it will expand downwards and y will increase by 1
                # if the segment goes down to up, it will expand to the left and x wil decrease by 1

                delta_x = track_segment_end_y - track_segment_start_y
                delta_y = track_segment_start_x - track_segment_end_x
                
                track_vertex_extra_1 = (track_segment_start_x + delta_x, track_segment_start_y + delta_y)
                # check if this is already in use
                if grid_vertices[track_vertex_extra_1]:
                    # in use, so can't expand this segment
                    continue

                track_vertex_extra_2 = (track_segment_end_x + delta_x, track_segment_end_y + delta_y)
                # check if this is already in use
                if grid_vertices[track_vertex_extra_2]:
                    # in use, so can't expand this segment
                    continue

                # neither new vertex has been used by the track, so insert the new vertices after the start one
                # this method inserts a list (the 2 new vertices) into the track before the vertex for the end of the segment
                track[track_segment_end_index:track_segment_end_index] = [track_vertex_extra_1,track_vertex_extra_2]

                # flag that the new vertices are part of the track
                grid_vertices[track_vertex_extra_1] = True
                grid_vertices[track_vertex_extra_2] = True                
                # if the track has been expanded at this segment, break from this loop
                break
            else:
                # gone through all of the track segments and the track wasn't expanded, so stop trying to expand it any more
                break
        
        self.track = track

    def SetScaledTrack(self):    
        self.scaled_track = [[t[0] * SQUARE_SIZE,t[1] * SQUARE_SIZE] for t in self.track]

    def DrawTrackStart(self):
        pygame.draw.circle(self.screen, START_COLOUR, self.scaled_track[0], TRACK_MAX_WIDTH)

    def DrawTrack(self):
        pygame.draw.lines(self.screen, BLACK, True, self.scaled_track, 1)

    def SetInterpolatedScaledTrack(self):
        # https://stackoverflow.com/questions/31464345/fitting-a-closed-curve-to-a-set-of-points
        
        # loop the track back round to the strart
        interpolated_scaled_track = self.scaled_track + [self.scaled_track[0]]

        # change the list of coordinates to a numpy array
        pts = np.array(interpolated_scaled_track)

        # magic happens
        tck, u = splprep(pts.T, u=None, s=0.0, per=1) 
        u_new = np.linspace(u.min(), u.max(), TRACK_CURVE_POINTS)
        x_new, y_new = splev(u_new, tck, der=0)

        self.interpolated_scaled_track = [list(a) for a in zip(x_new , y_new)]

    def SetTrackWidths(self):
        # track width should vary between TRACK_MIN_WIDTH to TRACK_MAX_WIDTH
        # to get the width to vary smoothly but randomly, a random walk is created and then smoothed over 20 points, normalised to the range [0,1] and scaled
        # the width starts at TRACK_MIN_WIDTH. If the end of the track is wide, it can cause problems with driving when it loops round to the narrow start.
        # The list of widths could be halved in length and mirrored, so that the end is the same width as the start, but this makes for an extra challenge.
        x = np.linspace(0, TRACK_CURVE_POINTS, TRACK_CURVE_POINTS)

        def RandomWalk(x):
            y = 0
            result = []
            for _ in x:
                result.append(y)
                y += np.random.normal(scale=1)
            return np.array(result)

        def NormalizeData(data):
            return (data - np.min(data)) / (np.max(data) - np.min(data))

        track_width = uniform_filter1d(RandomWalk(x), size=20)
        track_width = (TRACK_MAX_WIDTH - TRACK_MIN_WIDTH) * NormalizeData(track_width) + TRACK_MIN_WIDTH
        self.track_widths = track_width
    
    def SetTrackPixels(self):
        # draw the track in lots of red circles on a black background
        self.screen.fill(BLACK)
        for i in range(0, len(self.interpolated_scaled_track)):
            pygame.draw.circle(self.screen, RED, self.interpolated_scaled_track[i], self.track_widths[i])

        pygame.display.update()
        
        # get an array from the screen identifying where the track is
        tp = pygame.surfarray.array_red(self.screen)
        # reduce this down to an array of booleans where 255 becomes True
        self.track_pixels = tp.astype(dtype=bool)

    def DrawInterpolatedTrack(self):
        # now make the track look nice
        self.screen.fill(WHITE)

        self.DrawTrackStart()

        # draw lots of black circles of varying widths to create a smooth track that matches the backing array track_pixels
        for i in range(0, len(self.interpolated_scaled_track)):
            pygame.draw.circle(self.screen, BLACK, self.interpolated_scaled_track[i], self.track_widths[i])
            
        # draw track centre line
        for t in self.scaled_track:
            self.screen.set_at((round(t[0]),round(t[1])), TRACK_MIDLINE_COLOUR)

        pygame.display.update()

    def GetInitialDirectionRadians(self):
        initial_angle = math.atan2(self.track[1][1]-self.track[0][1], self.track[1][0]-self.track[0][0])
        return initial_angle

# define a main function
def main():     
    # initialize the pygame module
    pygame.init()
    # load and set the logo
    logo = pygame.image.load("logo32x32.png")
    pygame.display.set_icon(logo)
    pygame.display.set_caption("AI car")
     
    # create a surface on screen that has the size defined globally
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    # define a variable to control the main loop
    running = True
    newTrackAndCarNeeded = True

    # main loop
    while running:
        if newTrackAndCarNeeded:
            track = Track(screen)
            track.Create()

            car = Car(screen, track)
            newTrackAndCarNeeded = False

        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False
                pygame.quit
                sys.exit()
                break
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # get the mouse position
                mouse_pos = pygame.mouse.get_pos()
                car.position = mouse_pos
                car.GetTrackEdgeDistances(True)
                continue

            if event.type == pygame.TEXTINPUT:
                if event.text == 'n':
                    newTrackAndCarNeeded = True
                    continue
        
        if not car.crashed:
            car.Drive()

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__=="__main__":
    # call the main function
    main()