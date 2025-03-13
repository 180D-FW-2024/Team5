maze-navigator.py is the program that runs on the Maze Navigator.

The program does the following:
- Sets up TCP connection with the main program that runs on the player's laptop: maze.py.
- Controls the motors using the GPIO on the Raspberry Pi 4.
- When a command is recieved from the main program:
    - Forward: The car will move forward until the black tape of the next square is detected at the correct position in the camera.
    - Left/Right: The car will rotate left or right until the angle of the IMU reaches 90 degrees from the starting angle.
 
We ended up isolating the IMU and camera vision functions and computation to the Maze Navigator after running into issues transmitting the data to the Maze Program. Transmitting the data added too much delay to use for accurately controlling movement. It also massively slowed down our program and caused it to freeze.

For future improvements, we would want to have better control over the motors. This would allow for better adjustments of the Maze Navigator. It would also allow us to correct any movement error that accumulates over time. Currently, we could implement functionality to track positioning error but we are can't correct it because we don't have fine enough control over our motors.
