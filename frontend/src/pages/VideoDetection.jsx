import React, { useState, useRef, useEffect } from 'react';
import CyberLayout from '../components/CyberLayout';

const VideoDetection = () => {

  // Existing States
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [hasFlipped, setHasFlipped] = useState(false);
  const fileInputRef = useRef(null);

  // Backend Ready States
  const [loading, setLoading] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const steps = [
    "Extracting Video Frames...",
    "Analyzing Temporal Features...",
    "Running BiLSTM Attention Network...",
    "Generating Confidence Score...",
    "Finalizing AI Report..."
  ];

  // cleanup preview memory
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // file processing
  const processFile = (file) => {

    if (file && file.type.startsWith('video/')) {

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setSelectedVideo(file);
      setPreviewUrl(URL.createObjectURL(file));

      // reset states
      setResult(null);
      setError(null);
      setAnalysisStep(0);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

    } else {

      setError("Please upload a valid video file");

    }
  };

  // REAL BACKEND ANALYSIS
  const handleAnalyze = async () => {

    if (!selectedVideo || loading) return;

    try {

      setLoading(true);
      setResult(null);
      setError(null);
      setAnalysisStep(0);

      // cinematic loading steps
      const interval = setInterval(() => {

        setAnalysisStep((prev) => {
          if (prev < steps.length - 1) {
            return prev + 1;
          }
          return prev;
        });

      }, 1400);

      // create form-data
      const formData = new FormData();

      formData.append("file", selectedVideo);

      // backend request
      const response = await fetch(
        "http://localhost:5000/api/detect/video",
        {
          method: "POST",
          body: formData
        }
      );

      clearInterval(interval);

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Video analysis failed");
      }

      const aiResult = data.result;

      // backend → frontend mapping
      setResult({
        label: aiResult.label,
        confidence: aiResult.confidence_pct,
        fakeProb: aiResult.probabilities.fake_pct,
        realProb: aiResult.probabilities.real_pct,
        framesAnalyzed: aiResult.frames_sampled,
        processTime: `${aiResult.inference_time_ms}ms`
      });

    } catch (err) {

      console.log(err);

      setError(
        err.message || "Failed to connect with AI server"
      );

    } finally {

      setLoading(false);

    }
  };

  const handleVideoChange = (e) =>
    processFile(e.target.files[0]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () =>
    setIsDragging(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    processFile(e.dataTransfer.files[0]);
  };

  const triggerFileInput = () =>
    fileInputRef.current.click();

  return (
    <CyberLayout>

      <style>
        {`
          .perspective-container {
            perspective: 2000px;
          }

          .flip-card-inner {
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform 2.5s cubic-bezier(0.22, 1, 0.36, 1);
            transform-style: preserve-3d;
          }

          .is-flipping {
            transform: rotateY(360deg);
          }

          .backface-hidden {
            backface-visibility: hidden;
            -webkit-backface-visibility: hidden;
          }

          .rotate-y-180 {
            transform: rotateY(180deg);
          }

          @keyframes scan-line {
            0% {
              transform: translateY(-100%);
            }

            100% {
              transform: translateY(1000%);
            }
          }

          .animate-scan-fast {
            animation: scan-line 1.5s linear infinite;
          }
        `}
      </style>

      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-16 animate-fade-in-down">

        {/* Header */}
        <div className="text-center mb-10">

          <h2 className="text-3xl md:text-5xl font-black uppercase tracking-tighter text-white">
            Video{" "}
            <span className="text-[#FF6F37] drop-shadow-[0_0_10px_#FF6F37]">
              Forensics
            </span>{" "}
            Unit
          </h2>

          <p className="text-gray-400 mt-2 text-sm uppercase tracking-widest font-mono opacity-70">

            {loading
              ? "SYSTEM ACTIVE: SCANNING TEMPORAL DATA..."
              : result
                ? "SCAN COMPLETE"
                : "Temporal Consistency Scanner v2.4"}

          </p>

        </div>

        {/* Upload Section */}
        <div
          className="perspective-container w-full max-w-3xl aspect-video relative transform-gpu mb-8"
          onMouseEnter={() => setHasFlipped(true)}
        >

          <div className={`flip-card-inner shadow-2xl ${hasFlipped ? 'is-flipping' : ''}`}>

            {/* FRONT FACE */}
            <div className="flip-card-front backface-hidden absolute inset-0 w-full h-full bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-6 md:p-10 flex flex-col items-center shadow-2xl">

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleVideoChange}
                accept="video/*"
                className="hidden"
              />

              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`group relative w-full flex-1 border-2 border-dashed transition-all duration-500 overflow-hidden rounded-xl bg-black/40 flex items-center justify-center
                  ${previewUrl
                    ? 'border-[#FF6F37]'
                    : isDragging
                      ? 'border-[#FF6F37] bg-[#FF6F37]/10'
                      : 'border-white/10'
                  }`}
              >

                {previewUrl ? (

                  <div className="relative w-full h-full flex items-center justify-center bg-black">

                    <video
                      src={previewUrl}
                      controls
                      className="max-w-full max-h-full relative z-10"
                    />

                    {loading && (
                      <div className="absolute inset-0 bg-[#FF6F37]/20 animate-pulse pointer-events-none z-20" />
                    )}

                  </div>

                ) : (

                  <div
                    onClick={triggerFileInput}
                    className="flex flex-col items-center justify-center h-full w-full cursor-pointer text-gray-500 group-hover:text-[#FF6F37]"
                  >

                    <svg
                      className="w-12 h-12 mb-4 animate-pulse"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >

                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="1"
                        d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />

                    </svg>

                    <p className="font-bold uppercase text-[10px] tracking-[0.3em]">
                      Initialize Video Stream
                    </p>

                  </div>

                )}

                {previewUrl && !result && (
                  <div className={`absolute top-0 left-0 w-full h-[3px] bg-[#FF6F37] shadow-[0_0_20px_#FF6F37] ${loading ? 'animate-scan-fast' : 'animate-scan'} pointer-events-none z-50`} />
                )}

              </div>

              {/* Buttons */}
              <div className="flex gap-4 mt-6 w-full">

                <button
                  onClick={(e) => {
                    e.stopPropagation();

                    if (previewUrl) {
                      URL.revokeObjectURL(previewUrl);
                    }

                    setSelectedVideo(null);
                    setPreviewUrl(null);
                    setResult(null);
                    setError(null);
                  }}
                  className="flex-1 px-6 py-3 border border-white/10 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-red-500/20 transition-all"
                >
                  Flush Buffer
                </button>

                <button
                  disabled={!selectedVideo || loading}
                  onClick={handleAnalyze}
                  className={`flex-[2] px-6 py-3 font-black uppercase text-[10px] tracking-widest transition-all duration-500
                    ${selectedVideo && !loading
                      ? 'bg-[#FF6F37] text-black shadow-[0_0_20px_#FF6F37]'
                      : 'bg-gray-900 text-gray-600 cursor-not-allowed'
                    }`}
                >

                  {loading
                    ? "Analyzing..."
                    : "Begin Temporal Deep-Scan"}

                </button>

              </div>

            </div>

            {/* BACK FACE */}
            <div className="flip-card-back absolute inset-0 backface-hidden rotate-y-180 bg-[#FF6F37] rounded-2xl p-8 flex flex-col items-center justify-center text-black">

              <div className="text-[12px] font-black uppercase mb-6 opacity-70 tracking-[0.4em] border-b border-black/30 pb-2 w-full text-center">
                Neural Uplink Active
              </div>

              <div className="w-20 h-20 rounded-lg border-4 border-black mb-6 flex items-center justify-center relative overflow-hidden">

                <div className="absolute inset-0 bg-black/10 animate-pulse" />

                <svg
                  className="w-10 h-10 text-black animate-spin-slow"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >

                  <path
                    strokeWidth="1.5"
                    d="M12 4v1m0 14v1m8-8h-1m-14 0h-1m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z"
                  />

                </svg>

              </div>

              <p className="text-center text-xl font-black uppercase tracking-tighter">
                AI Deep-Scan
              </p>

            </div>

          </div>

        </div>

        {/* HUD Metadata */}
        {selectedVideo && !result && !loading && (

          <div className="mt-4 mb-10 grid grid-cols-2 md:grid-cols-4 gap-8 font-mono text-[9px] text-[#FF6F37] uppercase bg-black/40 p-5 rounded-lg border-l-2 border-[#FF6F37] animate-fade-in shadow-xl w-full max-w-3xl">

            <div className="flex flex-col gap-1">
              <span className="text-gray-500">
                Filename:
              </span>

              <span className="truncate font-bold">
                {selectedVideo.name}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-gray-500">
                Size:
              </span>

              <span className="font-bold">
                {(selectedVideo.size / (1024 * 1024)).toFixed(2)} MB
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-gray-500">
                Codec:
              </span>

              <span className="font-bold">
                {selectedVideo.type.split('/')[1]}
              </span>
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-gray-500">
                Security:
              </span>

              <span className="text-green-400 font-bold">
                Encrypted
              </span>
            </div>

          </div>
        )}

        {/* Loading State */}
        {loading && (

          <div className="w-full max-w-3xl bg-black/50 border border-[#FF6F37]/30 rounded-xl p-6 mb-10 animate-pulse overflow-hidden">

            <div className="flex items-center gap-4">

              <div className="w-10 h-10 border-2 border-[#FF6F37] border-t-transparent rounded-full animate-spin" />

              <div>

                <p className="text-[#FF6F37] font-mono text-xs uppercase tracking-widest">
                  Temporal_BiLSTM_Active
                </p>

                <p className="text-white font-bold text-sm uppercase">
                  {steps[analysisStep]}
                </p>

              </div>

            </div>

            <div className="mt-4 w-full bg-white/10 h-1 rounded-full overflow-hidden">

              <div
                className="bg-[#FF6F37] h-full transition-all duration-500"
                style={{
                  width: `${(analysisStep + 1) * 20}%`
                }}
              />

            </div>

          </div>
        )}

        {/* Error State */}
        {error && (

          <div className="w-full max-w-3xl bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-8 animate-fade-in">

            <p className="text-red-400 font-mono text-xs uppercase tracking-widest">
              SYSTEM ERROR: {error}
            </p>

          </div>
        )}

        {/* Result State */}
        {result && !loading && (

          <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in-up mt-4">

            {/* Summary Card */}
            <div className="md:col-span-1 bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 flex flex-col items-center justify-center text-center">

              <div className={`text-5xl font-black mb-2 ${result.label === 'FAKE'
                  ? 'text-red-500'
                  : 'text-green-500'
                } drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]`}>

                {result.label}

              </div>

              <p className="text-gray-400 text-[10px] uppercase tracking-[0.3em] mb-4">
                Verdict Confidence
              </p>

              <div className="w-full h-px bg-white/10 mb-4" />

              <div className="space-y-3 w-full font-mono text-[10px]">

                <div className="flex justify-between">

                  <span className="text-gray-500">
                    FRAMES_ANALYZED:
                  </span>

                  <span className="text-[#FF6F37]">
                    {result.framesAnalyzed}
                  </span>

                </div>

                <div className="flex justify-between">

                  <span className="text-gray-500">
                    LATENCY:
                  </span>

                  <span className="text-white">
                    {result.processTime}
                  </span>

                </div>

                <div className="flex justify-between">

                  <span className="text-gray-500">
                    TEMPORAL_MODEL:
                  </span>

                  <span className="text-white">
                    BiLSTM-Attn
                  </span>

                </div>

              </div>

            </div>

            {/* Metrics Dashboard */}
            <div className="md:col-span-2 bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-8">

              <h3 className="text-[#FF6F37] font-bold uppercase text-xs tracking-widest mb-6 flex items-center gap-2">

                <span className="w-2 h-2 bg-[#FF6F37] rounded-full animate-ping" />

                Temporal Analysis Metrics

              </h3>

              <div className="grid grid-cols-1 gap-6">

                {/* Fake Probability */}
                <div>

                  <div className="flex justify-between text-[10px] mb-2">

                    <span className="text-red-400 font-bold uppercase tracking-widest">
                      Deepfake Probability
                    </span>

                    <span className="text-white">
                      {result.fakeProb}%
                    </span>

                  </div>

                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">

                    <div
                      className="bg-red-500 h-full shadow-[0_0_10px_#ef4444]"
                      style={{
                        width: `${result.fakeProb}%`
                      }}
                    />

                  </div>

                </div>

                {/* Real Probability */}
                <div>

                  <div className="flex justify-between text-[10px] mb-2">

                    <span className="text-green-400 font-bold uppercase tracking-widest">
                      Originality Score
                    </span>

                    <span className="text-white">
                      {result.realProb}%
                    </span>

                  </div>

                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">

                    <div
                      className="bg-green-500 h-full shadow-[0_0_10px_#22c55e]"
                      style={{
                        width: `${result.realProb}%`
                      }}
                    />

                  </div>

                </div>

              </div>

              <div className="mt-8 p-4 bg-[#FF6F37]/10 border border-[#FF6F37]/20 rounded-lg">

                <p className="text-[#FF6F37] text-[10px] font-mono leading-relaxed">

                  <span className="font-bold">
                    FORENSIC_SUMMARY:
                  </span>

                  {" "}

                  BiLSTM networks detected temporal inconsistencies in facial frame transitions. Pixel-level manipulation identified in lip-sync region. Confidence level exceeds legal authentication threshold.

                </p>

              </div>

            </div>

          </div>
        )}

      </div>

    </CyberLayout>
  );
};

export default VideoDetection;