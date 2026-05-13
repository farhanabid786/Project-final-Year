import React from 'react'
import { motion } from "framer-motion";
import EvilEye from '../components/EvilEye';
import BlurText from '../components/ui/BlurText';
import HomeText from '../components/HomeText';
import TryNow from '../components/TryNow';

const Home = () => {
  // Enhanced smoothness variants with spring physics
  const eyeVariants = {
    hidden: {
      opacity: 0,
      scale: 0.9,
      y: 30,
      filter: "blur(15px)",
    },
    visible: {
      opacity: 1,
      scale: 1.1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        delay: 0.6,
        type: "spring",
        stiffness: 40,       // Lower stiffness for that "heavy/smooth" feel
        damping: 18,         // Controls the bounce
        mass: 1,
        filter: { duration: 1.2 }
      },
    },
  };

  return (
    <div style={{ backgroundColor: '#000000', minHeight: '100vh', width: '100%', overflowX: 'hidden' }}>

      <div className='flex flex-col justify-center items-center py-12 w-full'>
        <BlurText
          text="Welcome to दृष्टि Vision"
          delay={200}
          animateBy="words"
          direction="top"

          className="hindi-orange text-5xl md:text-8xl font-bold mb-4 text-white tracking-tight"
        />

        <BlurText
          text="Detect deepfakes with AI precision. Fast, accurate, and reliable."
          delay={100}
          animateBy="words"
          direction="top"
          /* Increased max-w here from xl to 3xl */
          className="text-gray-500 mb-8 text-2xl md:text-2xl max-w-4xl text-center"
        />
      </div>

      <div style={{
        width: '100%',
        height: '75vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000000',
        overflow: 'hidden',
       
      }}>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={eyeVariants}
          style={{
            /* Increased size: vmin is safer than px for responsive design */
            width: '85vmin',
            height: '85vmin',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom : "35vh"
          }}
        >
          <EvilEye
            eyeColor="#FF6F37"
            intensity={1.3}   // Boosted intensity to make it pop at larger size
            pupilSize={0.6}
            irisWidth={0.25}
            glowIntensity={0.4}
            scale={0.9}        // Now you can safely use a high scale
            noiseScale={1}
            pupilFollow={1.3}
            flameSpeed={0.8}
            backgroundColor="#000000"
          />
        </motion.div>
      </div>
      <div>
        <HomeText />
      </div>
      <div>
        <TryNow />
      </div>
    </div>
  )
}

export default Home;