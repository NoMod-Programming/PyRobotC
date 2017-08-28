# PyRobotC
An attempt at creating a Python to RobotC compiler

## Usage:
    pyRobotC.py [file]

## Documentation
Uses a basic understanding of [PEP 484](https://www.python.org/dev/peps/pep-0484/) type annotations to assist in conversion to RobotC, which has static typing. The basic syntax is as follows:

    def add(number1: int, number2: int) -> int:
        return number1 + number2

## Included "modules"
This also includes pseudo-modules that either allow easier access to C functions from a pythonic interface, or allow non-pythonic functions to be used. They are the `vex` and `cfuncs` modules.

### The `vex` module
#### vex.`pragma(function[, arg1, arg2, ...])`
This allows `#pragma` statements to be used with PyRobotC. With a single argument, it simple generates the following code:

    pragma(systemFile) -> #pragma systemFile

With multiple arguments, it uses the first one as the "name" for the function, and the rest as arguments, such as the following example:

    vex.pragma(config, I2C_Usage, I2C1, i2cSensors) -> #pragma config(I2C_Usage, I2C1, i2cSensors)

#### vex.`motor(port, speed)`
This functions sets the specified motor on `port` to the specified `speed` (from 127 to -127).

#### vex.`slaveMotors(master,slave1[, slave2, ...])`
Slave motors to a master, that way all commands sent to the master will be sent to the slaves.

#### vex.`motorReversed(port, isReversed)`
Set whether or not a motor's direction is reversed by 180 degrees. Useful when a mechanical design results in a logical "reversed" condition of a motor

#### More functions coming soon!

### The `cfuncs` module
#### More functions coming soon!
