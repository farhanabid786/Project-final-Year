import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const AuthSuccess = () => {

  const navigate = useNavigate();

  const { login } = useAuth();

  useEffect(() => {

    // Get token from URL
    const params = new URLSearchParams(
      window.location.search
    );

    const token = params.get("token");

    // If token exists
    if (token) {

      // Save token using AuthContext
      login(token);

      // Wait for auth state update
      setTimeout(() => {

        navigate("/");

      }, 100);

    } else {

      // If token missing
      navigate("/login");

    }

  }, []);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center text-white">
      Authenticating...
    </div>
  );
};

export default AuthSuccess;