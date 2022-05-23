import asyncio
import bluetooth
import pigpio
import depthai as dai
import ffmpeg
import os
from time import time

# GPIO Pins for motor controller
drivePower = 4
steerPower = 17
driveBack = 27
driveFwd = 22
steerLeft = 23
steerRight = 24

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

# GPIO
pi = pigpio.pi()
pi.set_PWM_frequency(drivePower, 8000)
pi.write(steerPower, 1)

# DepthAI

pipeline = dai.Pipeline()
rgb = pipeline.create(dai.node.ColorCamera)
enc = pipeline.create(dai.node.VideoEncoder)
vidOut = pipeline.create(dai.node.XLinkOut)

vidOut.setStreamName("video")

rgb.setFps(60)
rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
rgb.video.link(enc.input)
enc.bitstream.link(vidOut.input)
rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
enc.setDefaultProfilePreset(
    rgb.getFps(), dai.VideoEncoderProperties.Profile.H265_MAIN)


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

print("Waiting for connection on RFCOMM channel", port)


async def write_frame(queue, videoFile, commandFile, command):
    videoData = queue.tryGet()
    if videoData is not None:
        videoData.getData
        commandFile.write(command)

async def process_video(start_time):
    stream = (ffmpeg
              .input(f"raw/{start_time}.h265")
              .output("raw/temp_{start_time}/%05d.jpg", "copy"))
    stream.run()

    with open(f"raw/commands_{start_time}", "r") as commandFile:
        lines = commandFile.readlines()
        for i in range(len(lines)):
            line = lines[i]
            if line == "stop":
                continue
            os.rename(f"raw/temp_{start_time}/{i:05}.jpg",
                      f"data/{line}/{int(time()*1000)}.jpg")

with dai.Device(pipeline) as device:
    videoQueue = device.getOutputQueue("video", maxSize=1, blocking=False)

    try:
        while True:
            # Keep connecting to Bluetooth clients
            client_sock, client_info = server_sock.accept()
            print("Connected to", client_info)
            currentCommand = "stop"
            start_time = int(time()*1000)
            with open(f"raw/out_{start_time}.h265", "wb") as videoOut, \
                    open(f"raw/commands_{start_time}.txt", "w") as commandOut:
                try:
                    while True:
                        data = client_sock.recv(1024)
                        if not data:
                            break
                        print(data)
                        if data[0] == steer:
                            direction = "center"
                            if data[1] == 0:
                                pi.clear_bank_1(
                                    1 << steerLeft | 1 << steerRight)
                            elif data[1] == 2:
                                direction = "right"
                                pi.write(steerLeft, 0)
                                pi.write(steerRight, 1)
                            else:
                                direction = "left"
                                pi.write(steerLeft, 1)
                                pi.write(steerRight, 0)
                            currentCommand = direction

                        elif data[0] == throttle:
                            throttleVal = int.from_bytes(
                                data[1:2], "little", signed=True)
                            pi.set_PWM_dutycycle(drivePower,
                                                 abs(throttleVal) + 128)
                            if throttleVal == 0:
                                pi.clear_bank_1(1 << driveBack | 1 << driveFwd)
                                pi.set_PWM_dutycycle(drivePower, 0)
                                print("stop")
                                currentCommand = "stop"
                            elif throttleVal >= 0:
                                pi.write(driveFwd, 1)
                                pi.write(driveBack, 0)
                                print("forward", abs(throttleVal)+128)
                            else:
                                pi.write(driveFwd, 0)
                                pi.write(driveBack, 1)
                                print("back", abs(throttleVal)+128)
                        asyncio.run(write_frame(
                            videoQueue, videoOut, commandOut, currentCommand))
                    asyncio.run(process_video(start_time))
                except OSError as err:
                    print("Error:", err)
                finally:
                    print("Disconnected")
                    client_sock.close()
    except KeyboardInterrupt:
        server_sock.close()
