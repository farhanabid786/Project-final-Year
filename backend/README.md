# 🛡️ Deepfake Detection System — Backend

AI-powered backend for detecting manipulated media (Images, Videos, and Live Camera Feed).

This backend acts as a bridge between the frontend application and the AI inference server.

---

# 🚀 Architecture

Frontend (React)
↓
Express Backend (REST API)
↓
FastAPI AI Server
↓
Deepfake Detection Model

---

# 📌 Features

✅ User Authentication (Register / Login)

✅ JWT Authentication

✅ Image Deepfake Detection

✅ Video Deepfake Detection

✅ Live Detection (Realtime)

✅ Express ↔ FastAPI Communication

✅ File Upload Support

✅ CORS Enabled

✅ Modular Backend Structure

---

# 🏗️ Backend Tech Stack

## Core Backend

- Node.js
- Express.js

## Authentication

- JWT (jsonwebtoken)

## Upload Handling

- Multer

## API Communication

- Axios

## Middleware

- CORS

## Environment Variables

- dotenv

---

# 📂 Folder Structure

backend/

src/

modules/

auth/

auth.routes.js

auth.controller.js

auth.service.js

detection/

detection.routes.js

detection.controller.js

detection.service.js

middleware/

upload.middleware.js

uploads/

server.js

app.js

.env

README.md

---

# 🔥 Installation

Clone repository:

```bash
git clone <repo-url>
```

Move into backend:

```bash
cd backend
```

Install dependencies:

```bash
npm install
```

Start backend:

```bash
npm run dev
```

Backend runs:

```text
http://localhost:5000
```

---

# ⚙️ Environment Variables

Create:

```env
.env
```

Example:

```env
PORT=5000

JWT_SECRET=your_secret

FASTAPI_URL=http://127.0.0.1:8001
```

---

# 🔐 Authentication Flow

Register:

```text
Frontend
↓
POST /api/auth/register
↓
Validate User
↓
Hash Password
↓
Generate JWT
↓
Send Token
```

Login:

```text
Frontend
↓
POST /api/auth/login
↓
Verify Credentials
↓
Generate JWT
↓
Authenticated User
```

---

# 🖼️ Image Detection Flow

Frontend Upload
↓

Express Route
↓

Multer Upload
↓

Controller
↓

Service
↓

Axios
↓

FastAPI
↓

AI Model
↓

Frontend Result

---

# 🎥 Video Detection Flow

Frontend Upload
↓

Express Upload
↓

Multer
↓

Controller
↓

Axios
↓

FastAPI Video Endpoint
↓

AI Prediction
↓

Frontend

---

# 🔴 Live Detection Flow

React Webcam
↓

Capture Frame
↓

Convert → Base64
↓

FastAPI
↓

Realtime AI
↓

Frontend HUD

---

# 📤 API Endpoints

---

## Authentication

### Register

POST

```http
/api/auth/register
```

Body:

```json
{
  "name":"John",
  "email":"john@example.com",
  "password":"123456"
}
```

---

### Login

POST

```http
/api/auth/login
```

Body:

```json
{
  "email":"john@example.com",
  "password":"123456"
}
```

---

## Detection

### Image Detection

POST

```http
/api/detect/image
```

Body:

```text
multipart/form-data
file
```

---

### Video Detection

POST

```http
/api/detect/video
```

Body:

```text
multipart/form-data
file
```

---

# 📦 Upload Storage

Uploaded files are temporarily stored inside:

```text
src/uploads/
```

Purpose:

- Upload buffering
- FastAPI forwarding

---

# 🧠 AI Integration

Backend does NOT run AI.

Backend responsibilities:

- Receive requests
- Upload handling
- Validation
- Forwarding to FastAPI
- Returning predictions

FastAPI responsibilities:

- AI inference
- Model execution
- Prediction generation

---

# 🚀 Run Backend

Development:

```bash
npm run dev
```

Production:

```bash
npm start
```

---

# 🧪 API Testing

Use:

- Postman
- Swagger (FastAPI)

---

# 🔒 Security

- JWT Authentication
- Password Hashing
- File Validation
- CORS Protection

---

# 👨‍💻 Author

Utsav Kashyap

Deepfake Detection Project