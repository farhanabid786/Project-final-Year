import express from "express";
import cors from "cors";
import passport from "passport";
import "./config/passport.js";

import authRoutes from "./modules/auth/auth.routes.js";
import detectionRoutes from "./modules/detection/detection.routes.js";

const app = express();

// middleware
app.use(express.json());

app.use(passport.initialize());
app.use(cors({
  origin: "http://localhost:5173",
  credentials: true
}));

// routes
app.use("/api/auth", authRoutes);
app.use("/api/detect", detectionRoutes);

// test route
app.get("/", (req, res) => {
  res.send("API working");
});

export default app;