# Team5
# For detailed download and program instructions, refer to the user manual found [here](https://github.com/180D-FW-2024/Team5/blob/main/ECE_180_User_Manual.pdf).


## Download Maze Game
### Mac/Linux (M1/ARM):
[Download the latest release](https://github.com/180D-FW-2024/Team5/releases/download/v1.0.0-beta/maze)

After downloading, navigate to folder containing downloaded file 'maze' and run: chmod +x ./maze && ./maze

### Windows (x86):

### Mac (Intel):


## Program Info
Main program is contained in maze-program. Needs to run on the user's laptop.

Maze Navigator code runs on the RC car that goes through the maze.

Controller runs on the Raspberry Pi 4 with the 3 directional buttons.

Both controller.py and maze-navigator.py need to be running before maze.py is started. (The Maze Navigator and Controller are setup to run their scripts on startup using systemd. No changes are required by the user).
