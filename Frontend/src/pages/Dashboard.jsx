import { useState } from 'react';
import ContainersUpload from '../components/ContainersUpload';
import ItemsUpload from '../components/ItemsUpload';
import PlacementRecommendations from '../components/PlacementRecommendations';
import './Dashboard.css'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('containers');

  return (
    <div className="dashboard">
      <h1>Cargo Management System</h1>
      
      <div className="tabs">
        <button 
          onClick={() => setActiveTab('containers')} 
          className={activeTab === 'containers' ? 'active' : ''}
        >
          Initialize Containers
        </button>
        <button 
          onClick={() => setActiveTab('items')} 
          className={activeTab === 'items' ? 'active' : ''}
        >
          Upload Resupply Items
        </button>
        <button 
          onClick={() => setActiveTab('placement')} 
          className={activeTab === 'placement' ? 'active' : ''}
        >
          Placement Recommendations
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'containers' && <ContainersUpload />}
        {activeTab === 'items' && <ItemsUpload />}
        {activeTab === 'placement' && <PlacementRecommendations />}
      </div>
    </div>
  );
}