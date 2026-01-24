# Progress over time

## V3 (November 2025 / January 2026)

![picarV3early1](/images/picarV3Early2.jpg)
![picarV3early2](/images/picarV3Early1.jpg)

**You can read about it in the main README for as long as it is the newest version.**

## V2 (August 2025)

![pic1](/images/picarV2_1.jpg)
![pic2](/images/picarV2_2.jpg)

### Hardware
- [...] Same as V1 except for:
- Custom PWM control board based on CH32V003 (More on that [below](#ch32v003-mantpwm-pwm-board))
- A small breadboard used only for making the jumper wire connections easier to manage for now. *(I will get rid of it eventually because it doesn't look good)*

### CH32V003 "mAntPWM" PWM Board

![mantpwm](/images/mantpwm.png)

*(The KiCad design files are in the `/pwm_board/design` directory)*

The board was designed and created to improve the PWM signal management. Raspberry Pi 5 itself was not enough because it can handle only 2 hardware PWM channels and I needed at least 3 channels so creating the board was both a solution to this problem and a cool sub-project to work on. Before making this board I came up with a temporary solution which you can read about [below](#saving-up-on-pwm-channels-before-the-pwm-board). 

Now I can see some flaws in the design such as wasted PWM outputs (I could've had up to 8 outputs instead of 4) or no on-board pull-up resistors for I2C but the board works as intended so I won't be ordering any new designs for now. 

### RPi 5 <-> mAntPWM coomunication
The RPi 5 communicates with the CH32V003 chip via I2C using a simple protocol documented in `/pwm_board/firmware/CH32V003A4M6/User/main.c`. You can also understand it better by reading the control functions in `/car/software/pwm_board.py`.

## V1 (April 2025)

![v1pic1](/images/old.jpg)
![v1pic2](/images/oldpic1.jpg)

### Hardware
- Powered by a custom made battery pack composed of 3x 18650 cells connected in series. It has both XT60 connector for the main power and 4-pin JST-XH used for balancing.
- SG92R micro servo for steering
- Raspberry Pi 5 8GB
- Raspberry Pi Camera HD v2 8MPx
- Custom PWM control board based on CH32V003 (More on that [below](#ch32v003-mantpwm-pwm-board))
- LM2596 step-down converter rated for 3A and set to (a bit more than) 5.1V used for powering the Raspberry Pi
- L298N motor driver used for motor control and for generating 5V powering the servo
- Cheap unnamed battery level indicator
- Custom 3D-printed frame and steering system (files available in the "designs" directory)
- 4x 60x8mm black Pololu 1420 wheels
- 2x 6x13x5mm bearings for the front wheels
- 2x N20-BT07 micro 100:1 320RPM 12V motors
- M3 screws used for assembling the frame and wheels together
- Breadboard with two BC337 transistors and required resistors.

### Saving up on PWM channels before the PWM board
Raspberry Pi 5 can generate only 2 channels of hardware PWM at once and I had to provide at least 3 PWM signals - one to control the servo, one for driving forward and one for driving backward. Since I didn't want to use software-based PWM I had to somehow cut down the number of signals. The obvious choice was to use only one PWM signal for the motors and to control the direction with digital outputs. I did it simply by switching the single PWM signal with two transistors going into separate inputs in the motor driver. 

![oldpwm](/car/design/v1/old_pwm_control.png)

*Irl it was a messy setup on a breadboard as you can imagine.*