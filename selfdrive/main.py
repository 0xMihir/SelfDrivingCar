import depthai as dai
import os, sys
from time import time
import cv2 
sys.path.insert(1, os.path.join(sys.path[0], ".."))
import common.driving as driving

pipeline = dai.Pipeline()
camera = pipeline.create(dai.node.ColorCamera)
nn = pipeline.create(dai.node.NeuralNetwork)
nnOut = pipeline.create(dai.node.XLinkOut)
cameraOut = pipeline.create(dai.node.XLinkOut)

camera.setBoardSocket(dai.CameraBoardSocket.RGB)
camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camera.setPreviewSize(480, 135)
camera.setInterleaved(False)
camera.preview.link(nn.input)
camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
nn.setBlobPath("./steeringmodel.blob")
nnOut.setStreamName("nn")
cameraOut.setStreamName("camera")
nn.out.link(nnOut.input)

with dai.Device(pipeline) as device:
    queue = device.getOutputQueue("nn")
    driving.driveFwd()
    driving.drivePower(50)
    while True:
        data = queue.get()
        fp16data = data.getFirstLayerFp16()
        # get max index
        max_index = fp16data.index(max(fp16data))
        if max_index == 0:
            driving.center()
        elif max_index == 1:
            driving.left()
        elif max_index == 2:
            driving.right()     
        

