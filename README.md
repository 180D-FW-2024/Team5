# Team5
# For detailed download and program instructions, refer to the user manual found [here](https://github.com/180D-FW-2024/Team5/blob/main/ECE_180_User_Manual.pdf).
Note: you must download the PDF to click on any of the links such as for the Tailscale invites.


## Download Maze Game
### MacOS (M1/ARM):
[Download the latest release](https://github.com/180D-FW-2024/Team5/releases/download/v1.0.0/maze)

After downloading, navigate to folder containing downloaded file 'maze' and run: chmod +x ./maze && ./maze

## Program Info
Main program is maze.py contained in maze-program. Needs to run on the user's laptop.

Maze Navigator program is maze-navigator.py contained in maze-navigator.

Controller program is controller.py contained in controller.

Both controller.py and maze-navigator.py need to be running before maze.py is started. (The Maze Navigator and Controller are setup to run their scripts on startup using systemd. No changes are required by the user).
