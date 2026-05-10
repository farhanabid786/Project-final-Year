import React, { useEffect } from 'react'
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Navbar = () => {
  const navigate = useNavigate();
  const { isLoggedIn, logout } = useAuth();

  const handleGetStarted = () => {
    if (isLoggedIn) {
      navigate('/detection');
    } else {
      navigate('/register');
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className='flex justify-center mt-2 w-full'>
      <nav className='relative flex justify-between items-center w-full max-w-6xl px-8 py-4 rounded-full border border-orange-400/40 bg-white/5 backdrop-blur-2xl text-white shadow-[0_0_15px_rgba(255,140,0,0.25)] transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_25px_rgba(255,140,0,0.45)]'>

        {/* Glow */}
        <div className="absolute inset-0 rounded-full border border-orange-400/20 blur-md opacity-60 pointer-events-none -z-10"></div>

        {/* Left Spacer */}
        <div className="w-[120px]"></div>

        {/* Links */}
        <div className="flex gap-2 sm:gap-6">

          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-5 py-2 rounded-full transition-all duration-300 ${
                isActive
                  ? "bg-white/10 text-orange-400"
                  : "text-white hover:text-orange-400 hover:bg-white/10 hover:shadow-[0_0_10px_rgba(255,140,0,0.3)]"
              }`
            }
          >
            Home
          </NavLink>

          <NavLink
            to="/about"
            className={({ isActive }) =>
              `px-5 py-2 rounded-full transition-all duration-300 ${
                isActive
                  ? "bg-white/10 text-orange-400"
                  : "text-white hover:text-orange-400 hover:bg-white/10 hover:shadow-[0_0_10px_rgba(255,140,0,0.3)]"
              }`
            }
          >
            About
          </NavLink>

          {!isLoggedIn ? (
            <NavLink
              to="/login"
              className={({ isActive }) =>
                `px-5 py-2 rounded-full transition-all duration-300 ${
                  isActive
                    ? "bg-white/10 text-orange-400"
                    : "text-white hover:text-orange-400 hover:bg-white/10 hover:shadow-[0_0_10px_rgba(255,140,0,0.3)]"
                }`
              }
            >
              Login
            </NavLink>
          ) : (
            <button
              onClick={handleLogout}
              className="px-5 py-2 rounded-full transition-all duration-300 text-white hover:text-orange-400 hover:bg-white/10 hover:shadow-[0_0_10px_rgba(255,140,0,0.3)]"
            >
              Logout
            </button>
          )}

        </div>

        {/* Right */}
        <div className="flex items-center gap-3 flex-shrink-0">

          <button 
            onClick={handleGetStarted}
            className="px-6 py-2 mr-2 bg-orange-500 hover:bg-orange-600 text-black text-[10px] font-black uppercase tracking-widest rounded-full transition-all duration-300 shadow-[0_0_15px_rgba(255,111,55,0.4)] active:scale-95"
          >
            Get Started
          </button>

          <div className="w-10 h-10 rounded-full bg-white/10 border border-white/20 hover:scale-105 transition duration-300 cursor-pointer group relative">
            <div className="absolute inset-0 border border-orange-400 rounded-full animate-ping opacity-20 group-hover:opacity-40" />
          </div>

        </div>

      </nav>
    </div>
  )
}

export default Navbar;