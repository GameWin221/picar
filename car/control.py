import gpiod
from gpiod.line import Direction, Value
import time
from rpi_hardware_pwm import HardwarePWM

MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5
MAX_STEER_ANGLE = 20.0
PIN_FORWARD = 6
PIN_BACKWARD = 5


# angle: [0.0, 180.0], 0.0 == left, 90.0 == center, 180.0 == right
def servo_val(angle: float) -> float:
    angle = max(0.0, min(180.0, angle))
    return (MIN_PULSE_MS + angle / 180.0 * (MAX_PULSE_MS - MIN_PULSE_MS)) / 20.0 * 100.0

gpiod_lines = gpiod.request_lines("/dev/gpiochip0", consumer="robot-controller", config = {
    PIN_FORWARD: gpiod.LineSettings(
        direction=Direction.OUTPUT, output_value=Value.INACTIVE
    ),
    PIN_BACKWARD: gpiod.LineSettings(
        direction=Direction.OUTPUT, output_value=Value.INACTIVE
    )
})
servo = HardwarePWM(pwm_channel=2, hz=50, chip=2)
motors = HardwarePWM(pwm_channel=3, hz=1000, chip=2)

# angle: [-MAX_STEER_ANGLE, MAX_STEER_ANGLE], positive values turn to the right
def steer(angle: float):
    global servo

    angle = max(-MAX_STEER_ANGLE, min(MAX_STEER_ANGLE, angle))
    
    servo_angle = 90.0 + angle
    servo.change_duty_cycle(servo_val(servo_angle))

def drive(val: float):
    global motors, pin_forward, pin_backward

    if val > 0.0:
        gpiod_lines.set_value(PIN_FORWARD, Value.ACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.INACTIVE)
    elif val == 0.0:
        gpiod_lines.set_value(PIN_FORWARD, Value.INACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.INACTIVE)
    else:
        gpiod_lines.set_value(PIN_FORWARD, Value.INACTIVE)
        gpiod_lines.set_value(PIN_BACKWARD, Value.ACTIVE)

    motors.change_duty_cycle(max(0.0, min(100.0, abs(val))))

def start():
    servo.start(servo_val(90))
    motors.start(0.0)

def stop():
    servo.stop()
    motors.stop()

