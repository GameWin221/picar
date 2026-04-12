import sys, traceback
import time
import asyncio
from websockets.asyncio.server import serve
import math
import control
import vision
import threading
import http.server

async def main_remote_control():
    def run_http_server():
        server = http.server.HTTPServer(('0.0.0.0', 8000), http.server.SimpleHTTPRequestHandler)
        server.serve_forever()
    
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    control.start()
    controlloop = asyncio.create_task(control.control_loop())

    async def serve_callback(websocket):
        async for message in websocket:
            parts = message.split()
            if parts[0] == "steer":
                control.set_steer_target(float(parts[1]))
            elif parts[0] == "motors":
                control.set_drive_target(float(parts[1]))
            elif parts[0] == "motorfreq":
                control.pcb.set_timer_frequency(control.pcb.PWM_MOTOR_TIMER, int(parts[1]))
                
            print(parts)
    
    async with serve(serve_callback, "0.0.0.0", 8080) as server:
        await server.serve_forever()
    
    await controlloop

def main_vision():
    vision.init_camera()
    
    while True:
        marker = vision.locate_marker()
        if marker != None:
            mx, my = marker
            halfx = 1280.0 / 2.0
            halfy = 720.0 / 2.0
            if mx > halfx:
                control.steer((mx - halfx) / halfx * control.MAX_STEER_ANGLE)
            else:
                control.steer((mx - halfx) / halfx * control.MAX_STEER_ANGLE)

            control.drive(my / 720.0 * 100.0)
        else:
            control.drive(0.0)
            
        time.sleep(0.1)

def main_test():
    t = 0.0
    while True:
        control.steer(math.sin(3.1415926 * t)*30.0)
        time.sleep(0.05)
        t += 0.05

if __name__ == "__main__":
    try:
        match sys.argv[-1]:
            case 'vision':
                print("Running the \"Vision\" main loop")
                main_vision()
            case 'test':
                print("Running the \"Test\" main loop")
                main_test()
            case _:
                print("Running the \"Remote Control\" main loop")
                asyncio.run(main_remote_control())
 
    except KeyboardInterrupt:
        print("\nShutdown requested...exiting")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    
    control.stop()
    sys.exit(0)
