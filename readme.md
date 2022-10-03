# Not-AI-Car
## Instructions
- Run the Python script not_ai_car.py
- Controls:
  - Esc to quit
  - N to generate a new track
  - Spacebar to pause
  - Left and right arrow keys to decrease and increase car speed


## Background
Looking for a project to learn python with, I found various examples of cars using "AI" to learn to navigate around a track, so I thought I would do something similar.

The main concern that YouTube commentators had of such cars was, after learning to drive around a track, would they be able to drive around another track? So, the first thing I coded was a randomly generated track, which was made to be curvy and of varying width.

Then, I added a "car" to the track, which could measure the distances to the edge of the track at various angles. As a test, I thought I'd see if I could get the car to drive around the track using some simple instructions and it did really well:

https://user-images.githubusercontent.com/13784388/193688536-a75e50a6-79e6-40f0-85d1-5d719833e330.mp4

## Notes
If you run the code, you'll see that the car goes off the track a bit. This is because the calculations for where the car should go and whether has crashed are based on it being just one pixel in size. An exercise for the reader would be to implement the code to make the car crash if any part of it goes off the track and to improve the driving, so that the car shouldn't crash. The simplest solution might be for the car to drive around a virtual track that it narrower than the visible track so, if the car is on the virtual track, you know it is still on the visible track.

As the simple driving instructions were so successful, I decided to save AI for a trickier challenge.
