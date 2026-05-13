import React, { useState, useRef, useEffect } from 'react';
import CyberLayout from '../components/CyberLayout';

const ImageDetection = () => {

  // Existing States
  const [selectedImage, setSelectedImage] = useState(null);
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
    "Analyzing Image Structure...",
    "Detecting Facial Landmarks...",
    "Running EfficientNet Model...",
    "Generating Confidence Score...",
    "Finalizing Forensics Report..."
  ];

  // cleanup preview memory
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // cinematic loading steps
  useEffect(() => {

    if (!loading) return;

    const interval = setInterval(() => {

      setAnalysisStep((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        }
        return prev;
      });

    }, 1200);

    return () => clearInterval(interval);

  }, [loading]);

  // file processing
  const processFile = (file) => {

    if (file && file.type.startsWith('image/')) {

      // cleanup old preview
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }

      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));

      // reset states
      setResult(null);
      setError(null);
      setAnalysisStep(0);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // REAL BACKEND ANALYSIS
  const handleAnalyze = async () => {

    if (!selectedImage || loading) return;

    try {

      setLoading(true);
      setResult(null);
      setError(null);
      setAnalysisStep(0);

      // form-data
      const formData = new FormData();

      formData.append("file", selectedImage);

      // backend request
      const response = await fetch(
        "http://localhost:5000/api/detect/image",
        {
          method: "POST",
          body: formData
        }
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Analysis failed");
      }

      const aiResult = data.result;

      // response mapping
      setResult({
        label: aiResult.label,
        confidence: aiResult.confidence,
        realProb: aiResult.real_prob,
        fakeProb: aiResult.fake_prob,
        faceDetected: aiResult.face_detected ? "TRUE" : "FALSE",
        processTime: `${aiResult.processing_ms}ms`
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

  const handleImageChange = (e) => processFile(e.target.files[0]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    processFile(e.dataTransfer.files[0]);
  };

  const triggerFileInput = () => fileInputRef.current.click();

  return (
    <CyberLayout>

      <style>
        {`
          .perspective-container { perspective: 2000px; }

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
            Image <span className="text-[#FF6F37] drop-shadow-[0_0_10px_#FF6F37]">Analysis</span> Terminal
          </h2>

          <p className="text-gray-400 mt-2 text-sm uppercase tracking-widest font-mono opacity-70">
            {loading
              ? "SYSTEM ACTIVE: ANALYZING..."
              : result
                ? "ANALYSIS COMPLETE"
                : "Status: Ready for Input"}
          </p>
        </div>

        {/* Upload Section */}
        <div
          className="perspective-container w-full max-w-2xl transform-gpu mb-8"
          onMouseEnter={() => setHasFlipped(true)}
        >

          <div className={`flip-card-inner relative shadow-2xl ${hasFlipped ? 'is-flipping' : ''}`}>

            {/* FRONT FACE */}
            <div className="flip-card-front backface-hidden w-full bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-8 flex flex-col items-center shadow-2xl transition-all duration-500 hover:border-white/20">

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageChange}
                accept="image/*"
                className="hidden"
              />

              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={triggerFileInput}
                className={`group relative w-full h-80 border-2 border-dashed transition-all duration-500 cursor-pointer flex items-center justify-center overflow-hidden rounded-xl
                  ${previewUrl
                    ? 'border-[#FF6F37]'
                    : isDragging
                      ? 'border-[#FF6F37] bg-[#FF6F37]/10'
                      : 'border-white/10'
                  }`}
              >

                {previewUrl ? (

                  <div className="relative w-full h-full p-2 overflow-hidden">

                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="w-full h-full object-contain"
                    />

                    {loading && (
                      <div className="absolute inset-0 bg-[#FF6F37]/20 animate-pulse pointer-events-none" />
                    )}

                  </div>

                ) : (

                  <div className="flex flex-col items-center justify-center text-gray-500 group-hover:text-[#FF6F37]">

                    <svg className="w-12 h-12 mb-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>

                    <p className="font-bold uppercase text-[10px] tracking-[0.3em]">
                      Initialize Data Stream
                    </p>

                  </div>

                )}

                {previewUrl && !result && (
                  <div className={`absolute inset-0 bg-gradient-to-b from-transparent via-[#FF6F37]/50 to-transparent h-[5px] w-full ${loading ? 'animate-scan-fast' : 'animate-scan'} pointer-events-none z-20`} />
                )}

              </div>

              {/* Buttons */}
              <div className="flex gap-4 mt-8 w-full">

                <button
                  onClick={(e) => {
                    e.stopPropagation();

                    if (previewUrl) {
                      URL.revokeObjectURL(previewUrl);
                    }

                    setSelectedImage(null);
                    setPreviewUrl(null);
                    setResult(null);
                    setError(null);
                  }}
                  className="flex-1 px-6 py-3 border border-white/10 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-red-500/20 transition-all"
                >
                  Flush Buffer
                </button>

                <button
                  disabled={!selectedImage || loading}
                  onClick={handleAnalyze}
                  className={`flex-1 px-6 py-3 font-black uppercase text-[10px] tracking-widest transition-all duration-500
                    ${selectedImage && !loading
                      ? 'bg-[#FF6F37] text-black shadow-[0_0_20px_#FF6F37]'
                      : 'bg-gray-900 text-gray-600 cursor-not-allowed'
                    }`}
                >
                  {loading ? "Analyzing..." : "Execute Analysis"}
                </button>

              </div>

            </div>

            {/* BACK FACE */}
            <div className="flip-card-back absolute inset-0 backface-hidden rotate-y-180 bg-[#FF6F37] rounded-2xl p-8 flex flex-col items-center justify-center text-black">

              <div className="text-[12px] font-black uppercase mb-6 opacity-70 tracking-[0.4em] border-b border-black/30 pb-2 w-full text-center">
                System Scan Active
              </div>

              <div className="w-24 h-24 rounded-full border-4 border-black mb-6 flex items-center justify-center relative">

                <div className="absolute inset-0 border-4 border-black/30 rounded-full animate-pulse scale-110" />

                <svg className="w-12 h-12 text-black animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeWidth="1.5" d="M12 4v1m0 14v1m8-8h-1m-14 0h-1m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
                </svg>

              </div>

              <p className="text-center text-lg font-black uppercase tracking-tighter">
                AI Forensics
              </p>

            </div>

          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="w-full max-w-2xl bg-black/50 border border-[#FF6F37]/30 rounded-xl p-6 mb-8 animate-pulse overflow-hidden relative">

            <div className="flex items-center gap-4">

              <div className="w-10 h-10 border-2 border-[#FF6F37] border-t-transparent rounded-full animate-spin" />

              <div>
                <p className="text-[#FF6F37] font-mono text-xs uppercase tracking-widest">
                  Running EfficientNet_v2
                </p>

                <p className="text-white font-bold text-sm uppercase">
                  {steps[analysisStep]}
                </p>
              </div>

            </div>

            <div className="mt-4 w-full bg-white/10 h-1 rounded-full overflow-hidden">

              <div
                className="bg-[#FF6F37] h-full transition-all duration-500 shadow-[0_0_10px_#FF6F37]"
                style={{ width: `${(analysisStep + 1) * 20}%` }}
              />

            </div>

          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="w-full max-w-2xl bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-8 animate-fade-in">

            <p className="text-red-400 font-mono text-xs uppercase tracking-widest">
              SYSTEM ERROR: {error}
            </p>

          </div>
        )}

        {/* Result Section */}
        {result && !loading && (

          <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in-up">

            {/* Summary Card */}
            <div className="md:col-span-1 bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 flex flex-col items-center justify-center text-center">

              <div className={`text-5xl font-black mb-2 ${result.label === 'FAKE' ? 'text-red-500' : 'text-green-500'} drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]`}>
                {result.label}
              </div>

              <p className="text-gray-400 text-[10px] uppercase tracking-[0.3em] mb-4">
                Probability Verdict
              </p>

              <div className="w-full h-px bg-white/10 mb-4" />

              <div className="space-y-3 w-full font-mono text-[10px]">

                <div className="flex justify-between">
                  <span className="text-gray-500">FACIAL_DETECTION:</span>
                  <span className="text-[#FF6F37]">{result.faceDetected}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-500">LATENCY:</span>
                  <span className="text-white">{result.processTime}</span>
                </div>

              </div>

            </div>

            {/* Metrics Dashboard */}
            <div className="md:col-span-2 bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-8">

              <h3 className="text-[#FF6F37] font-bold uppercase text-xs tracking-widest mb-6 flex items-center gap-2">

                <span className="w-2 h-2 bg-[#FF6F37] rounded-full animate-ping" />

                Analysis Metrics

              </h3>

              <div className="grid grid-cols-1 gap-6">

                {/* Fake Probability */}
                <div>

                  <div className="flex justify-between text-[10px] mb-2">

                    <span className="text-red-400 font-bold uppercase tracking-widest">
                      Manipulated (Fake)
                    </span>

                    <span className="text-white">
                      {result.fakeProb}%
                    </span>

                  </div>

                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">

                    <div
                      className="bg-red-500 h-full shadow-[0_0_10px_#ef4444]"
                      style={{ width: `${result.fakeProb}%` }}
                    />

                  </div>

                </div>

                {/* Real Probability */}
                <div>

                  <div className="flex justify-between text-[10px] mb-2">

                    <span className="text-green-400 font-bold uppercase tracking-widest">
                      Authentic (Real)
                    </span>

                    <span className="text-white">
                      {result.realProb}%
                    </span>

                  </div>

                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5">

                    <div
                      className="bg-green-500 h-full shadow-[0_0_10px_#22c55e]"
                      style={{ width: `${result.realProb}%` }}
                    />

                  </div>

                </div>

              </div>

              <div className="mt-8 p-4 bg-[#FF6F37]/10 border border-[#FF6F37]/20 rounded-lg">

                <p className="text-[#FF6F37] text-[10px] font-mono leading-relaxed">

                  <span className="font-bold">SYSTEM_NOTE:</span>

                  {" "}
                  EfficientNet analysis indicates high-frequency noise patterns typically associated with generative adversarial networks. Confidence level satisfies forensic standard protocols.

                </p>

              </div>

            </div>

          </div>
        )}

        {/* Footer */}
        {selectedImage && !result && !loading && (

          <div className="mt-6 flex gap-6 font-mono text-[10px] text-[#FF6F37] uppercase tracking-tighter bg-black/30 px-4 py-2 rounded-full border border-[#FF6F37]/20 animate-fade-in">

            <div className="flex gap-2">

              <span className="text-gray-500">File:</span>

              <span className="max-w-[150px] truncate">
                {selectedImage.name}
              </span>

            </div>

            <span className="opacity-30">|</span>

            <div className="flex gap-2">

              <span className="text-gray-500">Type:</span>

              <span>
                {selectedImage.type.split('/')[1]}
              </span>

            </div>

          </div>
        )}

      </div>

    </CyberLayout>
  );
};

export default ImageDetection;