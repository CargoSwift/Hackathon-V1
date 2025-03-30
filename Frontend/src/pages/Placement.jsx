import { useState, useEffect } from 'react'
import { api } from '../utils/api'

export default function Placement() {
  const [newItems, setNewItems] = useState([])
  const [placements, setPlacements] = useState([])
  const [rearrangements, setRearrangements] = useState([])
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleImport = async () => {
    if (!file) return
    
    try {
      setLoading(true)
      const result = await api.importItems(file)
      if (result.success) {
        alert(`Successfully imported ${result.itemsImported} items`)
        setNewItems(prev => [...prev, ...Array(result.itemsImported).fill({})]) // Mock
      } else {
        alert('Import failed')
      }
    } catch (error) {
      console.error('Error importing items:', error)
      alert('Error importing items')
    } finally {
      setLoading(false)
    }
  }

  const handlePlacement = async () => {
    if (newItems.length === 0) return
    
    try {
      setLoading(true)
      const result = await api.getPlacementRecommendations(newItems)
      if (result.success) {
        setPlacements(result.placements)
        setRearrangements(result.rearrangements)
      }
    } catch (error) {
      console.error('Error getting placement recommendations:', error)
      alert('Error getting placement recommendations')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="placement">
      <h1>Placement Recommendations</h1>
      
      <div className="import-section">
        <h2>Import New Items</h2>
        <input type="file" accept=".csv" onChange={handleFileChange} />
        <button onClick={handleImport} disabled={!file || loading}>
          {loading ? 'Importing...' : 'Import Items'}
        </button>
      </div>
      
      <div className="placement-section">
        <h2>Place New Items</h2>
        <button onClick={handlePlacement} disabled={newItems.length === 0 || loading}>
          {loading ? 'Calculating...' : 'Get Placement Recommendations'}
        </button>
        
        {placements.length > 0 && (
          <div className="results">
            <h3>Placement Recommendations</h3>
            <table>
              <thead>
                <tr>
                  <th>Item ID</th>
                  <th>Container ID</th>
                  <th>Position</th>
                </tr>
              </thead>
              <tbody>
                {placements.map((placement, index) => (
                  <tr key={index}>
                    <td>{placement.itemId}</td>
                    <td>{placement.containerId}</td>
                    <td>
                      ({placement.position.startCoordinates.width}, 
                      {placement.position.startCoordinates.depth}, 
                      {placement.position.startCoordinates.height}) to (
                      {placement.position.endCoordinates.width}, 
                      {placement.position.endCoordinates.depth}, 
                      {placement.position.endCoordinates.height})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {rearrangements.length > 0 && (
          <div className="rearrangements">
            <h3>Rearrangements Needed</h3>
            <ul>
              {rearrangements.map((rearrangement, index) => (
                <li key={index}>
                  {rearrangement.itemId}: {rearrangement.message}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}