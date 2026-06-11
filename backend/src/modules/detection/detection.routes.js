import express from "express";

import upload from "../../middleware/upload.middleware.js";

import {
  detectImage,
  detectVideo
} from "./detection.controller.js";

const router = express.Router();


// ================= IMAGE DETECTION =================
router.post(
  "/image",
  upload.single("file"),
  detectImage
);


// ================= VIDEO DETECTION =================
router.post(
  "/video",
  upload.single("file"),
  detectVideo
);

export default router;