import React from "react";
import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import "./App.css";
import Account from "./Components/Account/Account";
import DashboardLayoutBasic from "./Components/DashboardLayoutBasic/DashboardLayoutBasic";
import Data from "./Components/Data/Data";
import Home from "./Components/Home/Home";
import OAuth from "./Components/OAuth/OAuth";
import Profile from "./Components/Profile/Profile";

function App() {
  return (
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<DashboardLayoutBasic />} />
            <Route path="/data" element={<Data />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/account" element={<Account />} />
            <Route path="/OAuth" element={<OAuth />} />
          </Routes>
        </div>
      </Router>
  );
}

export default App;
