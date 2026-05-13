import React, { useState, useRef, useEffect } from 'react';
import CyberLayout from '../components/CyberLayout';

const LiveDetection = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedFrames, setCapturedFrames] = useState([]);

  // NEW STATES
  const [prediction, setPrediction] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [faceBoxes, setFaceBoxes] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // prevents multiple simultaneous requests
  const sendingRef = useRef(false);

  // START CAMERA
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 1280,
          height: 720,
          facingMode: "user"
        }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
      }
    } catch (err) {
      console.error("Camera Access Denied:", err);
      alert("Please allow camera access to use Live Detection.");
    }
  };

  // STOP CAMERA
  const stopCamera = () => {
    const stream = videoRef.current?.srcObject;
    const tracks = stream?.getTracks();
    tracks?.forEach(track => track.stop());
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setPrediction(null);
    setConfidence(null);
    setFaceBoxes([]);
    setError(null);
  };

  // REAL LIVE DETECTION
  const captureFrame = async () => {
    if (
      !videoRef.current ||
      !canvasRef.current ||
      sendingRef.current
    ) return;

    try {
      sendingRef.current = true;
      const context = canvasRef.current.getContext('2d');

      // optimized canvas size
      canvasRef.current.width = 320;
      canvasRef.current.height = 240;

      context.drawImage(
        videoRef.current,
        0,
        0,
        320,
        240
      );

      const frameData =
        canvasRef.current.toDataURL('image/jpeg');

      setCapturedFrames(prev => [
        ...prev.slice(-9),
        frameData
      ]);

      setIsAnalyzing(true);

      // FASTAPI REQUEST
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/detect/live",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            frame_b64: frameData,
            session_id: "live-session"
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Live detection failed"
        );
      }

      // REAL AI RESULT
      setPrediction(data.label);
      setConfidence(data.confidence_display);
      setFaceBoxes(data.face_boxes || []);
      setError(null);

    } catch (err) {
      console.log(err);
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
      sendingRef.current = false;
    }
  };

  // LIVE INTERVAL
  useEffect(() => {
    let interval;
    if (isStreaming) {
      interval = setInterval(() => {
        captureFrame();
      }, 1000);
    }
    return () => {
      clearInterval(interval);
    };
  }, [isStreaming]);

  return (
    <CyberLayout>
      {/* Custom Styles for AI Visualization */}
      <style>{`
        @keyframes sonar {
          0% { transform: scale(0.9); opacity: 1; }
          100% { transform: scale(1.4); opacity: 0; }
        }
        .animate-sonar { animation: sonar 2s cubic-bezier(0, 0, 0.2, 1) infinite; }
        .face-box-transition { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
      `}</style>

      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-16 animate-fade-in-down">

        {/* Header */}
        <div className="text-center mb-10 group">
          <h2 className="text-3xl md:text-5xl font-black uppercase tracking-tighter text-white transition-all duration-500 group-hover:tracking-normal">
            Live{" "}
            <span className="text-[#FF6F37] drop-shadow-[0_0_10px_rgba(255,111,55,0.5)]">
              Neural
            </span>{" "}
            Feed
          </h2>

          <div className="flex items-center justify-center gap-2 mt-2">
            <span
              className={`w-2 h-2 rounded-full transition-colors duration-500 ${isStreaming
                ? 'bg-green-500 animate-ping'
                : 'bg-red-500'
                }`}
            />
            <p className="text-gray-400 text-xs uppercase tracking-[0.3em] font-mono opacity-70">
              {isStreaming
                ? 'Stream Active'
                : 'Sensor Offline'}
            </p>
          </div>
        </div>

        {/* Camera Viewport */}
        <div className="w-full max-w-4xl bg-black border border-white/10 rounded-2xl overflow-hidden relative shadow-2xl transition-all duration-700 hover:border-white/20 transform-gpu">

          {/* Decorative Corners */}
          <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-[#FF6F37] z-20 animate-pulse" />
          <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-[#FF6F37] z-20 animate-pulse delay-75" />
          <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-[#FF6F37] z-20 animate-pulse delay-150" />
          <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-[#FF6F37] z-20 animate-pulse delay-300" />

          {/* VIDEO */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className={`w-full aspect-video object-cover transform-gpu transition-all duration-1000 ${!isStreaming
              ? 'hidden opacity-0 scale-105'
              : 'block opacity-100 scale-100 animate-smooth-entry'
              }`}
          />

          {/* Camera OFF */}
          {!isStreaming && (
            <div className="w-full aspect-video flex flex-col items-center justify-center bg-zinc-900/50 backdrop-blur-sm">
              <div className="w-20 h-20 border border-white/10 rounded-full flex items-center justify-center mb-6 relative group">
                <svg
                  className="w-10 h-10 text-gray-600 transition-colors group-hover:text-[#FF6F37]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeWidth="1"
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <div className="absolute inset-0 border border-[#FF6F37]/30 rounded-full animate-ping pointer-events-none" />
              </div>
              <button
                onClick={startCamera}
                className="px-8 py-3 bg-[#FF6F37] text-black font-black uppercase text-xs tracking-widest transition-all duration-300 hover:scale-105 hover:bg-[#e86330] shadow-[0_0_20px_rgba(255,111,55,0.3)] active:scale-95"
              >
                Initialize Camera
              </button>
            </div>
          )}

          {/* STREAM HUD */}
          {isStreaming && (
            <>
              <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-10 bg-[radial-gradient(circle_at_center,transparent_0%,black_90%)] opacity-40" />

              {/* ENHANCED FACE TRACKING OVERLAY */}
              {faceBoxes.map((box, index) => {
                const isFake = prediction === "FAKE";
                const themeColor = isFake ? "#ef4444" : "#22c55e"; // Red-500 : Green-500
                
                return (
                  <div
                    key={index}
                    className="absolute face-box-transition z-40"
                    style={{
                      left: `${(box.x / 320) * 100}%`,
                      top: `${(box.y / 240) * 100}%`,
                      width: `${(box.w / 320) * 100}%`,
                      height: `${(box.h / 240) * 100}%`,
                      border: `2px solid ${themeColor}`,
                      boxShadow: `0 0 20px ${themeColor}66, inset 0 0 15px ${themeColor}33`
                    }}
                  >
                    {/* Scanning Sonar Effect */}
                    <div 
                      className="absolute inset-0 animate-sonar rounded-sm pointer-events-none"
                      style={{ border: `1px solid ${themeColor}` }}
                    />
                    
                    {/* Dynamic AI Label */}
                    <div 
                      className="absolute -top-7 left-[-2px] px-3 py-1 flex items-center gap-2 clip-path-polygon"
                      style={{ backgroundColor: themeColor }}
                    >
                      <div className="w-1.5 h-1.5 bg-black rounded-full animate-pulse" />
                      <span className="text-black text-[10px] font-black tracking-tighter uppercase">
                        {prediction || "SCANNING"} // {confidence || "0"}%
                      </span>
                    </div>

                    {/* Glowing Corners */}
                    <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2" style={{ borderColor: themeColor }} />
                    <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2" style={{ borderColor: themeColor }} />
                    <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2" style={{ borderColor: themeColor }} />
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2" style={{ borderColor: themeColor }} />
                  </div>
                );
              })}

              {/* SCAN LINE */}
              <div className="absolute top-0 left-0 w-full h-[2px] bg-[#FF6F37] shadow-[0_0_25px_#FF6F37] animate-scan z-30 opacity-50" />

              {/* HUD PANEL */}
              <div className="absolute bottom-6 right-6 text-[#FF6F37] font-mono text-[10px] z-30 space-y-1 bg-black/60 backdrop-blur-md p-3 border-r-2 border-[#FF6F37] animate-slide-up">
                <p className="flex justify-between gap-4">
                  <span className="opacity-50">REC:</span>
                  <span className="animate-pulse">00:00:24:12</span>
                </p>
                <p className="flex justify-between gap-4">
                  <span className="opacity-50">FPS:</span>
                  30.00
                </p>
                <p className="flex justify-between gap-4">
                  <span className="opacity-50">ISO:</span>
                  400
                </p>
                <p className="flex justify-between gap-4 border-t border-[#FF6F37]/20 mt-1 pt-1">
                  <span className="opacity-50">AI:</span>
                  <span
                    className={
                      prediction === "FAKE"
                        ? "text-red-400 font-bold"
                        : "text-green-400 font-bold"
                    }
                  >
                    {prediction || "SEARCHING"}
                  </span>
                </p>
                <p className="flex justify-between gap-4">
                  <span className="opacity-50">CONF:</span>
                  <span className="text-white">
                    {confidence ? `${confidence}%` : "--"}
                  </span>
                </p>
              </div>
            </>
          )}
        </div>

        {/* Hidden Canvas */}
        <canvas ref={canvasRef} className="hidden" />

        {/* ERROR */}
        {error && (
          <div className="mt-6 bg-red-500/10 border border-red-500/30 px-6 py-3 rounded-xl animate-fade-in">
            <p className="text-red-400 text-xs uppercase tracking-widest font-mono">
              SYSTEM ERROR: {error}
            </p>
          </div>
        )}

        {/* CONTROLS */}
        {isStreaming && (
          <div className="mt-10 flex flex-col sm:flex-row gap-6 animate-slide-up">
            <button
              onClick={stopCamera}
              className="px-8 py-2.5 border border-red-500/50 text-red-500 text-[10px] font-bold uppercase tracking-widest hover:bg-red-500 hover:text-black transition-all duration-300 transform active:scale-95"
            >
              Terminate Feed
            </button>

            <button
              className="px-8 py-2.5 bg-[#FF6F37]/10 border border-[#FF6F37] text-[#FF6F37] text-[10px] font-bold uppercase tracking-widest relative overflow-hidden group shadow-[0_0_15px_rgba(255,111,55,0.1)] hover:shadow-[0_0_25px_rgba(255,111,55,0.3)] transition-all duration-500"
            >
              <span className="relative z-10 animate-pulse">
                {isAnalyzing
                  ? "Analyzing Neural Tensors..."
                  : prediction
                    ? `Neural Match: ${prediction}`
                    : "Scanning Biometrics..."}
              </span>
              <div className="absolute inset-0 bg-[#FF6F37]/10 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-700" />
            </button>
          </div>
        )}
      </div>
    </CyberLayout>
  );
};

export default LiveDetection;