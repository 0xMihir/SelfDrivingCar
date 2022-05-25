import pigpio

# GPIO Pins for motor controller
drivePower = 4
steerPower = 17
driveBack = 27
driveFwd = 22
steerLeft = 23
steerRight = 24


# GPIO
pi = pigpio.pi()
pi.set_PWM_frequency(drivePower, 8000)
pi.write(steerPower, 1)

# Throttle

def stop():
    pi.clear_bank_1(1 << driveBack | 1 << driveFwd)
    pi.set_PWM_dutycycle(drivePower, 0)

def setThrottle(throttleVal):
    if throttleVal == 0:
            stop()
    else:
        pi.set_PWM_dutycycle(drivePower, abs(throttleVal) + 128)
        if throttleVal >= 0:
            pi.write(driveFwd, 1)
            pi.write(driveBack, 0)
        else:
            pi.write(driveFwd, 0)
            pi.write(driveBack, 1)



# Steering
def left():
    pi.write(steerLeft, 1)
    pi.write(steerRight, 0)

def center():
    pi.clear_bank_1(1 << steerLeft | 1 << steerRight)

def right():
    pi.write(steerLeft, 0)
    pi.write(steerRight, 1)