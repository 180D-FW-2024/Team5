import socket
import RPi.GPIO as gpio
import time
import threading
import IMU
import cv2
#import struct
#import pickle
#from picamera2 import Picamera2

# Motor pins
in1 = 17
in2 = 22
in3 = 23
in4 = 24

# GPIO Setup
def init_gpio():
    gpio.setmode(gpio.BCM)
    gpio.setup(in1, gpio.OUT)
    gpio.setup(in2, gpio.OUT)
    gpio.setup(in3, gpio.OUT)
    gpio.setup(in4, gpio.OUT)

def forward():
    gpio.output(in1, False)
    gpio.output(in2, True)
    gpio.output(in3, True)
    gpio.output(in4, False)

def backward():
    gpio.output(in1, True)
    gpio.output(in2, False)
    gpio.output(in3, False)
    gpio.output(in4, True)

def left_turn():
    gpio.output(in1, True)
    gpio.output(in2, False)
    gpio.output(in3, True)
    gpio.output(in4, False)

def right_turn():
    gpio.output(in1, False)
    gpio.output(in2, True)
    gpio.output(in3, False)
    gpio.output(in4, True)

def stop():
    gpio.output(in1, False)
    gpio.output(in2, False)
    gpio.output(in3, False)
    gpio.output(in4, False)

def process_imu_data():
    acc_x = IMU.readACCx()
    acc_y = IMU.readACCy()
    acc_z = IMU.readACCz()
    gyr_x = IMU.readGYRx()
    gyr_y = IMU.readGYRy()
    gyr_z = IMU.readGYRz()
    mag_x = IMU.readMAGx()
    mag_y = IMU.readMAGy()
    mag_z = IMU.readMAGz()

    imu_data = {
        "acc": {"x": acc_x, "y": acc_y, "z": acc_z},
        "gyro": {"x": gyr_x, "y": gyr_y, "z": acc_z},
        "mag": {"x": mag_x, "y": mag_y, "z": mag_z}
    }
    return imu_data

# Server Setup
HOST = ''  # Listen on all available interfaces
PORT = 8080  # Port for command/IMU data
# CAMERA_PORT = 8081  # Port for camera stream

running = True

def imu_data_sender(conn):
    """Send IMU data continuously to the client."""
    global running
    while running:
        imu_data = process_imu_data()
        imu_message = f"imu_data|acc:{imu_data['acc']}|gyro:{imu_data['gyro']}|mag:{imu_data['mag']}\n"
        try:
            conn.sendall(imu_message.encode())
        except Exception as e:
            print(f"Error sending IMU data: {e}")
            break
        time.sleep(0.1)  # Send data every 100ms

# def start_camera_stream():
#    """Stream camera frames to the client."""
#    global running
#    picam2 = Picamera2()
#    picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
#    picam2.start()

#    camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    camera_socket.bind((HOST, CAMERA_PORT))
#    camera_socket.listen(1)
#    print("Waiting for camera connection...")
#    conn, addr = camera_socket.accept()
#    print(f"Camera connected by {addr}")

#    try:
#        while running:
#            frame = picam2.capture_array()
#            # Convert frame to RGB
#            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Serialize and send the frame
#           data = pickle.dumps(frame)
#            conn.sendall(struct.pack("L", len(data)) + data)
#    except Exception as e:
#        print(f"Camera stream error: {e}")
#    finally:
#        picam2.stop()
#        conn.close()
#        camera_socket.close()

try:
    # GPIO Initialization
    init_gpio()

    # IMU Initialization
    print("Detecting IMU...")
    IMU.detectIMU()  # Detect BerryIMU version
    IMU.initIMU()    # Initialize IMU sensors
    print("IMU Initialized.")

    # Start camera stream thread
    # camera_thread = threading.Thread(target=start_camera_stream, daemon=True)
    # camera_thread.start()

    # Command server setup
    print("Waiting for connection...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    conn, addr = sock.accept()
    print(f"Connected by {addr}")

    # Start IMU data thread
    imu_thread = threading.Thread(target=imu_data_sender, args=(conn,), daemon=True)
    imu_thread.start()

    # Command handling loop
    while True:
        data = conn.recv(1024).decode().strip()
        if not data:
            break

        print(f"Received command: {data}")

        if data == 'forward':
            forward()
            time.sleep(0.55)
            stop()
        elif data == 'left':
            left_turn()
            time.sleep(0.34)
            stop()
        elif data == 'right':
            right_turn()
            time.sleep(0.34)
            stop()
        elif data == 'stop':
            stop()
        else:
            print(f"Unknown command: {data}")

finally:
    running = False  # Stop the IMU thread
    if imu_thread.is_alive():
        imu_thread.join()
#     if camera_thread.is_alive():
#        camera_thread.join()
    stop()
    gpio.cleanup()
    sock.close()
    print("Server closed.")