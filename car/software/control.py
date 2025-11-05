import gpiod
from gpiod.line import Direction, Value
import time
#from rpi_hardware_pwm import HardwarePWM
from pwm_board import mAntPWMBoard
import threading
import asyncio

control_lock = threading.Lock()

FILTERING_ENABLE = False
TIMESTEP = 0.02

# Max servo rotational speed in degrees/s
MAX_STEER_CHANGE_RATE = 180.0
steer_target = 0.0
steer_current = 0.0

# Max motor speed change in percent/s
MAX_DRIVE_CHANGE_RATE = 100.0
drive_target = 0.0
drive_current = 0.0

MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5
MAX_STEER_ANGLE = 30.0
PIN_FORWARD = 6
PIN_BACKWARD = 5

gpiod_lines = gpiod.request_lines("/dev/gpiochip0", consumer="robot-controller", config = {
    PIN_FORWARD: gpiod.LineSettings(
        direction=Direction.OUTPUT, output_value=Value.INACTIVE
    ),
    PIN_BACKWARD: gpiod.LineSettings(
        direction=Direction.OUTPUT, output_value=Value.INACTIVE
    )
})

pwm = mAntPWMBoard()

def set_steer_target(angle: float):
    global control_lock, steer_target
    
    if not FILTERING_ENABLE:
        steer(angle)    
    else:
        with control_lock:
            steer_target = angle
        
def set_drive_target(val: float):
    global control_lock, drive_target
    
    if not FILTERING_ENABLE:
        drive(val)
    else:    
        with control_lock:
            drive_target = val

# angle: [0.0, 180.0], 0.0 == left, 90.0 == center, 180.0 == right
# returns [MIN_PULSE_MS, MAX_PULSE_MS]
def servo_val(angle: float) -> float:
    angle = max(0.0, min(180.0, angle))
    return (MIN_PULSE_MS + (angle / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS))

# angle: [-MAX_STEER_ANGLE, MAX_STEER_ANGLE], positive values turn to the right
def steer(angle: float):
    global pwm

    angle = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, angle))
    
    val = mAntPWMBoard.PWM_MAX_DUTY * servo_val(90.0+angle) / (1000.0/50.0) #20ms

    pwm.set_ch_duty_cycle(1, int(val))
    
def drive(val: float):
    global pwm, pin_forward, pin_backward

    if val > 0.0:
        gpiod_lines.set_value(PIN_FORWARD, Value.ACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.INACTIVE)
    elif val == 0.0:
        gpiod_lines.set_value(PIN_FORWARD, Value.INACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.INACTIVE)
    else:
        gpiod_lines.set_value(PIN_FORWARD, Value.INACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.ACTIVE)

    adj = int(val / 100.0 * mAntPWMBoard.PWM_MAX_DUTY)
    
    if adj < 0:
        pwm.set_ch_duty_cycle(3, -adj)
        pwm.set_ch_duty_cycle(4, 0)
    else:
        pwm.set_ch_duty_cycle(3, 0)
        pwm.set_ch_duty_cycle(4, adj)

def start():
    pwm.set_ch_frequency(1, 50)
    pwm.set_ch_frequency(3, 12000)
    pwm.set_ch_frequency(4, 12000)

def stop():
    pwm.set_ch_duty_cycle(1, 0)
    pwm.set_ch_duty_cycle(2, 0)
    pwm.set_ch_duty_cycle(3, 0)
    pwm.set_ch_duty_cycle(4, 0)

# Returns v so that: -m <= v <= m
def clamp_margin(v: float, m: float) -> float:
    return min(m, max(-m, v))

# run with asyncio
async def control_loop():
    global control_lock
    global steer_target, steer_current
    global drive_target, drive_current
    
    if not FILTERING_ENABLE:
        return
    
    while True:
        with control_lock:
            steer_current += clamp_margin(steer_target - steer_current, MAX_STEER_CHANGE_RATE * TIMESTEP)
            drive_current += clamp_margin(drive_target - drive_current, MAX_DRIVE_CHANGE_RATE * TIMESTEP)
            #print(steer_current, drive_current)
            
            steer(steer_current)
            drive(drive_current)
            
        await asyncio.sleep(TIMESTEP)
