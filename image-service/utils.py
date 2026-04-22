import os
import gdown

def download_model(model_path, url):
    if not os.path.exists(model_path):
        print("⬇️ Downloading model from Google Drive...")

        gdown.download(url, model_path, quiet=False)

        if not os.path.exists(model_path):
            raise RuntimeError("❌ Model download failed!")

        print("✅ Model downloaded successfully")
