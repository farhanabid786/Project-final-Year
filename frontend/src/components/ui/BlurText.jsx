import React from "react";
import { motion } from "framer-motion";

const BlurText = ({
  text,
  delay = 100,
  animateBy = "words",
  direction = "top",
  className = "",
}) => {
  const items = animateBy === "words" ? text.split(" ") : text.split("");

  const variants = {
    hidden: {
      opacity: 0,
      y: direction === "top" ? 20 : -20,
      filter: "blur(10px)",
    },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        delay: i * (delay / 1000),
        duration:0.9,
        ease: [0.22, 1, 0.36, 1],
      },
    }),
  };

  return (
    <div className={className}>
      {items.map((item, i) => (
        <motion.span
          key={i}
          custom={i}
          initial="hidden"
          animate="visible"
          variants={variants}
          className="inline-block mr-2"
        >
          {item}
        </motion.span>
      ))}
    </div>
  );
};

export default BlurText;