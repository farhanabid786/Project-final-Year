import {
  detectImageService,
  detectVideoService
} from "./detection.service.js";


// ================= IMAGE DETECTION =================
export const detectImage = async (req, res) => {

  try {

    // check file
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No file uploaded"
      });
    }

    // send image to FastAPI
    const result = await detectImageService(
      req.file.path
    );

    // return response
    res.status(200).json({
      success: true,
      result
    });

  } catch (err) {

    res.status(500).json({
      success: false,
      message: err.message
    });

  }

};


// ================= VIDEO DETECTION =================
export const detectVideo = async (req, res) => {

  try {

    // check file
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No video uploaded"
      });
    }

    // send video to FastAPI
    const result = await detectVideoService(
      req.file.path
    );

    // return response
    res.status(200).json({
      success: true,
      result
    });

  } catch (err) {

    res.status(500).json({
      success: false,
      message: err.message
    });

  }

};