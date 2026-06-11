import axios from "axios";
import fs from "fs";
import FormData from "form-data";


// ================= IMAGE DETECTION =================
export const detectImageService = async (filePath) => {

  try {

    // create form-data
    const formData = new FormData();

    // append image
    formData.append(
      "file",
      fs.createReadStream(filePath)
    );

    // send image to FastAPI
    const response = await axios.post(
      "http://127.0.0.1:8001/predict",
      formData,
      {
        headers: formData.getHeaders()
      }
    );

    // return FastAPI response
    return response.data;

  } catch (err) {

    console.log(
      "Image FastAPI Error:",
      err.message
    );

    throw new Error(
      "Failed to connect with Image AI server"
    );

  }

};


// ================= VIDEO DETECTION =================
export const detectVideoService = async (filePath) => {

  try {

    // create form-data
    const formData = new FormData();

    // append video
    formData.append(
      "file",
      fs.createReadStream(filePath)
    );

    // send video to FastAPI
    const response = await axios.post(
      "http://127.0.0.1:8000/api/v1/detect/video",
      formData,
      {
        headers: formData.getHeaders()
      }
    );

    // return FastAPI response
    return response.data;

  } catch (err) {

    console.log(
      "Video FastAPI Error:",
      err.message
    );

    throw new Error(
      "Failed to connect with Video AI server"
    );

  }

};