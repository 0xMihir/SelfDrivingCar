import ffmpeg 
import shutil
from time import time_ns
import sys, os

def process_video(start_time):
    if not os.path.exists(f"raw/temp_{start_time}"):
        os.makedirs(f"raw/temp_{start_time}")
    print(f"raw/out_{start_time}.h265")
    stream = (ffmpeg
              .input(f"raw/out_{start_time}.h265")
              .output(f"raw/temp_{start_time}/%05d.jpg"))
    stream.run()

    with open(f"raw/commands_{start_time}.txt", "r") as commandFile:
        lines = commandFile.readlines()
        for i in range(len(lines)):
            line = lines[i]
            line = line[0:-1]
            if line in ["stop", "", "kill"]:
                continue
            shutil.copyfile(f"raw/temp_{start_time}/{i:05}.jpg",
                      f"data/{line}/{int(time_ns())}.jpg")

if __name__ == "__main__":
    process_video(sys.argv[1])