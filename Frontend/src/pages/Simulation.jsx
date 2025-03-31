import { useState, useEffect } from "react";
import { api } from "../utils/api";
import "./Simulation.css";

const API_BASE = "http://localhost:8000";
export default function Simulation() {
  const [daysToSimulate, setDaysToSimulate] = useState(1);
  const [itemsToUse, setItemsToUse] = useState([]);
  const [currentItemId, setCurrentItemId] = useState("");
  const [currentUses, setCurrentUses] = useState(1);
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);

  // Fetch all items on component mount
  useEffect(() => {
    async function fetchItems() {
      try {
        setLoading(true);
        const response = await fetch(API_BASE + "/api/items");
        const data = await response.json();
        if (data.success) {
          setItems(data.items);
        }
      } catch (error) {
        console.error("Error fetching items:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchItems();
  }, []);

  const handleAddItem = () => {
    if (!currentItemId || currentUses < 1) return;

    // Find the selected item details
    const selectedItem = items.find((item) => item.item_id === currentItemId);

    setItemsToUse((prev) => [
      ...prev,
      {
        itemId: currentItemId,
        name: selectedItem?.name || currentItemId,
        uses: currentUses,
      },
    ]);
    setCurrentItemId("");
    setCurrentUses(1);
  };

  const handleRemoveItem = (index) => {
    setItemsToUse((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSimulate = async () => {
    if (daysToSimulate < 1) return;

    try {
      setLoading(true);
      const result = await api.simulateDay({
        numOfDays: daysToSimulate,
        itemsToBeUsedPerDay: itemsToUse.map(({ itemId, uses }) => ({
          itemId,
          uses,
        })),
      });

      if (result.success) {
        setSimulationResult(result);
      }
    } catch (error) {
      console.error("Error simulating time:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="simulation">
      <h1>Time Simulation</h1>

      <div className="simulation-controls">
        <div className="form-group">
          <label>Days to Simulate:</label>
          <input
            type="number"
            value={daysToSimulate}
            onChange={(e) =>
              setDaysToSimulate(Math.max(1, parseInt(e.target.value) || 1))
            }
            min="1"
          />
        </div>

        <div className="items-to-use">
          <h2>Items to Use Each Day</h2>

          <div className="add-item">
            <select
              value={currentItemId}
              onChange={(e) => setCurrentItemId(e.target.value)}
              disabled={loading || items.length === 0}
            >
              <option value="">Select an item</option>
              {items.map((item) => (
                <option key={item.item_id} value={item.item_id}>
                  {item.item_id} - {item.name}
                  {item.usage_limit !== null &&
                    ` (Uses left: ${item.usage_limit})`}
                  {item.expiry_date &&
                    ` (Expires: ${new Date(
                      item.expiry_date
                    ).toLocaleDateString()})`}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={currentUses}
              onChange={(e) =>
                setCurrentUses(Math.max(1, parseInt(e.target.value) || 1))
              }
              min="1"
              placeholder="Uses per day"
              disabled={!currentItemId}
            />
            <button
              onClick={handleAddItem}
              disabled={!currentItemId || currentUses < 1}
            >
              Add Item
            </button>
          </div>

          {itemsToUse.length > 0 && (
            <table className="items-table">
              <thead>
                <tr>
                  <th>Item ID</th>
                  <th>Name</th>
                  <th>Uses per Day</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {itemsToUse.map((item, index) => (
                  <tr key={index}>
                    <td>{item.itemId}</td>
                    <td>{item.name}</td>
                    <td>{item.uses}</td>
                    <td>
                      <button
                        onClick={() => handleRemoveItem(index)}
                        className="remove-button"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <button
          onClick={handleSimulate}
          disabled={loading || itemsToUse.length === 0}
          className="simulate-button"
        >
          {loading ? "Simulating..." : "Simulate Time"}
        </button>
      </div>

      {simulationResult && (
        <div className="simulation-results">
          <h2>Simulation Results</h2>
          <p>Simulated {simulationResult.daysSimulated} days</p>

          {simulationResult.changes.itemsExpired.length > 0 && (
            <div className="result-section">
              <h3>Expired Items</h3>
              <table>
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationResult.changes.itemsExpired.map((day, index) => (
                    <tr key={index}>
                      <td>{day.day}</td>
                      <td>{day.count} items</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {simulationResult.changes.itemsDepletedToday.length > 0 && (
            <div className="result-section">
              <h3>Depleted Items</h3>
              <table>
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Item ID</th>
                    <th>Name</th>
                  </tr>
                </thead>
                <tbody>
                  {simulationResult.changes.itemsDepletedToday.map(
                    (item, index) => (
                      <tr key={index}>
                        <td>{item.day}</td>
                        <td>{item.itemId}</td>
                        <td>{item.name}</td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}

          {simulationResult.changes.itemsUsed.length > 0 && (
            <div className="result-section">
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
  );
}
