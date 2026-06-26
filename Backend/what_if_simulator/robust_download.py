import os
import easyocr
import time
import sys

# Force standard encoding for Windows terminal when tqdm tries to print progress bars
import codecs
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

model_dir = os.path.expanduser('~/.EasyOCR/model')

def ensure_model():
    for attempt in range(5):
        try:
            print(f"Attempt {attempt + 1} to download EasyOCR models...")
            reader = easyocr.Reader(['en'], gpu=False)
            print("Successfully loaded EasyOCR!")
            return True
        except Exception as e:
            print(f"Failed: {e}")
            # Delete potentially corrupted files
            if os.path.exists(model_dir):
                for f in os.listdir(model_dir):
                    if f.endswith('.pth') or f.endswith('.zip'):
                        try:
                            os.remove(os.path.join(model_dir, f))
                        except:
                            pass
            time.sleep(2)
    return False

ensure_model()
