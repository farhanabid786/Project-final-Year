import React from "react";
import Navbar from "./components/Navbar";
import AppRoutes from "./routes/AppRoutes";

const App = () => {
  return (
    <div className="bg-black min-h-screen text-white pt-12">
      <Navbar />
      <AppRoutes />
    </div>
  );
};

export default App;