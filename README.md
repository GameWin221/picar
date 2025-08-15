# picar
Car with autonomous and remote-controlled capabilities using the Raspberry Pi 5 

![pic1](/images/pic1.jpg)

![pic2](/images/pic2.jpg)

# Hardware
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
- A small breadboard used only for making the jumper wire connections easier to manage for now. *(I will get rid of it eventually because it doesn't look good)*

## CH32V003 "mAntPWM" PWM Board

![mantpwm](/images/mantpwm.png)

*(The KiCad design files are in the `/pwm_board/design` directory)*

The board was designed and created to improve the PWM signal management. Raspberry Pi 5 itself was not enough because it can handle only 2 hardware PWM channels and I needed at least 3 channels so creating the board was both a solution to this problem and a cool sub-project to work on. Before making this board I came up with a temporary solution which you can read about [below](#saving-up-on-pwm-channels-before-the-pwm-board). 

The RPi 5 communicates with the CH32V003 chip via I2C using a simple protocol documented in `/pwm_board/firmware/CH32V003A4M6/User/main.c`. You can also understand it better by reading the control functions in `/car/software/pwm_board.py`. Read more about software/firmware in the [dedicated section below](#software-and-control)

Now I can see some flaws in the design such as wasted PWM outputs (I could've had up to 8 outputs instead of 4) or no on-board pull-up resistors for I2C but the board works as intended so I won't be ordering any new designs for now. 

### Saving up on PWM channels before the PWM board
Raspberry Pi 5 can generate only 2 channels of hardware PWM at once and I had to provide at least 3 PWM signals - one to control the servo, one for driving forward and one for driving backward. Since I didn't want to use software-based PWM I had to somehow cut down the number of signals. The obvious choice was to use only one PWM signal for the motors and to control the direction with digital outputs. I did it simply by switching the single PWM signal with two transistors going into separate inputs in the motor driver. 

![oldpwm](/car/design/v1/old_pwm_control.png)

*Irl it was a messy setup on a breadboard as you can imagine.*

# Software and control

## Frontend
It is possible to control **picar** through a simple web interface you can find in `/frontend/index.html`. There are two sliders that control it as the names suggest but the better (and way cooler) option is to use a gamepad and control the car this way. The website automatically detects connected gamepads and lets the user steer by using both triggers for accelerating and braking and the left thumbstick for steering.

There also is a viewport for watching the live feed coming from the camera connected to the RPi 5. The stream source must be a WebRTC source which can be created easily by using [MediaMTX](https://github.com/bluenviron/mediamtx). You can find the working `mediamtx.yml` file I use to enable the stream at `/car/sotware/mediamtx.yml`. Once mediamtx starts with my provided config, the camera can be accessed by connecting via WebRTC to `raspberry_pi_5_ip:8889/rpi`.

## Vision
**picar** is capable of detecting and following custom made markers. ... *I will write about it more soon.*

## Building the code

### RPi 5 Python
Configure the virtual environment if you need and run `pip install -r requirements.txt` while being in the `/car/software` directory to download the necessary packages. The `gpiod` (version 2.x) package might be troublesome because it most likely needs to be installed as a system package and not a local pip package. Same problem might occur for opencv. Once everything is downloaded, run `python main.py` and should run fine.

#### Enabling the necessary RPi 5 options
To make I2C communication work properly, enable it either with the `raspi-config` command or by manually adding the necessary lines to the `/boot/firmware/config.txt` file:

```
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=80000 # or any other as you wish
dtparam=i2s=on
```

Also enable the camera detection in the same way. Here is the line for `/boot/firmware/config.txt`:

```
camera_auto_detect=1
```

### CH32V003 C Firmware
Downloading and building it through MounRiver Studio IDE is the easiest route to go. This repo already has project files that work out of the box when you open them with the IDE. Just press F7 and it should build perfectly fine.

#### Flashing it
You'll need a **WCH LinkE** programmer in order to flash the firmware to the chip. Once you have it, connect GND to GND and the SWDIO pin to the chip's SWIO pin according to its datasheet *(It's pin PD1 for CH32V003A4M6)*. The chip must be powered either from the programmer's voltage pin or externally during flashing.

Now go to MounRiver Studio IDE and press F7 to build your project and then F8 to flash it having the WCH LinkE programmer plugged into your computer at the same time, **note that flashing your code does not rebuild it automatically, you have to remember to press F7 each time.**. You can also change the flashing configuration but it's almost always good to go by default. *(called Download Configuration)*:

![wchlinke](/images/WCHLinkEFlashing.png)

Do not press or hold the reset button during flashing (the NRST pin)