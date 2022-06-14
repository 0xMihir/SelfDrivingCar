import depthai as dai
import os, sys
from time import time
import cv2 
sys.path.insert(1, os.path.join(sys.path[0], ".."))
# import common.driving as driving

pipeline = dai.Pipeline()
camera = pipeline.create(dai.node.ColorCamera)
nn = pipeline.create(dai.node.NeuralNetwork)
nnOut = pipeline.create(dai.node.XLinkOut)
previewOut = pipeline.create(dai.node.XLinkOut)

camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camera.setPreviewSize(480, 135)
camera.setInterleaved(False)

camera.preview.link(nn.input)
camera.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
nn.setBlobPath("./steeringmodel.blob")
nn.out.link(nnOut.input)
camera.preview.link(previewOut.input)
nnOut.setStreamName("nn")
previewOut.setStreamName("preview")


with dai.Device(pipeline) as device:
    print('USB speed:', device.getUsbSpeed())

    nnQueue = device.getOutputQueue("nn")
    previewQueue = device.getOutputQueue("preview", maxSize=4, blocking=False)

    while True:
        data = nnQueue.get()
        fp16data = data.getFirstLayerFp16()
        # for i in range(0, len(fp16data)):
        #     print(format(fp16data[i], ".6f"), end=" ")
        # print("",end="\r")
        # get max index
        max_index = fp16data.index(max(fp16data))
        # print(["center", "left", "right"][max_index],"             ", end="\r")
        previewFrame = previewQueue.get().getCvFrame()
        cv2.putText(previewFrame, ["center", "left", "right"][max_index], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Neural Network Image", previewFrame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

