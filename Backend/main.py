from ultralytics import YOLO


def train():
    # Load pretrained model
    model = YOLO("E:/Portmind-AI-Hacknomics/Backend/runs/detect/runs/train/yolo11_custom-2/weights/last.pt")

     # Train
    results = model.train(
        resume=True,
    )

    print("Training completed!")


if __name__ == "__main__":
    train()