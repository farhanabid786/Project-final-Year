import os
import gdown

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODEL_DIR, exist_ok=True)

# ===== YOUR GOOGLE DRIVE LINKS =====
EFF_URL = "https://drive.google.com/uc?id=1xigFpgBhZrlwRn4FWX8LZaf7_Rq5E7G3"
TF_URL  = "https://drive.google.com/uc?id=1xwuOR6UsC9bEMoMZgk2slrtXMlrLZYcB"

EFF_PATH = os.path.join(MODEL_DIR, "best_model_v3.pth")
TF_PATH  = os.path.join(MODEL_DIR, "deepfake_model.h5")


def download_models():
    if not os.path.exists(EFF_PATH):
        print("⬇️ Downloading EfficientNet model...")
        gdown.download(EFF_URL, EFF_PATH, quiet=False)

    if not os.path.exists(TF_PATH):
        print("⬇️ Downloading TensorFlow model...")
        gdown.download(TF_URL, TF_PATH, quiet=False)

    print("✅ Models ready")
