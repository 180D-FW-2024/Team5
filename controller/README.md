controller.py is the program that runs on the controller.

The program does the following:
- Sets up TCP connection with the main program that runs on the player's laptop: maze.py.
- The controller sends a command to the main program whenever the player presses one of the three buttons.

We decided on this implementation after trying to emulate a bluetooth keyboard for the controller's connection to the Maze Program. That implementation ended up being outdated. Emulating a bluetooth keyboard on Linux is quite complex and most of the information We could find was it was at least 10 years old. Using a server TCP connection similar to the Maze Navigator ended up working great with no known bugs or issues.

To enable/disable Systemd config that runs program on boot:

Reload Systemd
```
sudo systemctl daemon-reload
```
Enable autostart service (replace enable with disable to turn off autostart)
```
sudo systemctl enable controller.service
```
Start immediately
```
sudo systemctl start controller.service
```
Check service status
```
sudo systemctl status controller.service
```
