# import the pygame module, so you can use it
import pygame
import numpy as np
import random

BLACK = (0, 0, 0)
WHITE = (200, 200, 200)
SQUARE_SIZE = 80
ROWS = 8
COLS = 10
TRACK_WIDTH = 10
TRACK_DRAWING_DELAY = 100

WINDOW_WIDTH = COLS * SQUARE_SIZE
WINDOW_HEIGHT = ROWS * SQUARE_SIZE

def create_grid(screen):
    # python version of the answer to this 
    # https://answers.unity.com/questions/394991/generate-closed-random-path-in-c.html
    
    start_row = random.randint(1, COLS-2)
    start_col = random.randint(1, ROWS-2)
    
    # create a list of the coordinates of 4 central points that make up a square
    track = [[start_row,start_col],[start_row+1,start_col],[start_row+1,start_col+1],[start_row,start_col+1]]
    
    # create 2D arrays to indicate if the vertex is the start or end of a track segment
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

    for track_vertex in track:
        grid_vertices[track_vertex[0],track_vertex[1]] = True
        #grid_segment_end[track_vertex[0],track_vertex[1]] = True

    # keep expanding the track until it won't expand any more
    expand_track = True
    while expand_track:
        # get a random track segment to expand but, if that won't expand, need to get another until all have been tested.
        # so, get a randomly sorted list of indices and work through the segments indexed by them until a segment can be expanded or none can be expanded and end the loop
        track_len = len(track)
        shuffled_indices = list(range(0,track_len))
        random.shuffle(shuffled_indices)

        # loop though the shuffled_indices until a segment can be expanded or all have been tried
        track_expanded = False
        
        draw_track(screen, track)
        pygame.time.delay(TRACK_DRAWING_DELAY)

        for track_segment_start_index in shuffled_indices:
            track_segment_end_index = track_segment_start_index + 1
            if track_segment_end_index > track_len-1:
                track_segment_end_index = 0

            track_segment_start = track[track_segment_start_index]
            track_segment_end = track[track_segment_end_index]

            track_segment_start_x = track_segment_start[0]
            track_segment_start_y = track_segment_start[1]
            track_segment_end_x = track_segment_end[0]
            track_segment_end_y = track_segment_end[1]

            # the track started off going round clockwise and so always will
            # the track should expand outwards, which is always to the left of the current track segment (when looking from the start of the segment to the end of it)
            # coordinates start (0,0) at the top left
            # if the segment goes left to right, it will expand upwards and y will decrease by 1
            # if the segment goes up to down, it will expand to the right and x will increase by 1
            # if the segment goes right to left, it will expand downwards and y will increase by 1
            # if the segment goes down to up, it will expand to the left and x wil decrease by 1

            delta_x = track_segment_end_y - track_segment_start_y
            delta_y = track_segment_start_x - track_segment_end_x
            
            track_vertex_extra_1 = [track_segment_start_x + delta_x, track_segment_start_y + delta_y]
            # check if this is already in use
            if grid_vertices[track_vertex_extra_1[0],track_vertex_extra_1[1]]:
                # in use, so can't expand this segment
                continue

            track_vertex_extra_2 = [track_segment_end_x + delta_x, track_segment_end_y + delta_y]
            # check if this is already in use
            if grid_vertices[track_vertex_extra_2[0],track_vertex_extra_2[1]]:
                # in use, so can't expand this segment
                continue

            # neither new vertex has been used by the track, so insert the new vertices after the start one
            # this method inserts a list (the 2 new vertices) into the track before the vertex for the end of the segment
            track[track_segment_end_index:track_segment_end_index] = [track_vertex_extra_1,track_vertex_extra_2]

            # flag that the new vertices are part of the track
            grid_vertices[track_vertex_extra_1[0],track_vertex_extra_1[1]] = True
            grid_vertices[track_vertex_extra_2[0],track_vertex_extra_2[1]] = True

            track_expanded = True
            
            # if the track has been expanded at this segment, break from this loop
            if track_expanded:
                break

        # if the track wasn't expanded for any segment then stop trying to expand it any more
        if not track_expanded:
            expand_track = False
    
    draw_track(screen, track)

def draw_track(screen, track):
    screen.fill(BLACK)
    scaled_track = [[t[0] * SQUARE_SIZE,t[1] * SQUARE_SIZE] for t in track]
    pygame.draw.lines(screen, WHITE, True, scaled_track, TRACK_WIDTH)
    pygame.display.update()

def draw(screen):
    screen.fill(BLACK)
    create_grid(screen)
    pygame.display.update()

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
    
    draw(screen)

    # main loop
    while running:
        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False
                break

            if event.type == pygame.TEXTINPUT:
                if event.text == 'n':
                    draw(screen)    

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__=="__main__":
    # call the main function
    main()