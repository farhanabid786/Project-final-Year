import mongoose from "mongoose";

const userSchema = new mongoose.Schema(
  {
    // Common fields
    name: {
      type: String,
      required: true
    },

    email: {
      type: String,
      required: true,
      unique: true
    },

    username: {
      type: String,
      unique: true,
      sparse: true
    },

    provider: {
      type: String,
      enum: ["local", "google"],
      default: "local"
    },

    // Local auth fields
    phone: {
      type: String
    },

    password: {
      type: String
    },

    // Google auth fields
    googleId: {
      type: String
    },

    avatar: {
      type: String
    }
  },
  { timestamps: true }
);

export default mongoose.model("User", userSchema);