import itertools
import cv2 as cv
import numpy as np
import picamera2
from picamera2 import Picamera2
from libcamera import Transform

camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'RGB888', "size": (1280, 720)}, transform=Transform(hflip=1, vflip=1)))
camera.start()

def _locate_marker_on_img(src: cv.Mat):
    lab_frame = cv.cvtColor(src, cv.COLOR_BGR2LAB)
    (l, _, _) = cv.split(lab_frame)

    l = cv.bilateralFilter(l, d=9, sigmaColor=75, sigmaSpace=75)

    avg_l = int(np.average(l))
    std_v = int(np.std(l))
                         
    inBlack  = np.array([avg_l - std_v // 2], dtype=np.float32)
    inWhite  = np.array([255], dtype=np.float32)
    inGamma  = np.array([2.0], dtype=np.float32)
    outBlack = np.array([0], dtype=np.float32)
    outWhite = np.array([255], dtype=np.float32)

    l = np.clip( (l - inBlack) / (inWhite - inBlack), 0, 255 )                            
    l = ( l ** (1/inGamma) ) *  (outWhite - outBlack) + outBlack
    l = np.clip( l, 0, 255).astype(np.uint8)
    
    print("average lightness: ", avg_l, std_v)
    
    _, dark_regions = cv.threshold(l, avg_l + std_v * 0.1, 255, cv.THRESH_BINARY_INV)
    
    params = cv.SimpleBlobDetector_Params()
    
    params.filterByColor = True
    params.blobColor = 255
    
    params.filterByArea = True
    params.minArea = 40
    params.maxArea = l.shape[0] * l.shape[1] * 0.1
    
    params.filterByCircularity = True
    params.minCircularity = 0.6
    params.filterByConvexity = False
    params.filterByInertia = True
    params.minInertiaRatio = 0.6
    
    detector = cv.SimpleBlobDetector_create(params)
    keypoints = detector.detect(dark_regions)
    
    final_color = cv.cvtColor(dark_regions, cv.COLOR_GRAY2BGR)
    for kp in keypoints:
        x, y = int(kp.pt[0]), int(kp.pt[1])
        #area = (kp.size / 2) ** 2 * np.pi
        #cv.putText(final_color, f"{area:.2f}", (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv.LINE_AA)
        cv.circle(final_color, (x, y), 5, (0, 0, 255), 2)
    
    cv.imwrite('frame.jpg', src)
        
    if len(keypoints) > 0:
        avg_px = int(sum(map(lambda k: k.pt[0], keypoints)) / len(keypoints))
        avg_py = int(sum(map(lambda k: k.pt[1], keypoints)) / len(keypoints))

        std_x = int(np.ceil(np.std(np.array(list(map(lambda k: k.pt[0], keypoints))))) * 0.65)
        std_y = int(np.ceil(np.std(np.array(list(map(lambda k: k.pt[0], keypoints))))) * 0.65)

        biggest_kp = max(keypoints, key=lambda k: k.size)
        cx, cy = int(biggest_kp.pt[0]), int(biggest_kp.pt[1])

        # Area in which the center point is expected to be (standard deviation for x and y)
        cv.rectangle(final_color, (avg_px-std_x, avg_py-std_y), (avg_px+std_x, avg_py+std_y), (0, 255, 0), 2)
        # Average center of the marker
        cv.circle(final_color, (avg_px, avg_py), 10, (0, 255, 0), 5)
        # Center of a midpoint candidate
        cv.circle(final_color, (cx, cy), 10, (255, 0, 0), 2)

        dx, dy = abs(cx - avg_px), abs(cy - avg_py)
        if dx <= std_x and dy <= std_y and len(keypoints) >= 3:
            # If the midpoint candidate fits within the standard deviation * multiplier
            # then we are sure that it is the correct marker midpoint
            print(f"Found marker at: {cx, cy}")
            return (cx, cy) 
        else:
            # Otherwise we estimate the marker midpoint position based on the average of keypoints
            print(f"Marker may be around: {avg_px, avg_py}")
            return (avg_px, avg_py)
    return None

def _locate_color_marker_on_img(src: cv.Mat):
    hsv_frame = cv.cvtColor(src, cv.COLOR_BGR2HSV_FULL)
    (h, s, _) = cv.split(hsv_frame)
    
    h = cv.bilateralFilter(h, d=6, sigmaColor=75, sigmaSpace=75)
    s = cv.bilateralFilter(s, d=6, sigmaColor=75, sigmaSpace=75)
    _, s = cv.threshold(s, 145, 255, cv.THRESH_BINARY)
    
    r = cv.inRange(h, 15, 230)
    r = cv.bitwise_not(r)
    
    g = cv.inRange(h, 50, 125)
    b = cv.inRange(h, 125, 160)
    
    #cv.imshow(str(np.sum(h)), np.concatenate((src, cv.cvtColor(h, cv.COLOR_GRAY2BGR), cv.cvtColor(s, cv.COLOR_GRAY2BGR))))
    #cv.imshow(str(np.sum(h)), np.concatenate((r, g, b, s), axis=1))
    final = cv.bitwise_and(cv.bitwise_or(cv.bitwise_or(r, g), b), s)
    
    params = cv.SimpleBlobDetector_Params()
    
    params.filterByColor = True
    params.blobColor = 255
    
    params.filterByArea = True
    params.minArea = 40
    params.maxArea = s.shape[0] * s.shape[1] * 0.1
    
    params.filterByCircularity = True
    params.minCircularity = 0.8
    params.filterByConvexity = False
    params.filterByInertia = True
    params.minInertiaRatio = 0.8
    
    detector = cv.SimpleBlobDetector_create(params)
    keypoints = detector.detect(final)
    print(len(keypoints))    
    final_color = cv.cvtColor(final, cv.COLOR_GRAY2BGR)
    #for kp in keypoints:
        #x, y = int(kp.pt[0]), int(kp.pt[1])
        #area = (kp.size / 2) ** 2 * np.pi
        #cv.putText(final_color, f"{area:.2f}", (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv.LINE_AA)
        #cv.circle(final_color, (x, y), 5, (0, 0, 255), 2)
    
    if len(keypoints) > 0:
        avg_px = int(sum(map(lambda k: k.pt[0], keypoints)) / len(keypoints))
        avg_py = int(sum(map(lambda k: k.pt[1], keypoints)) / len(keypoints))
    
        #std_x = int(np.ceil(np.std(np.array(list(map(lambda k: k.pt[0], keypoints))))) * 0.65)
        #std_y = int(np.ceil(np.std(np.array(list(map(lambda k: k.pt[0], keypoints))))) * 0.65)
        size_ratios = []
        for a, b in itertools.combinations(keypoints, 2):
            size_ratios.append(a.size / b.size)

        # Are all keypoints similar in size?
        all_kp_similar = all([0.8 < r < 1.2 for r in size_ratios])
        
        # Average center of the marker
        #cv.circle(final_color, (avg_px, avg_py), 10, (0, 255, 0), 5)

        #cv.imshow(str(np.sum(h)+1), np.concatenate((src,  final_color), axis=1))
        
        if len(keypoints) == 3 and all_kp_similar:
            # If the midpoint candidate fits within the standard deviation * multiplier
            # then we are sure that it is the correct marker midpoint
            print(f"Found marker at: {avg_px, avg_py}")
        else:
            # Otherwise we estimate the marker midpoint position based on the average of keypoints
            print(f"Marker may be around: {avg_px, avg_py}")
        
        return (avg_px, avg_py)
    
    return None

def locate_marker():
    frame = camera.capture_array()
    return _locate_color_marker_on_img(frame)

