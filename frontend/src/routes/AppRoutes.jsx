import React from 'react';
import { Routes, Route } from 'react-router-dom';

import Home from '../pages/Home';
import Login from '../pages/Login';
import Register from '../pages/Register';
import About from '../pages/About';

import Detection from '../pages/Detection';
import ImageDetection from '../pages/ImageDetection';
import VideoDetection from '../pages/VideoDetection';
import LiveDetection from '../pages/LiveDetection';

import AuthSuccess from '../pages/AuthSuccess';

import CyberLayout from '../components/CyberLayout';
import ProtectedRoute from '../components/ProtectedRoute';

const AppRoutes = () => {
  return (
    <Routes>

      {/* Public Routes */}
      <Route path="/" element={<Home />} />

      <Route
        path="/login"
        element={
          <CyberLayout>
            <Login />
          </CyberLayout>
        }
      />

      <Route
        path="/register"
        element={
          <CyberLayout>
            <Register />
          </CyberLayout>
        }
      />

      {/* Google Auth Success Route */}
      <Route
        path="/auth-success"
        element={<AuthSuccess />}
      />

      <Route
        path="/about"
        element={
          <CyberLayout>
            <About />
          </CyberLayout>
        }
      />


      {/* 🔒 Protected Routes */}

      <Route
        path="/detection"
        element={
          <ProtectedRoute>
            <CyberLayout>
              <Detection />
            </CyberLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/detection/image"
        element={
          <ProtectedRoute>
            <CyberLayout>
              <ImageDetection />
            </CyberLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/detection/video"
        element={
          <ProtectedRoute>
            <CyberLayout>
              <VideoDetection />
            </CyberLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/detection/live"
        element={
          <ProtectedRoute>
            <CyberLayout>
              <LiveDetection />
            </CyberLayout>
          </ProtectedRoute>
        }
      />

    </Routes>
  );
};

export default AppRoutes;