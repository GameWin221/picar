import sys, traceback
import socket
import time
import io
import asyncio
from websockets.asyncio.server import serve

import control
import vision

async def serve_callback(websocket):
    async for message in websocket:
        parts = message.split()
        if parts[0] == "steer":
            control.steer(float(parts[1]))
        elif parts[0] == "motors":
            control.drive(float(parts[1]))
        print(parts)

async def main():
    async with serve(serve_callback, "0.0.0.0", 8080) as server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        # Manual remote-control server
        #asyncio.run(main())
        
        # Autonomous control
        control.start()
        
        while True:
            marker = vision.locate_marker()
            if marker != None:
                mx, my = marker
                halfx = 1280.0 / 2.0
                halfy = 720.0 / 2.0
                if mx > halfx:
                    control.steer((mx - halfx) / halfx * 20.0)
                else:
                    control.steer((mx - halfx) / halfx * 20.0)
                
                #control.drive(my / 720.0 * 100.0)
            else:
                control.drive(0.0)
            time.sleep(0.1)
            

    except KeyboardInterrupt:
        print("Shutdown requested...exiting")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    
    control.stop()
    sys.exit(0)


