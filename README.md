# pyrover
The Pyrover is a compact battery-powered rover operating on a raspberry pi that is controlled via a webpage.
![alt text](https://github.com/i02132002/pyrover/blob/main/rover.jpg?raw=true)

## Demo
![alt text](https://github.com/i02132002/pyrover/blob/main/pyrover_demo_clip.mp4?raw=true)

## Hardware connections
The raspberry pi pinouts to the stepper motor controller (HW-95 : L298N STEPPER MOTOR DRIVER MODULE) are as follows:
Pin 24 --> IN2
Pin 23 --> IN1
Pin 25 --> ENA
Pin 6  --> IN4
Pin 5  --> IN3
Pin 26 --> ENB

Optionally, two servos providing yaw and pitch motion can be controlled on Pin 17 and Pin 27. Under development.

The battery is a rechargeable 8400mAh 3S2P lithium ion battery, providing 12V to the DC motors.
A 25W DC-DC converter (TOBSUN EA25-5V) is used to convert the 12V provided by the battery to 5V needed by the raspberry pi.

## How to run
Run `rpi_camera_surveilance_system.py` to start the webserver. The webpage will be hosted at `localhost:8000/index.html`.
To move the rover, click the arrow keys on the webpage, left/right to rotate and up/down to move forward/backward. Press the central button to stop the motion.

