import React from 'react';
import { useNavigate } from 'react-router-dom';
import CyberLayout from '../components/CyberLayout';
import CyberCard from '../components/CyberCard';

const Detection = () => {
  const navigate = useNavigate();

  const detectionModes = [
    {
      title: "Image Detection",
      description: "Deep-level pixel analysis for static forensic checks and deepfake detection.",
      type: "image",
      onAction: () => navigate('/detection/image')
    },
    {
      title: "Video Detection",
      description: "Frame-by-frame temporal consistency monitoring for altered video content.",
      type: "video",
      onAction: () => navigate('/detection/video')
    },
    {
      title: "Live Detection",
      description: "Real-time neural network surveillance via low-latency webcam monitoring.",
      type: "live",
      onAction: () => navigate('/detection/live')
    }
  ];

  return (
    <CyberLayout>
      <div className="flex flex-col items-center justify-center min-h-screen px-6 py-10 md:py-20 overflow-x-hidden">

        {/* Header - Subtle blur-to-clear transition added in CSS */}
        <div className="text-center mb-12 md:mb-16 space-y-4 animate-fade-in-down">
          <h2 className="text-3xl sm:text-4xl md:text-6xl font-black tracking-tighter uppercase text-white">
            Choose Your <span className="text-[#FF6F37] drop-shadow-[0_0_10px_#FF6F37]">Analysis</span> Method
          </h2>
          <p className="text-gray-400 max-w-lg mx-auto text-xs md:text-base font-medium tracking-wide leading-relaxed opacity-80">
            Use our advanced AI to scan files and streams for digital alterations,
            helping you verify the authenticity of your media.
          </p>
          <div className="w-16 md:w-24 h-[2px] bg-[#FF6F37] mx-auto mt-6 rounded-full shadow-[0_0_20px_#FF6F37]" />
        </div>

        {/* Cards - Added transform-gpu for hardware acceleration */}
        <div className="flex flex-col md:flex-row flex-wrap justify-center items-center gap-8 md:gap-12 lg:gap-16 w-full">
          {detectionModes.map((mode, index) => (
            <div
              key={index}
              className="transform-gpu transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] hover:scale-[1.03] hover:-translate-y-2 animate-slide-up"
              style={{ 
                animationDelay: `${index * 120}ms`, // Slightly faster stagger for snappier feel
                animationFillMode: 'backwards' 
              }}
            >
              <CyberCard
                title={mode.title}
                description={mode.description}
                type={mode.type}
                onAction={mode.onAction}
              />
            </div>
          ))}
        </div>

        {/* Status Footer */}
        <div className="mt-16 md:mt-24 animate-pulse duration-[3000ms] flex items-center gap-3 text-[9px] md:text-[10px] uppercase tracking-[0.4em] text-gray-500">
          <span className="w-1.5 h-1.5 rounded-full bg-[#FF6F37] shadow-[0_0_10px_#FF6F37]" />
          System Status: <span className="text-gray-300">Optimal Analysis Ready</span>
        </div>
      </div>
    </CyberLayout>
  );
};

export default Detection;