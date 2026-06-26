import sys
import os

# Ensure paths
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
WAGON_DETECTION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "wagon number detection"))
if WAGON_DETECTION_PATH not in sys.path:
    sys.path.append(WAGON_DETECTION_PATH)

from main import process_video_task

if __name__ == "__main__":
    input_video = os.path.abspath(os.path.join(WAGON_DETECTION_PATH, "vids", "4.MP4"))
    output_video = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "processed", "test_output.mp4"))
    print(f"Testing process_video_task... input: {input_video}")
    try:
        process_video_task(999999, input_video, output_video)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
