import React from 'react';
import CyberLayout from '../components/CyberLayout';

const TEAM_MEMBERS = [
  { 
    id: 1, 
    name: "Utsav", 
    role: "Full-Stack Developer", 
    bio: "Bridging the gap between robust server-side logic and interactive user interfaces. Specializes in building end-to-end forensic applications.", 
    tech: "React / Node.js / MongoDB / Express" 
  },
  { 
    id: 2, 
    name: "Farhan", 
    role: "AI/ML Engineer", 
    bio: "Focused on developing and deploying deep learning models for real-time media authentication and pattern recognition in digital assets.", 
    tech: "PyTorch / TensorFlow / OpenCV" 
  },
  { 
    id: 3, 
    name: "Nandini", 
    role: "Data Scientist", 
    bio: "Extracting actionable insights from complex datasets. Expert in statistical modeling and cleaning high-volume data for neural training.", 
    tech: "Python / R / Pandas / Scikit-learn" 
  },
  { 
    id: 4, 
    name: "Jamal", 
    role: "Backend Engineer", 
    bio: "Architecting high-performance server infrastructures and secure APIs to handle heavy video processing and concurrent system requests.", 
    tech: "Node.js / MongoDB / Express / AWS" 
  },
];

const About = () => {
  return (
    <CyberLayout>
      {/* 3D Transform CSS - Logic for the flip cards */}
      <style>
        {`
          .preserve-3d { transform-style: preserve-3d; }
          .backface-hidden { backface-visibility: hidden; }
          .rotate-y-180 { transform: rotateY(180deg); }
        `}
      </style>

      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-20 animate-fade-in">
        
        {/* Header Section with Glitch Animation */}
        <div className="text-center mb-16 group">
          <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter text-white animate-fade-in-down">
            The <span className="text-[#FF6F37] drop-shadow-[0_0_20px_rgba(255,111,55,0.4)]">Core</span> Team
          </h2>
          <div className="h-[2px] w-32 bg-[#FF6F37] mx-auto mt-2 animate-pulse" />
          <p className="text-gray-400 mt-4 max-w-lg mx-auto font-medium uppercase tracking-[0.2em] text-[10px] opacity-70">
            The engineering minds behind the analysis engine
          </p>
        </div>

        {/* Team Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-7xl">
          {TEAM_MEMBERS.map((member, index) => (
            <div 
              key={member.id} 
              className={`flip-card h-[400px] w-full group perspective-1000 animate-slide-up`}
              style={{ animationDelay: `${index * 150}ms` }} // Staggered entry logic
            >
              <div className="flip-card-inner relative w-full h-full transition-all duration-700 preserve-3d group-hover:rotate-y-180">
                
                {/* FRONT CARD */}
                <div className="flip-card-front absolute inset-0 backface-hidden bg-white/5 border border-white/10 rounded-xl flex flex-col items-center justify-center p-6 backdrop-blur-md shadow-xl transition-all group-hover:border-[#FF6F37]/50">
                  <div className="w-20 h-20 rounded-full border border-[#FF6F37]/50 mb-6 flex items-center justify-center bg-black relative transform transition-transform duration-500 group-hover:scale-110">
                    <span className="text-[#FF6F37] text-2xl font-black">{member.name[0]}</span>
                    
                    {/* Decorative orbit rings */}
                    <div className="absolute inset-[-4px] border border-[#FF6F37] rounded-full animate-ping opacity-30" />
                    <div className="absolute inset-0 border border-[#FF6F37]/40 rounded-full animate-spin-slow" />
                  </div>

                  <h3 className="text-white text-xl font-bold uppercase tracking-tight group-hover:text-[#FF6F37] transition-colors">
                    {member.name}
                  </h3>
                  
                  <p className="text-[#FF6F37] text-[10px] font-mono mt-2 tracking-widest border-t border-[#FF6F37]/30 pt-2 opacity-80">
                    {member.role}
                  </p>

                  <div className="absolute bottom-4 text-white/20 text-[8px] font-mono tracking-tighter group-hover:opacity-200 transition-opacity">
                    HOVER TO DECRYPT FILE
                  </div>
                </div>

                {/* BACK CARD */}
                <div className="flip-card-back absolute inset-0 backface-hidden bg-[#FF6F37] rounded-xl flex flex-col items-center justify-center p-8 rotate-y-180 text-black shadow-[0_0_50px_rgba(255,111,55,0.4)]">
                  <div className="text-[10px] font-black uppercase mb-4 opacity-70 tracking-widest border-b border-black/30 pb-1 w-full text-center">
                    Personel File: {member.id}
                  </div>
                  
                  <p className="text-center text-sm font-bold leading-relaxed mb-6">
                    {member.bio}
                  </p>
                  
                  <div className="w-full space-y-2">
                    <p className="text-[9px] font-black uppercase opacity-60 mb-1">Tech Stack:</p>
                    <div className="bg-black/10 px-3 py-2 rounded border border-black/20 text-[10px] font-black text-center backdrop-blur-sm">
                      {member.tech}
                    </div>
                  </div>

                  {/* Decorative corner accent on back */}
                  <div className="absolute top-2 right-2 text-black font-black text-xl">
                    //
                  </div>
                </div>

              </div>
            </div>
          ))}
        </div>

      </div>
    </CyberLayout>
  );
};

export default About;