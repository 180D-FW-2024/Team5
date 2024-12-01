import socket
import RPi.GPIO as gpio # type: ignore
import time

# GPIO Setup
def init():
    gpio.setmode(gpio.BCM)
    gpio.setup(17, gpio.OUT)
    gpio.setup(22, gpio.OUT)
    gpio.setup(23, gpio.OUT)
    gpio.setup(24, gpio.OUT)

def forward():
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, True)
    gpio.output(24, False)

def backward():
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, True)

def left_turn():
    gpio.output(17, True)
    gpio.output(22, False)
    gpio.output(23, True)
    gpio.output(24, False)

def right_turn():
    gpio.output(17, False)
    gpio.output(22, True)
    gpio.output(23, False)
    gpio.output(24, True)

def stop():
    gpio.output(17, False)
    gpio.output(22, False)
    gpio.output(23, False)
    gpio.output(24, False)

# Server Setup
HOST = ''  # Listen on all available interfaces
PORT = 8080  # Port number, ensure it matches the laptop script

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

try:
    init()
    print("Waiting for connection...")
    conn, addr = sock.accept()
    print(f"Connected by {addr}")
    
    while True:
        data = conn.recv(1024).decode().strip()
        if not data:
            break

        print(f"Received command: {data}")
        if data == 'up':
            forward()
            time.sleep(1)
            stop()
        elif data == 'down':
            backward()
            time.sleep(1)
            stop()
        elif data == 'left':
            left_turn()
            time.sleep(1)
            stop()
        elif data == 'right':
            right_turn()
            time.sleep(1)
            stop()
        elif data == 'stop':
            stop()
        else:
            print(f"Unknown command: {data}")

finally:
    stop()
    gpio.cleanup()
    sock.close()