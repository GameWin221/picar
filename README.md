# picar
Car with autonomous and remote-controlled capabilities using the Raspberry Pi 5 

![pic1](/images/pic1.jpg)

![pic2](/images/pic2.jpg)

# Hardware
- Powered by a custom made battery pack composed of 3x 18650 cells connected in series. It has both XT60 connector for the main power and 4-pin JST-XH used for balancing.
- SG92R micro servo for steering
- Raspberry Pi 5 8GB
- Raspberry Pi Camera HD v2 8MPx
- LM2596 step-down converter rated for 3A and set to (a bit more than) 5.1V used for powering the Raspberry Pi
- L298N motor driver used for motor control and for generating 5V powering the servo
- Cheap unnamed battery level indicator
- Custom 3D-printed frame and steering system (files available in the "designs" directory)
- 4x 60x8mm black Pololu 1420 wheels
- 2x 6x13x5mm bearings for the front wheels
- 2x N20-BT07 micro 100:1 320RPM 12V motors
- M3 screws used for assembling the frame and wheels together
- Zip-ties used where needed
- A small breadboard and a bunch of resistors and transistors used for controlling the motor direction with a single PWM channel (I explained it in the paragraph below)

## Saving up on PWM channels
Raspberry Pi 5 can generate only 2 channels of hardware PWM at once and I had to provide at least 3 PWM signals - one to control the servo, one for driving forward and one for driving backward. Since I didn't want to use software-based PWM I had to somehow cut down the number of signals. The obvious choice was to use only one PWM signal for the motors and to control the direction with digital outputs. I did it simply by switching the single PWM signal with two transistors going into separate inputs on the motor driver. 

(I will make an image here..)

# Software and control

(I will write more here in near future once I find some spare time...)