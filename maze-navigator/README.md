maze-navigator.py is the program that runs on the Maze Navigator.

The program does the following:
- Sets up TCP connection with the main program that runs on the player's laptop: maze.py.
- Controls the motors using the GPIO on the Raspberry Pi 4.
- When a command is recieved from the main program:
    - Forward: The car will move forward until the black tape of the next square is detected at the correct position in the camera.
    - Left/Right: The car will rotate left or right until the angle of the IMU reaches 90 degrees from the starting angle.
