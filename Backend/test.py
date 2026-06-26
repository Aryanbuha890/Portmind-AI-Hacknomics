from ultralytics import YOLO

model = YOLO("E:/Portmind-AI-Hacknomics/Backend/runs/detect/railway_hackathon/wagon_counter_v1/weights/best.pt")

results = model.predict(
    source="E:/Portmind-AI-Hacknomics/Backend/2.mp4",
    conf=0.25,
    save=True
)