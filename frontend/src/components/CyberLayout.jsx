const CyberLayout = ({ children }) => {
  return (
    <div className="relative min-h-screen">
      <div className="cyber-grid" />
      <div className="cyber-global-glow" />
      <div className="cyber-orb-top" />
      <div className="cyber-orb" />
      
      {/* Content stays on top */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};
export default CyberLayout;