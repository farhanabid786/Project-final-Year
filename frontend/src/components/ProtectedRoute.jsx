import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { isLoggedIn } = useAuth();

  // ❌ not logged in → redirect
  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  // ✅ logged in → allow access
  return children;
};

export default ProtectedRoute;