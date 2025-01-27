import RPi.GPIO as GPIO
import socket
import time

# Button GPIO pins
BUTTONS = {
    27: 'w',  # Forward
    22: 'a',  # Left
    17: 'd',  # Right
}

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in BUTTONS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull-up resistor

# Server connection details
SERVER_IP = '100.107.224.80'  # Maze Program Tailscale IP
SERVER_PORT = 9090

try:
    # Create and maintain a persistent connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        print("Listening for button presses...")
        while True:
            for pin, command in BUTTONS.items():
                if GPIO.input(pin) == GPIO.LOW:  # Button pressed
                    print(f"Button {pin} pressed, sending '{command}'")
                    client.sendall(command.encode())  # Send command
                    time.sleep(0.3)  # Debounce delay
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()