// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Placement from './pages/Placement'
import Retrieval from './pages/Retrieval'
import Rearrangement from './pages/Rearrangement'
import WasteManagement from './pages/WasteManagement'
import Simulation from './pages/Simulation'
import Logs from './pages/Logs'
import Navigation from './components/Navigation'

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navigation />
        <div className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/placement" element={<Placement />} />
            <Route path="/retrieval" element={<Retrieval />} />
            <Route path="/rearrangement" element={<Rearrangement />} />
            <Route path="/waste" element={<WasteManagement />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App