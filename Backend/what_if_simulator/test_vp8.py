import cv2
print("Testing vp80 codec")
try:
    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    out = cv2.VideoWriter("test_vp8.webm", fourcc, 30, (640, 480))
    if out.isOpened():
        print("VP80 is supported!")
        import numpy as np
        out.write(np.zeros((480, 640, 3), dtype=np.uint8))
        out.release()
    else:
        print("VP80 is NOT supported.")
except Exception as e:
    print(f"Error: {e}")
