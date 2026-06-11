import jwt from "jsonwebtoken";

export const protect = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    // 1. check header exists
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        success: false,
        message: "No token provided"
      });
    }

    // 2. extract token
    const token = authHeader.split(" ")[1];

    // 3. verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // 4. attach user to request
    req.user = decoded;

    next();

  } catch (err) {
    res.status(401).json({
      success: false,
      message: "Invalid token"
    });
  }
};