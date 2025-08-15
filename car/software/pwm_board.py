import smbus2

CONTROL_MODE_FREQ: int = 0b0101
CONTROL_MODE_DUTY: int = 0b1010

class mAntPWMBoard:
    """
        Controls my CH32V003-based "mAnt PWM Board" over I2C. 
        Works out of the box after activating I2C in raspi-config and in /boot/firmware/config.txt
        
        By default SDA is connected to GPIO2 and SCL to GPIO3 (Refer to the Raspberry Pi 5 pinout).
    """

    address = None
    bus = None
    
    # Dictated by the mAntPWM board
    PWM_MAX_DUTY: int = 1000
    PWM_MAX_FREQ: int = 48000
    
    def __init__(self, address=0x17, bus=1):
        self.address = address
        self.bus = smbus2.SMBus(bus)

    # Channel 1 and 2 share a common frequency. Same goes for channels 3 and 4.
    def set_ch_frequency(self, channel: int, frequency: int):
        if channel > 4 or channel < 1:
            print(f"Failed to set frequency - Only channels [1, 2, 3, 4] are supported!")
            return
        
        if frequency > self.PWM_MAX_FREQ or frequency < 1:
            print(f"PWM frequency must be within the [1; {self.PWM_MAX_FREQ}] range!")
            return
            
        self.bus.write_byte(self.address, (channel << 4) | CONTROL_MODE_FREQ)
        self.bus.write_byte(self.address, (frequency & 0xFF))
        self.bus.write_byte(self.address, ((frequency >> 8) & 0xFF))
        
    def set_ch_duty_cycle(self, channel: int, duty_cycle: int):
        if channel > 4 or channel < 1:
            print(f"Failed to set duty cycle - Only channels [1, 2, 3, 4] are supported!")
            return
        
        if duty_cycle > self.PWM_MAX_DUTY or duty_cycle < 0:
            print(f"PWM duty cycle must be within the [0; {self.PWM_MAX_DUTY}] range!")
            return
        
        self.bus.write_byte(self.address, (channel << 4) | CONTROL_MODE_DUTY)
        self.bus.write_byte(self.address, (duty_cycle & 0xFF))
        self.bus.write_byte(self.address, ((duty_cycle >> 8) & 0xFF))
        

    