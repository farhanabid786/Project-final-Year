import os
import io
import urllib.request
import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
from model import DEFAULT_MODEL_CONFIG

# ---------------- FACE DETECTOR ----------------
_PROTO_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
_WEIGHTS_URL = "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

def download_face_detector(detector_dir):
    os.makedirs(detector_dir, exist_ok=True)

    proto = os.path.join(detector_dir, "deploy.prototxt")
    model = os.path.join(detector_dir, "res10_300x300_ssd_iter_140000.caffemodel")

    if not os.path.exists(proto):
        urllib.request.urlretrieve(_PROTO_URL, proto)

    if not os.path.exists(model):
        urllib.request.urlretrieve(_WEIGHTS_URL, model)

    return proto, model

def load_face_net(detector_dir):
    proto, weights = download_face_detector(detector_dir)
    return cv2.dnn.readNetFromCaffe(proto, weights)

# ---------------- TRANSFORM (MATCH TRAINING) ----------------
transform = transforms.Compose([
    transforms.Resize((380, 380)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ---------------- IMAGE LOADER ----------------
def load_image(image_bytes):
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is not None:
        return img

    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

# ---------------- FACE DETECTION ----------------
def detect_face(img, net):
    h, w = img.shape[:2]

    blob = cv2.dnn.blobFromImage(img, 1.0, (300,300), (104,177,123))
    net.setInput(blob)
    detections = net.forward()

    best = None
    best_conf = 0

    for i in range(detections.shape[2]):
        conf = detections[0,0,i,2]
        if conf > 0.5 and conf > best_conf:
            best_conf = conf
            box = detections[0,0,i,3:7] * np.array([w,h,w,h])
            best = box.astype(int)

    if best is None:
        # fallback center crop
        size = min(w,h)
        cx, cy = w//2, h//2
        return img[cy-size//2:cy+size//2, cx-size//2:cx+size//2], False

    x1,y1,x2,y2 = best
    return img[y1:y2, x1:x2], True

# ---------------- PREDICTION ----------------
def predict_from_bytes(image_bytes, model, face_net, device, threshold):
    img = load_image(image_bytes)
    face, detected = detect_face(img, face_net)

    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    face = Image.fromarray(face)

    tensor = transform(face).unsqueeze(0).to(device)

    with torch.no_grad():
        prob = torch.sigmoid(model(tensor)).item()

    label = "FAKE" if prob >= threshold else "REAL"

    return {
        "label": label,
        "confidence": round(max(prob, 1-prob)*100, 2),
        "fake_prob": round(prob*100, 2),
        "real_prob": round((1-prob)*100, 2),
        "face_detected": detected,
        "threshold": threshold
    }
