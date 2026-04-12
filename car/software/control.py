import time
from pcb_driver import PCBDriver
import threading
import asyncio

control_lock = threading.Lock()

FILTERING_ENABLE = True
TIMESTEP = 0.02

# Max servo rotational speed in degrees/s
MAX_STEER_CHANGE_RATE = 270.0
steer_target = 0.0
steer_current = 0.0

# Max motor speed change in percent/s
MAX_DRIVE_CHANGE_RATE = 200.0
drive_target = 0.0
drive_current = 0.0

MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5
MAX_STEER_ANGLE = 30.0
PIN_FORWARD = 6
PIN_BACKWARD = 5

pcb = PCBDriver()

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
    global pcb

    angle = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, angle))
    
    val = pcb.PWM_MAX_DUTY * servo_val(90.0+angle) / (1000.0/50.0) #20ms

    pcb.set_ch_duty(pcb.PWM_SERVO_TIMER, 1, int(val))
    
def drive(val: float):
    global pcb

    adj = int(val / 100.0 * pcb.PWM_MAX_DUTY)

    if val > 0.0:
        pcb.set_motor_direction(1)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_RIGHT_MOTOR_CH, adj)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_LEFT_MOTOR_CH, adj)
    elif val == 0.0:
        pcb.set_motor_direction(0)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_RIGHT_MOTOR_CH, 0)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_LEFT_MOTOR_CH, 0)
    else:
        pcb.set_motor_direction(-1)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_RIGHT_MOTOR_CH, -adj)
        pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_LEFT_MOTOR_CH, -adj)

def start():
    pcb.set_timer_frequency(pcb.PWM_SERVO_TIMER, 50)
    pcb.set_timer_frequency(pcb.PWM_MOTOR_TIMER, 12000)
    steer(0.0)
    drive(0.0)

def stop():
    pcb.set_ch_duty(pcb.PWM_SERVO_TIMER, 1, 0)
    pcb.set_ch_duty(pcb.PWM_SERVO_TIMER, 2, 0)
    pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, 3, 0)
    pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, 4, 0)
    
    pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_RIGHT_MOTOR_CH, 0)
    pcb.set_ch_duty(pcb.PWM_MOTOR_TIMER, pcb.PWM_LEFT_MOTOR_CH, 0)

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
