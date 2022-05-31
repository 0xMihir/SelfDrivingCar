# Training Data

This folder contains the code required to acquire and train models for the car.

## Raspberry Pi Setup

1. Install Bluetooth development modules `sudo apt install libbluetooth-dev`
2. Install DepthAI dependencies `sudo curl -fL https://docs.luxonis.com/install_dependencies.sh | bash`
3. Install python dependencies `pip install -r requirements_pi.txt`
4. Make the Pi's bluetooth discoverable `sudo hciconfig hci0 piscan`
    * To make this work on startup add the following to `/etc/rc.local` before `exit 0`:
    ```bash
    sleep 1
    /usr/bin/bluetoothctl <<EOF
    power on
    discoverable on
    pairable on
    EOF
    ```
5. Pair an Android phone with the Pi
6. Run the server using `sudo -E training_server.py`

## Android Setup

1. Open the [RCControllerApp](RCControllerApp) folder in Android Studio
2. Change the name of the device to your Pi's hostname
3. Build and install the app on an Android phone
4. Pair the Pi with the phone
5. Run the app and the car

## Training Setup

Use Python 3.8 for the training part

1. Install python dependencies using `pip install -r requirements.txt`
2. Upgrade tensorflow to the latest version using `pip install --upgrade tensorflow`. Ignore the incompatiblilty warnings about numpy and tensorflow.
3. Run all cells in the [notebook](train_model.ipynb)
4. Model and MyriadX blob should be in the models folder
