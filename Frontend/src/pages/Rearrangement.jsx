import { useEffect, useState } from 'react'
import './Rearrangement.css'

export default function Rearrangement() {
  const [containers, setContainers] = useState([])
  const [selectedContainer, setSelectedContainer] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [rearrangementPlan, setRearrangementPlan] = useState(null)

  useEffect(() => {
    // Mock data - in a real app, fetch from API
    setContainers([
      { container_id: 'contA', zone: 'Crew Quarters', available_volume: 5000 },
      { container_id: 'contB', zone: 'Airlock', available_volume: 3000 },
      { container_id: 'contC', zone: 'Laboratory', available_volume: 8000 }
    ])
  }, [])

  useEffect(() => {
    if (!selectedContainer) return
    
    // Mock data - in a real app, fetch items in container from API
    setItems([
      { item_id: 'ITEM001', name: 'Food Packet', priority: 80, width: 10, depth: 10, height: 20 },
      { item_id: 'ITEM002', name: 'Oxygen Cylinder', priority: 95, width: 15, depth: 15, height: 50 },
      { item_id: 'ITEM003', name: 'First Aid Kit', priority: 100, width: 20, depth: 20, height: 10 }
    ])
  }, [selectedContainer])

  const handleGeneratePlan = async () => {
    if (!selectedContainer) return
    
    try {
      setLoading(true)
      // In a real app, call API to generate rearrangement plan
      // This is mock data
      setTimeout(() => {
        setRearrangementPlan({
          containerId: selectedContainer,
          steps: [
            { action: 'move', itemId: 'ITEM002', from: 'contA', to: 'contC', reason: 'Make space for high priority items' },
            { action: 'rotate', itemId: 'ITEM001', newOrientation: 'width: 20, depth: 10, height: 10' }
          ],
          estimatedTime: '15 minutes',
          spaceGained: '2000 cm³'
        })
        setLoading(false)
      }, 1000)
    } catch (error) {
      console.error('Error generating rearrangement plan:', error)
      setLoading(false)
    }
  }

  return (
    <div className="rearrangement">
      <h1>Rearrangement Optimization</h1>
      
      <div className="container-selection">
        <h2>Select Container to Optimize</h2>
        <select 
          value={selectedContainer} 
          onChange={(e) => setSelectedContainer(e.target.value)}
        >
          <option value="">Select a container</option>
          {containers.map(container => (
            <option key={container.container_id} value={container.container_id}>
              {container.container_id} ({container.zone}) - {container.available_volume} cm³ available
            </option>
          ))}
        </select>
      </div>
      
      {selectedContainer && (
        <div className="container-contents">
          <h3>Items in Container {selectedContainer}</h3>
          <table>
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Name</th>
                <th>Priority</th>
                <th>Dimensions (W×D×H)</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.item_id}>
                  <td>{item.item_id}</td>
                  <td>{item.name}</td>
                  <td>{item.priority}</td>
                  <td>{item.width} × {item.depth} × {item.height}</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          <button onClick={handleGeneratePlan} disabled={loading}>
            {loading ? 'Generating Plan...' : 'Generate Rearrangement Plan'}
          </button>
        </div>
      )}
      
      {rearrangementPlan && (
        <div className="rearrangement-plan">
          <h2>Rearrangement Plan for {rearrangementPlan.containerId}</h2>
          <p><strong>Estimated Time:</strong> {rearrangementPlan.estimatedTime}</p>
          <p><strong>Space Gained:</strong> {rearrangementPlan.spaceGained}</p>
          
          <h3>Steps:</h3>
          <ol>
            {rearrangementPlan.steps.map((step, index) => (
              <li key={index}>
                {step.action === 'move' ? (
                  <>Move item {step.itemId} from {step.from} to {step.to}. Reason: {step.reason}</>
                ) : (
                  <>Rotate item {step.itemId}. New orientation: {step.newOrientation}</>
                )}
              </li>
            ))}
          </ol>
          
          <button className="execute-button">Execute Rearrangement</button>
        </div>
      )}
    </div>
  )
}