import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import "./WasteManagement.css"

export default function WasteManagement() {
  const [wasteItems, setWasteItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [returnPlan, setReturnPlan] = useState(null)
  const [undockingData, setUndockingData] = useState({
    containerId: '',
    date: new Date().toISOString().split('T')[0],
    maxWeight: 1000
  })

  useEffect(() => {
    fetchWasteItems()
  }, [])

  const fetchWasteItems = async () => {
    try {
      setLoading(true)
      const result = await api.identifyWaste()
      if (result.success) {
        setWasteItems(result.wasteItems)
      }
    } catch (error) {
      console.error('Error fetching waste items:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateReturnPlan = async () => {
    if (!undockingData.containerId) return
    
    try {
      setLoading(true)
      const result = await api.createReturnPlan({
        undockingContainerId: undockingData.containerId,
        undockingDate: undockingData.date,
        maxWeight: undockingData.maxWeight
      })
      
      if (result.success) {
        setReturnPlan(result.returnPlan)
      }
    } catch (error) {
      console.error('Error creating return plan:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCompleteUndocking = async () => {
    if (!returnPlan?.planId) return
    
    try {
      setLoading(true)
      const result = await api.completeUndocking({
        planId: returnPlan.planId
      })
      
      if (result.success) {
        alert(`Successfully undocked ${result.itemsRemoved} waste items`)
        setReturnPlan(null)
        fetchWasteItems()
      }
    } catch (error) {
      console.error('Error completing undocking:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="waste-management">
      <h1>Waste Management</h1>
      
      <div className="waste-list">
        <h2>Waste Items</h2>
        <button onClick={fetchWasteItems} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Waste List'}
        </button>
        
        {wasteItems.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Name</th>
                <th>Reason</th>
                <th>Mass (kg)</th>
                <th>Volume (cm³)</th>
                <th>Marked Date</th>
              </tr>
            </thead>
            <tbody>
              {wasteItems.map(item => (
                <tr key={item.item_id}>
                  <td>{item.item_id}</td>
                  <td>{item.name}</td>
                  <td>{item.reason}</td>
                  <td>{item.mass}</td>
                  <td>{item.width * item.depth * item.height}</td>
                  <td>{new Date(item.marked_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No waste items identified.</p>
        )}
      </div>
      
      <div className="return-planning">
        <h2>Return Planning</h2>
        
        <div className="form-group">
          <label>Undocking Container ID:</label>
          <input 
            type="text" 
            value={undockingData.containerId}
            onChange={(e) => setUndockingData({...undockingData, containerId: e.target.value})}
            placeholder="Enter container ID"
          />
        </div>
        
        <div className="form-group">
          <label>Undocking Date:</label>
          <input 
            type="date" 
            value={undockingData.date}
            onChange={(e) => setUndockingData({...undockingData, date: e.target.value})}
          />
        </div>
        
        <div className="form-group">
          <label>Max Weight (kg):</label>
          <input 
            type="number" 
            value={undockingData.maxWeight}
            onChange={(e) => setUndockingData({...undockingData, maxWeight: e.target.value})}
            min="1"
          />
        </div>
        
        <button 
          onClick={handleCreateReturnPlan} 
          disabled={!undockingData.containerId || loading}
        >
          {loading ? 'Creating Plan...' : 'Create Return Plan'}
        </button>
      </div>
      
      {returnPlan && (
        <div className="return-plan">
          <h3>Return Plan Details</h3>
          <p><strong>Plan ID:</strong> {returnPlan.planId}</p>
          <p><strong>Items to Return:</strong> {returnPlan.itemsToReturn}</p>
          <p><strong>Total Volume:</strong> {returnPlan.totalVolume} cm³</p>
          <p><strong>Total Weight:</strong> {returnPlan.totalWeight} kg</p>
          
          <button 
            onClick={handleCompleteUndocking}
            disabled={loading}
            className="undock-button"
          >
            {loading ? 'Undocking...' : 'Complete Undocking'}
          </button>
        </div>
      )}
    </div>
  )
}