# import os
# import torch
# import threading

# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware

# from model import load_model
# from inference import load_face_net, predict_from_bytes
# from utils import download_model


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# MODEL_DIR = os.path.join(BASE_DIR, "models")
# os.makedirs(MODEL_DIR, exist_ok=True)

# MODEL_NAME = os.getenv("MODEL_NAME", "best_model_v3.pth")
# MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

# MODEL_URL = os.getenv(
#     "MODEL_URL",
#     "https://drive.google.com/uc?id=1xigFpgBhZrlwRn4FWX8LZaf7_Rq5E7G3"
# )

# DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

# DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# model = None
# face_net = None
# threshold = None
# lock = threading.Lock()


# def get_model():
#     global model, face_net, threshold

#     if model is None:
#         with lock:
#             if model is None:
#                 download_model(MODEL_PATH, MODEL_URL)
#                 model_loaded, threshold_loaded = load_model(MODEL_PATH, DEVICE)
#                 face_net_loaded = load_face_net(DETECTOR_DIR)

#                 model = model_loaded
#                 threshold = threshold_loaded
#                 face_net = face_net_loaded

#     return model, face_net, threshold


# def preload():
#     try:
#         get_model()
#     except Exception:
#         pass


# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.on_event("startup")
# def startup():
#     threading.Thread(target=preload).start()


# @app.get("/")
# def root():
#     return {"status": "running"}


# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "device": str(DEVICE),
#         "model_loaded": model is not None
#     }


# @app.post("/predict")
# async def predict(file: UploadFile = File(...)):
#     try:
#         contents = await file.read()

#         model_obj, face_net_obj, threshold_val = get_model()

#         result = predict_from_bytes(
#             contents,
#             model_obj,
#             face_net_obj,
#             DEVICE,
#             threshold_val
#         )

#         return {
#             "filename": file.filename,
#             "result": result
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


import os
import torch
import threading

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model import load_model
from inference import load_face_net, predict_from_bytes
from utils import download_model


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_NAME = os.getenv("MODEL_NAME", "best_model_v3.pth")
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

MODEL_URL = os.getenv(
    "MODEL_URL",
    "https://huggingface.co/farhanabid786/deepfake-efficientnet/resolve/main/best_model_v3.pth"
)

DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


model = None
face_net = None
threshold = None
lock = threading.Lock()


def get_model():
    global model, face_net, threshold

    if model is None:
        with lock:
            if model is None:
                if not os.path.exists(MODEL_PATH):
                    download_model(MODEL_PATH, MODEL_URL)

                model_loaded, threshold_loaded = load_model(MODEL_PATH, DEVICE)
                face_net_loaded = load_face_net(DETECTOR_DIR)

                model = model_loaded
                threshold = threshold_loaded
                face_net = face_net_loaded

    return model, face_net, threshold


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        model_obj, face_net_obj, threshold_val = get_model()

        result = predict_from_bytes(
            contents,
            model_obj,
            face_net_obj,
            DEVICE,
            threshold_val
        )

        return {
            "filename": file.filename,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
