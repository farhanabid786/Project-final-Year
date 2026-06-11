import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";
import { registerService } from "./auth.service.js";
import User from "./auth.model.js";


// ================= REGISTER =================
export const registerUser = async (req, res) => {
  try {
    const { name, username, email, phone, password } = req.body;

    if (!name || !username || !email || !phone || !password) {
      return res.status(400).json({
        success: false,
        message: "All fields are required"
      });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await registerService({
      name,
      username,
      email,
      phone,
      password: hashedPassword
    });

    const userResponse = {
      _id: user._id,
      name: user.name,
      username: user.username,
      email: user.email,
      phone: user.phone
    };

    res.status(201).json({
      success: true,
      message: "User created successfully",
      data: userResponse
    });

  } catch (err) {
    res.status(400).json({
      success: false,
      message: err.message
    });
  }
};


// ================= LOGIN =================
export const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: "Email and password required"
      });
    }

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({
        success: false,
        message: "User not found"
      });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({
        success: false,
        message: "Invalid credentials"
      });
    }

    const token = jwt.sign(
      { id: user._id },
      process.env.JWT_SECRET,
      { expiresIn: "1d" }
    );

    const safeUser = {
      _id: user._id,
      name: user.name,
      email: user.email
    };

    res.status(200).json({
      success: true,
      message: "Login successful",
      data: {
        token,
        user: safeUser
      }
    });

  } catch (err) {
    res.status(500).json({
      success: false,
      message: err.message
    });
  }
};


// ================= GET CURRENT USER =================
export const getMe = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select("-password");

    res.status(200).json({
      success: true,
      data: user
    });

  } catch (err) {
    res.status(500).json({
      success: false,
      message: err.message
    });
  }
};