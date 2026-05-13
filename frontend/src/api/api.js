export const BASE_URL = "http://localhost:5000/api";

//  helper to get token
export const getAuthHeaders = () => {
  const token = localStorage.getItem("token");

  return {
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : ""
  };
};