import smbus2

CONTROL_MODE_FREQ: int = 0b0101
CONTROL_MODE_DUTY: int = 0b1010

class PCBDriver:
    """
        Controls the external PCB over I2C. 
        Works out of the box after activating I2C in raspi-config and in /boot/firmware/config.txt
        
        By default SDA is connected to GPIO2 and SCL to GPIO3 (Refer to the Raspberry Pi 5 pinout).
    """

    address = None
    bus = None
    
    # Dictated by the CH32V003 firmware
    PWM_MAX_DUTY: int = 1000
    PWM_MAX_FREQ: int = 48000
    
    PWM_SERVO_TIMER: int = 1
    PWM_MOTOR_TIMER: int = 2
    
    PWM_RIGHT_MOTOR_CH: int = 3
    PWM_LEFT_MOTOR_CH: int = 4
    
    def __init__(self, address=0x17, bus=1):
        self.address = address
        self.bus = smbus2.SMBus(bus)

    def set_timer_frequency(self, timer: int, frequency: int):
        if timer not in [1, 2]:
            print(f"Failed to set frequency - Only timers [1, 2] are supported!")
            return
        
        if frequency > self.PWM_MAX_FREQ or frequency < 1:
            print(f"PWM frequency must be within the [1; {self.PWM_MAX_FREQ}] range!")
            return
            
        self.bus.write_word_data(self.address, timer, frequency)
        
    def set_ch_duty(self, timer: int, channel: int, duty_cycle: int):
        if timer not in [1, 2]:
            print(f"Failed to set duty cycle - Only timers [1, 2] are supported!")
            return
        
        if timer == 1:
            if channel > 4 or channel < 1:
                print(f"Failed to set duty cycle - Only channels [1, 2, 3, 4] are supported for timer 1!")
                return
        elif timer == 2:
            if channel > 4 or channel < 3:
                print(f"Failed to set duty cycle - Only channels [3, 4] are supported for timer 2!")
                return

        if duty_cycle > self.PWM_MAX_DUTY or duty_cycle < 0:
            print(f"PWM duty cycle must be within the [0; {self.PWM_MAX_DUTY}] range!")
            return
        
        self.bus.write_word_data(self.address, timer * 4 + channel - 1, duty_cycle)
        
    def set_motor_direction(self, direction: int):
        if direction not in [-1, 0, 1]:
            print(f"Failed to set motor direction - Only directions [-1, 0, 1] are supported! (0 = stop, 1 = forward, -1 = backward)")
            return
          
        dirf = 1 if direction == 1 else 0
        dirb = 1 if direction == -1 else 0
                
        self.bus.write_word_data(self.address, 12, dirf | (dirb << 8))
    