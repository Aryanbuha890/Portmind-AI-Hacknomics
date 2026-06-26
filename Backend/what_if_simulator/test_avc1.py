import cv2
print("Testing avc1 codec")
try:
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter("test_avc1.mp4", fourcc, 30, (640, 480))
    if out.isOpened():
        print("AVC1 is supported!")
        out.release()
    else:
        print("AVC1 is NOT supported.")
except Exception as e:
    print(f"Error: {e}")
