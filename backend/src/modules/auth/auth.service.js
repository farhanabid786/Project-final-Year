import User from "./auth.model.js";

export const registerService = async (data) => {
  const { name, username, email, phone, password } = data;

  const existingUser = await User.findOne({
    $or: [{ email }, { username }]
  });

  if (existingUser) {
    throw new Error("User already exists");
  }

  const user = await User.create({
    name,
    username,
    email,
    phone,
    password
  });

  return user;
};