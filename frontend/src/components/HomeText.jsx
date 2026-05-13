import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

const HomeText = () => {
    const containerRef = useRef(null);

    // 1. TRACK SCROLL PROGRESS: Specifically for this component
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start end", "end start"] // Starts when top of div hits bottom of screen
    });

    // 2. SCROLL-BASED TRANSFORMS:
    // As the user scrolls, these values will shift smoothly
    const titleY = useTransform(scrollYProgress, [0, 0.4], [100, 0]);
    const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
    const scale = useTransform(scrollYProgress, [0, 0.3], [0.8, 1]);

    return (
        <motion.div
            ref={containerRef}
            style={{
                maxWidth: '1100px',
                margin: '0 auto',
                padding: '150px 20px', // Extra padding to give scroll space
                color: '#ffffff',
                fontFamily: "'Inter', system-ui, sans-serif",
                opacity, // Entire section fades in/out based on scroll
            }}
        >
            {/* SCROLL-LINKED HEADING */}
            <motion.h1
                style={{
                    y: titleY,
                    scale,
                    textAlign: 'center',
                    lineHeight: 1, // Matches tracking-tight feel
                    marginBottom: '1rem', // mb-4 equivalent
                    letterSpacing: '-0.05em', // tracking-tight
                    textTransform: 'uppercase',
                    // Responsive Font Logic (5xl to 8xl)
                    fontSize: 'clamp(3rem, 10vw, 6rem)',
                    fontWeight: '800', // font-bold
                    color: '#ffffff', // base text-white
                }}
            >
                Securing {" "}
                <span style={{ color: '#FF6F37' }}>
                    Truth
                </span>
                {" "} in the Age of AI
            </motion.h1>

            {/* REVEAL ON VIEW: Staggered Features */}
            <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ margin: "-100px" }} // Triggers slightly before it hits center
                transition={{ duration: 1 }}
                style={{
                    fontSize: 'clamp(1rem, 2vw, 1.25rem)',
                    lineHeight: '1.8',
                    textAlign: 'center',
                    color: '#A0A0A0',
                    maxWidth: '850px',
                    margin: '0 auto 80px auto'
                }}
            >
                In an era of synthetic media, we provide a critical line of defense. Our platform
                leverages state-of-the-art neural networks to dissect pixel-level inconsistencies
                and biological markers.
            </motion.p>

            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '25px',
                    marginBottom: '100px'
                }}
            >
                {[
                    { title: "Image Detection", desc: "Identifies GAN signatures and pixel-level artifacts hidden within static media." },
                    { title: "Video Analysis", desc: "Monitors frame-to-frame temporal consistency and unnatural blinking patterns." },
                    { title: "Live Verification", desc: "Active, real-time defense against identity spoofing and digital injection masks." }
                ].map((feature, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 50 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: false, amount: 0.3 }} // Re-animates if they scroll back up
                        transition={{ delay: idx * 0.2, duration: 0.6 }} // Staggered reveal
                        whileHover={{ y: -10, borderColor: '#FF6F37', transition: { duration: 0.2 } }}
                        style={{
                            padding: '40px 30px',
                            borderRadius: '20px',
                            background: 'linear-gradient(145deg, #0f0f0f, #050505)',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
                            position: 'relative',
                            overflow: 'hidden'
                        }}
                    >
                        <h3 style={{ color: '#FF6F37', fontSize: '1.5rem', marginBottom: '15px', fontWeight: '700' }}>
                            {feature.title}
                        </h3>
                        <p style={{ fontSize: '1rem', color: '#888', lineHeight: '1.6' }}>
                            {feature.desc}
                        </p>
                    </motion.div>
                ))}
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8 }}
                style={{
                    textAlign: 'center',
                    padding: '60px 40px',
                    background: 'rgba(255, 111, 55, 0.03)',
                    borderRadius: '30px',
                    border: '1px solid rgba(255, 111, 55, 0.1)',
                    backdropFilter: 'blur(10px)'
                }}
            >
                <h2 style={{ fontSize: '2rem', color: '#ffffff', marginBottom: '25px', fontWeight: '800' }}>
                    
                    
                    Why {" "} <span style={{color: '#FF6F37'}}>Trust</span> {" "}Our Model?
                </h2>
                <p style={{ fontSize: '1.1rem', color: '#999', maxWidth: '800px', margin: '0 auto', lineHeight: '1.7' }}>
                    We deliver high-precision, privacy-first forensics designed to secure digital truth.
                </p>
            </motion.div>
        </motion.div>
    );
};

export default HomeText;