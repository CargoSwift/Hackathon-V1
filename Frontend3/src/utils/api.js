// src/utils/api.js
const API_BASE = '/api'

export const api = {
  // Placement
  getPlacementRecommendations: (items) => 
    fetch(`${API_BASE}/placement`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items })
    }).then(res => res.json()),

  // Retrieval
  searchItem: (params) => 
    fetch(`${API_BASE}/search?${new URLSearchParams(params)}`)
      .then(res => res.json()),
  
  retrieveItem: (data) => 
    fetch(`${API_BASE}/retrieve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),
  
  placeItem: (data) => 
    fetch(`${API_BASE}/place`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),

  // Waste Management
  identifyWaste: () => 
    fetch(`${API_BASE}/waste/identify`)
      .then(res => res.json()),
  
  createReturnPlan: (data) => 
    fetch(`${API_BASE}/waste/return-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),
  
  completeUndocking: (data) => 
    fetch(`${API_BASE}/waste/complete-undocking`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),

  // Time Simulation
  simulateDay: (data) => 
    fetch(`${API_BASE}/simulate/day`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(res => res.json()),

  // Data Import/Export
  importItems: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`${API_BASE}/import/items`, {
      method: 'POST',
      body: formData
    }).then(res => res.json())
  },
  
  exportArrangement: () => 
    fetch(`${API_BASE}/export/arrangement`)
      .then(res => res.blob()),

  // Logs
  getLogs: (params) => 
    fetch(`${API_BASE}/logs?${new URLSearchParams(params)}`)
      .then(res => res.json())
}