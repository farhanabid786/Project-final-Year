import express from "express";
import passport from "passport";
import jwt from "jsonwebtoken";

import {
  registerUser,
  loginUser,
  getMe
} from "./auth.controller.js";

import { protect } from "../../middleware/auth.middleware.js";

const router = express.Router();


// ================= PUBLIC ROUTES =================

// Manual register
router.post("/register", registerUser);

// Manual login
router.post("/login", loginUser);


// ================= GOOGLE AUTH =================

// Redirect user to Google
router.get(
  "/google",
  passport.authenticate("google", {
    scope: ["profile", "email"]
  })
);


// Google callback
router.get(
  "/google/callback",

  passport.authenticate("google", {
    session: false,
    failureRedirect: "http://localhost:5173/login"
  }),

  async (req, res) => {
    try {

      // Generate JWT
      const token = jwt.sign(
        { id: req.user._id },
        process.env.JWT_SECRET,
        { expiresIn: "1d" }
      );

      // Redirect frontend with token
      res.redirect(
        `http://localhost:5173/auth-success?token=${token}`
      );

    } catch (error) {

      res.redirect("http://localhost:5173/login");

    }
  }
);


// ================= PROTECTED ROUTES =================

router.get("/me", protect, getMe);


export default router;