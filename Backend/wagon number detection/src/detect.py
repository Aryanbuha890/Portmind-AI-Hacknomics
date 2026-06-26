import cv2
import sys
import os

# Get the absolute path to the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

# Add the parent directory to sys.path to allow importing 'wnd'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from wnd import WagonNumberDetection

# Use absolute paths for videos to avoid CWD issues
videoPath = os.path.join(parent_dir, "vids", "3.mp4")
output_path = os.path.join(parent_dir, "results", "output3.mp4")

# Ensure results directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

vid = cv2.VideoCapture(videoPath)
if not vid.isOpened():
    print(f"Error: Could not open video file at {videoPath}")
    sys.exit(1)

# --- Setup Video Writer ---
frame_width = int(vid.get(3))
frame_height = int(vid.get(4))
fps = int(vid.get(cv2.CAP_PROP_FPS))
if fps <= 0:
    fps = 30 # Fallback FPS

# Ensure output frame size matches the resized output from DetectWagonNumber
# DetectWagonNumber resizes to height 480
new_height = 480
new_width = int(frame_width * (new_height / frame_height))

fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
# --------------------------

previousWagonNumber = ""
currentWagonNumber = ""

print(f"Processing video... Saving to {output_path}")

frame_count = 0
detected_numbers = set()

while True:
    ret, frame = vid.read()

    if not ret:
        print("End of video.")
        break
    
    frame_count += 1
    
    # Run the model
    wagonNumber, outputFrame = WagonNumberDetection.DetectWagonNumber(frame)

    currentWagonNumber = wagonNumber
    if currentWagonNumber == "":
        pass # No number detected
    elif currentWagonNumber != previousWagonNumber:
        # A new number was detected!
        clean_number = "".join(filter(str.isalnum, currentWagonNumber))
        if len(clean_number) >= 11 and clean_number not in detected_numbers:
            print(f"[Frame {frame_count}] Detected Wagon Number: {currentWagonNumber}")
            detected_numbers.add(clean_number)
            
        # Draw on the output frame
        cv2.putText(outputFrame, currentWagonNumber, (230, 380), cv2.FONT_HERSHEY_DUPLEX, 1.8, (255,255,255) , 1, cv2.LINE_AA)
        previousWagonNumber = currentWagonNumber
        
    # Write the modified frame to the file
    out.write(outputFrame)

    cv2.imshow("frame", outputFrame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vid.release()
out.release()
cv2.destroyAllWindows()

print("Done. Total unique wagons detected:", len(detected_numbers))
for w in detected_numbers:
    print("-", w)
