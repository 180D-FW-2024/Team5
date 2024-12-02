import socket
import RPi.GPIO as gpio # type: ignore
import time
import threading
import IMU

# motor 1 pins
# ena = 12
# in1 = 17
# in2 = 22

# motor 2 pins
# enb = 13
# in3 = 23
# in4 = 24

# GPIO Setup
def init_gpio():
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
PORT = 8080  # Port number, ensure it matches the maze software port

running = True

def imu_data_sender(conn):
    """Send IMU data continuously to the client."""
    global running
    while running:
        imu_data = process_imu_data()
        imu_message = f"imu_data|acc:{imu_data['acc']}|gyro:{imu_data['gyro']}|mag:{imu_data['mag']}"
        try:
            conn.sendall(imu_message.encode())
        except Exception as e:
            print(f"Error sending IMU data: {e}")
            break
        time.sleep(0.1)  # Send data every 100ms

try:
    # GPIO Initialization
    init_gpio()

    # IMU Initialization
    print("Detecting IMU...")
    IMU.detectIMU()  # Detect BerryIMU version
    IMU.initIMU()    # Initialize IMU sensors
    print("IMU Initialized.")

    print("Waiting for connection...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(1)
    conn, addr = sock.accept()
    print(f"Connected by {addr}")

    # Start a thread for sending IMU data
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
    running = False  # Stop the IMU thread
    if imu_thread.is_alive():
        imu_thread.join()  # Ensure the thread is closed
    stop()
    gpio.cleanup()
    sock.close()
    print("Server closed.")