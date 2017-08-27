#region config
vex.pragma(config, I2C_Usage, I2C1, i2cSensors)
vex.pragma(config, Sensor, in1, leftLight, sensorLineFollower)
vex.pragma(config, Sensor, in2, middleLight, sensorLineFollower)
vex.pragma(config, Sensor, in3, rightLight, sensorLineFollower)
vex.pragma(config, Sensor, in4, wristPot, sensorPotentiometer)
vex.pragma(config, Sensor, in5, gyro, sensorGyro)
vex.pragma(config, Sensor, dgtl1, rightEncoder, sensorQuadEncoder)
vex.pragma(config, Sensor, dgtl3, leftEncoder, sensorQuadEncoder)
vex.pragma(config, Sensor, dgtl5, extensionEncoder, sensorQuadEncoder)
vex.pragma(config, Sensor, dgtl7, touchSensor, sensorTouch)
vex.pragma(config, Sensor, dgtl8, sonarSensor, sensorSONAR_cm)
vex.pragma(config, Sensor, dgtl11, armEncoder, sensorQuadEncoder)
vex.pragma(config, Sensor, I2C_1, _,sensorQuadEncoderOnI2CPort, _, AutoAssign)
vex.pragma(config, Sensor, I2C_2, _,sensorQuadEncoderOnI2CPort, _, AutoAssign)
vex.pragma(config, Sensor, I2C_3, _,sensorQuadEncoderOnI2CPort, _, AutoAssign)
vex.pragma(config, Sensor, I2C_4, _,sensorQuadEncoderOnI2CPort, _, AutoAssign)
vex.pragma(config, Sensor, I2C_5, _,sensorQuadEncoderOnI2CPort, _, AutoAssign)
vex.pragma(config, Motor, port1, frontRightMotor, tmotorVex393_HBridge, openLoop, reversed)
vex.pragma(config, Motor, port2, rearRightMotor, tmotorVex393_MC29, openLoop, reversed, encoderPort, I2C_1)
vex.pragma(config, Motor, port3, frontLeftMotor, tmotorVex393_MC29, openLoop)
vex.pragma(config, Motor, port4, rearLeftMotor, tmotorVex393_MC29, openLoop, encoderPort, I2C_2)
vex.pragma(config, Motor, port6, clawMotor,     tmotorVex393_MC29, openLoop)
vex.pragma(config, Motor, port7, armMotor,      tmotorVex393_MC29, openLoop, encoderPort, I2C_3)
vex.pragma(config, Motor, port8, leftExtendMotor, tmotorVex393_MC29, openLoop, encoderPort, I2C_4)
vex.pragma(config, Motor, port9, rightExtendMotor, tmotorVex393_MC29, openLoop)
vex.pragma(config, Motor, port10, wristMotor,    tmotorVex393_HBridge, openLoop, encoderPort, I2C_5)
#endregion config


import JoystickDriver.c
import autonRecorder.c


def threshold(number:int,minNumber:int=20) -> int:
  """Threshold a value to a minimum int"""
  return number if abs(number) >= minNumber else 0

def main() -> task:
  """This is the main task."""
  threshold:int = 10
  while (True):
    getJoystickSettings(joystick) # Update joystick in a loop
    motor[frontRightMotor] = motor[rearRightMotor] = threshold(joystick.joy1_y2)
    motor[frontLeftMotor] = motor[rearLeftMotor] = threshold(joystick.joy1_y1)

    if joy1Btn(6):
      motor[armMotor] = 127
    elif joy1Btn(8):
      motor[armMotor] = -63
    else:
      motor[armMotor] = 0

    if joy1Btn(5):
      motor[clawMotor] = 127
    elif joy1Btn(7):
      motor[clawMotor] = -127
    else:
      motor[clawMotor] = 0
    
    if joy1Btn(4):
      motor[leftExtenderMotor] = motor[rightExtenderMotor] = 127
    elif joy1Btn(2):
      motor[leftExtenderMotor] = motor[rightExtenderMotor] = -127
    else:
      motor[leftExtenderMotor] = motor[rightExtenderMotor] = 0
      
    if joy1Btn(1):
      motor[wristMotor] = 127
    elif joy1Btn(3):
      motor[wristMotor] = -127
    else:
      motor[wristMotor] = 0
