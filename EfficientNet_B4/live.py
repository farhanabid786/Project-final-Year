import cv2
import requests
import time

API_URL = "http://127.0.0.1:8000/predict/live"

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera not detected")
    exit()

print("🎥 Starting live detection... Press ESC to exit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to capture frame")
        break

    # Encode frame to JPEG
    _, img_encoded = cv2.imencode('.jpg', frame)

    try:
        # Send frame to API
        response = requests.post(
            API_URL,
            files={"file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")}
        )

        result = response.json()

        # Extract prediction
        label = result.get("prediction", "N/A")
        confidence = result.get("confidence", 0)

        # Format text
        text = f"{label} ({confidence:.2f})"

        # Color (Green = REAL, Red = FAKE)
        color = (0, 255, 0) if label == "REAL" else (0, 0, 255)

    except Exception as e:
        text = "API ERROR"
        color = (0, 0, 255)

    # Display result on frame
    cv2.putText(
        frame,
        text,
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        2,
        cv2.LINE_AA
    )

    # Show window
    cv2.imshow("Deepfake Live Detection", frame)

    # Exit on ESC
    if cv2.waitKey(1) == 27:
        break

    # Optional: slight delay to reduce API load
    time.sleep(0.1)

cap.release()
cv2.destroyAllWindows()