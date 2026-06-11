# import os
# import gdown

# def download_model(model_path, url):
#     if not os.path.exists(model_path):
#         print("⬇️ Downloading model from Google Drive...")

#         gdown.download(url, model_path, quiet=False)

#         if not os.path.exists(model_path):
#             raise RuntimeError("❌ Model download failed!")

#         print("✅ Model downloaded successfully")

import os
import requests

def download_model(model_path, url):
    if os.path.exists(model_path):
        return

    response = requests.get(url, stream=True)

    if response.status_code != 200:
        raise RuntimeError("Model download failed")

    with open(model_path, "wb") as f:
        for chunk in response.iter_content(8192):
            if chunk:
                f.write(chunk)
            if chunk:
                f.write(chunk)
