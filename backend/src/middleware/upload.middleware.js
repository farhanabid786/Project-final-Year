import multer from "multer";
import path from "path";

// storage config
const storage = multer.diskStorage({

  destination: (req, file, cb) => {
    cb(null, "src/uploads");
  },

  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  }

});

// file filter
const fileFilter = (req, file, cb) => {

  // allowed image + video formats
  const allowedTypes =
    /jpeg|jpg|png|mp4|mov|avi|webm/;

  const extname = allowedTypes.test(
    path.extname(file.originalname).toLowerCase()
  );

  const mimetype = allowedTypes.test(
    file.mimetype
  );

  if (extname && mimetype) {

    cb(null, true);

  } else {

    cb(
      new Error(
        "Only images and video files are allowed"
      )
    );

  }

};

// multer instance
const upload = multer({
  storage,
  fileFilter
});

export default upload;