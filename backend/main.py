import streamlit as st
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import efficientnet_b4
from PIL import Image

# ---------- CONFIG ----------
MODEL_PATH = "best_model.pth"
IMAGE_SIZE = 384
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    model = efficientnet_b4(pretrained=False)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 1)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model

model = load_model()

# ---------- TRANSFORM ----------
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],
                         [0.229,0.224,0.225])
])

# ---------- UI ----------
st.title("Deepfake Image Detection System")
st.write("Upload any image to check whether it is REAL or FAKE")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.image(image, caption="Uploaded Image", use_column_width=True)

    img_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = model(img_tensor)
        prob = torch.sigmoid(output).item()

    st.write("### Prediction Results")

    if prob > 0.5:
        st.success(f"REAL Image (Confidence: {prob*100:.2f}%)")
    else:
        st.error(f"FAKE Image (Confidence: {(1-prob)*100:.2f}%)")

    st.write(f"Raw Real Probability: {prob:.6f}")