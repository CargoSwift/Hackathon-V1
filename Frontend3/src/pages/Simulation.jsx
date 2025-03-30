import { useState } from 'react'
import { api } from '../utils/api'

export default function Simulation() {
  const [daysToSimulate, setDaysToSimulate] = useState(1)
  const [itemsToUse, setItemsToUse] = useState([])
  const [currentItemId, setCurrentItemId] = useState('')
  const [currentUses, setCurrentUses] = useState(1)
  const [simulationResult, setSimulationResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAddItem = () => {
    if (!currentItemId || currentUses < 1) return
    
    setItemsToUse(prev => [
      ...prev,
      { itemId: currentItemId, uses: currentUses }
    ])
    setCurrentItemId('')
    setCurrentUses(1)
  }

  const handleRemoveItem = (index) => {
    setItemsToUse(prev => prev.filter((_, i) => i !== index))
  }

  const handleSimulate = async () => {
    if (daysToSimulate < 1) return
    
    try {
      setLoading(true)
      const result = await api.simulateDay({
        numOfDays: daysToSimulate,
        itemsToBeUsedPerDay: itemsToUse
      })
      
      if (result.success) {
        setSimulationResult(result)
      }
    } catch (error) {
      console.error('Error simulating time:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="simulation">
      <h1>Time Simulation</h1>
      
      <div className="simulation-controls">
        <div className="form-group">
          <label>Days to Simulate:</label>
          <input 
            type="number" 
            value={daysToSimulate}
            onChange={(e) => setDaysToSimulate(Math.max(1, parseInt(e.target.value) || 1))}
            min="1"
          />
        </div>
        
        <div className="items-to-use">
          <h2>Items to Use Each Day</h2>
          
          <div className="add-item">
            <input 
              type="text" 
              value={currentItemId}
              onChange={(e) => setCurrentItemId(e.target.value)}
              placeholder="Item ID"
            />
            <input 
              type="number" 
              value={currentUses}
              onChange={(e) => setCurrentUses(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
              placeholder="Uses"
            />
            <button onClick={handleAddItem}>Add Item</button>
          </div>
          
          {itemsToUse.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Item ID</th>
                  <th>Uses per Day</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {itemsToUse.map((item, index) => (
                  <tr key={index}>
                    <td>{item.itemId}</td>
                    <td>{item.uses}</td>
                    <td>
                      <button onClick={() => handleRemoveItem(index)}>Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        <button 
          onClick={handleSimulate} 
          disabled={loading}
          className="simulate-button"
        >
          {loading ? 'Simulating...' : 'Simulate Time'}
        </button>
      </div>
      
      {simulationResult && (
        <div className="simulation-results">
          <h2>Simulation Results</h2>
          <p>Simulated {simulationResult.daysSimulated} days</p>
          
          {simulationResult.changes.itemsExpired.length > 0 && (
            <div className="expired-items">
              <h3>Expired Items</h3>
              <ul>
                {simulationResult.changes.itemsExpired.map((day, index) => (
                  <li key={index}>
                    Day {day.day}: {day.count} items expired
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {simulationResult.changes.itemsDepletedToday.length > 0 && (
            <div className="depleted-items">
              <h3>Depleted Items</h3>
              <ul>
                {simulationResult.changes.itemsDepletedToday.map((item, index) => (
                  <li key={index}>
                    Day {item.day}: {item.name} (ID: {item.itemId}) - out of uses
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {simulationResult.changes.itemsUsed.length > 0 && (
            <div className="used-items">
              <h3>Items Used</h3>
              <table>
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Item ID</th>
                    <th>Name</th>
                    <th>Remaining Uses</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationResult.changes.itemsUsed.map((item, index) => (
                    <tr key={index}>
                      <td>{item.day}</td>
                      <td>{item.itemId}</td>
                      <td>{item.name}</td>
                      <td>{item.remainingUses}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}