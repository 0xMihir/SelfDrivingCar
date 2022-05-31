import threading
import bluetooth
import depthai as dai
import os, sys
from time import time
sys.path.insert(1, os.path.join(sys.path[0], ".."))
import common.driving as driving

# Codes
steer = 0
throttle = 1
left = 1
center = 0
right = 2

# Directories
directories = ["data/left", "data/center", "data/right", "raw"]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

# DepthAI

pipeline = dai.Pipeline()
camRgb = pipeline.create(dai.node.ColorCamera)
videoEnc = pipeline.create(dai.node.VideoEncoder)
xout = pipeline.create(dai.node.XLinkOut)

xout.setStreamName("video")

camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
videoEnc.setDefaultProfilePreset(60, dai.VideoEncoderProperties.Profile.H265_MAIN)
camRgb.video.link(videoEnc.input)
videoEnc.bitstream.link(xout.input)

# Bluetooth
server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "534cb228-39b8-4009-9327-27dca1e528cf"

bluetooth.advertise_service(server_sock, "RCCarServer", service_id=uuid,
                            service_classes=[
                                uuid, bluetooth.SERIAL_PORT_CLASS],
                            profiles=[bluetooth.SERIAL_PORT_PROFILE])


command = "stop"
def write_frame(queue, videoFile, commandFile):
    global command
    while True:
        videoData = queue.get()
        if command == "kill":
            break
        videoData.getData().tofile(videoFile)
        commandFile.write(command+"\n")


driving.stop()
with dai.Device(pipeline) as device:
    videoQueue = device.getOutputQueue("video", maxSize=30, blocking=False)
    try:
        while True:
            # Keep connecting to Bluetooth clients
            print("Waiting for connection on RFCOMM channel", port)
            client_sock, client_info = server_sock.accept()
            print("Connected to", client_info)
            start_time = int(time()*1000)
            with open(f"raw/out_{start_time}.h265", "wb") as videoOut, \
                    open(f"raw/commands_{start_time}.txt", "w") as commandOut:
                thread = threading.Thread(target=write_frame,args=(videoQueue, videoOut, commandOut))
                try:
                    thread.start()
                    while True:
                        data = client_sock.recv(1024)
                        if not data:
                            break
                        if data[0] == steer:
                            command = "center"
                            if data[1] == 0:
                                driving.center()
                            elif data[1] == 2:
                                command = "right"
                                driving.right()
                            else:
                                command = "left"
                                driving.left()

                        elif data[0] == throttle:
                            throttleVal = int.from_bytes(
                                data[1:2], "little", signed=True)
                            driving.setThrottle(throttleVal)
                            if throttleVal == 0:
                                command = "stop"
                        
                except OSError as err:
                    print("Error:", err)
                finally:
                    print("Disconnected")
                    command = "kill"
                    thread.join()
                    client_sock.close()
                    driving.stop()
                    
    except KeyboardInterrupt:
        server_sock.close()
        for file in os.scandir("raw"):
            if file.is_file():
                os.chmod(file.path,os.stat.S)
        driving.stop()