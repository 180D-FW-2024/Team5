maze.py is the program that runs on the Player's laptop.

The program does the following:
- Sets up TCP connection with the Maze Navigator and Controller.
- Creates the GUI, generates the maze walls, and handles all the game rules.
- Listens for controller commands, when a command is received:
    - Sends command to Maze Navigator if move is valid.
- The GUI has the following buttons:
    - Start: Generates initial maze.
    - Restart Current Maze: Restart game with current maze layout.
    - New Maze: Restart game with new maze layout.
    - Enable/Disable Voice Commands: Toggles voice control functionality.
    - Arrows: Allows the player to control Maze Navigator using GUI.

No known bugs.

For future improvements, we would want to add a reset position button. This would automatically move the Maze Navigator back to starting square and would eliminate the need to manually put it back.
