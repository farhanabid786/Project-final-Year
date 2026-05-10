import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';


const TryNow = () => {
  return (
    <div className="flex justify-center py-12 bg-transparent">
      <NavLink to="/detection">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="group relative flex items-center gap-3 overflow-hidden rounded-full border-2 border-[#FF6F37] px-10 py-4 text-lg font-bold uppercase tracking-[0.2em] text-white transition-shadow duration-300 hover:shadow-[0_0_25px_rgba(255,111,55,0.5)]"
        >
          {/* THE LASER SCAN EFFECT */}
          <motion.div
            initial={{ x: '-100%' }}
            whileHover={{ x: '100%' }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="absolute inset-0 z-0 bg-gradient-to-r from-transparent via-[#FF6F37]/30 to-transparent"
          />

          {/* BUTTON CONTENT */}
          <span className="relative z-10">Try Now</span>
          
          <motion.span 
            animate={{ x: [0, 5, 0] }} 
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
            className="relative z-10 text-2xl"
          >
            →
          </motion.span>
        </motion.button>
      </NavLink>
    </div>
  );
};

export default TryNow;