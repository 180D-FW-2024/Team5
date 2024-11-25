import socket
from pynput import keyboard

# Setup
HOST = '131.179.11.38'  # RPi's IP address
PORT = 8080  # Port number, needs to match the server

# Initialize the socket connection
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Function to send commands to the server
def send_command(command):
    client.sendall(command.encode())
    print(f"Sent command: {command}")

# Function to handle key press events
def on_press(key):
    try:
        if key.char == 'w':  # Forward
            send_command("forward")
        elif key.char == 's':  # Reverse
            send_command("reverse")
        elif key.char == 'a':  # Left
            send_command("left")
        elif key.char == 'd':  # Right
            send_command("right")
        elif key.char == 'q':  # Quit
            send_command("stop")
            return False  # Stop the listener
    except AttributeError:
        # Handle special keys
        pass

# Stop moving car on release of key
def on_release(key):
    try:
        if key.char != null: # Send command that you want the car to stop doing its action
            send_command("stop moving")
    except AttributeError:
        pass


# Start listening for keyboard inputs
try:
    print("Press W/A/S/D for movement, Q to quit.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
finally:
    client.close()
    print("Connection closed.")