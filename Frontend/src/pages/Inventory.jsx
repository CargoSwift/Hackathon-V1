import { useState, useEffect } from "react";
import "./Inventory.css";

const API_BASE = "http://localhost:8000";

export default function Inventory() {
  const [containers, setContainers] = useState([]);
  const [unplacedItems, setUnplacedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedContainer, setExpandedContainer] = useState(null);

  useEffect(() => {
    async function fetchInventory() {
      try {
        setLoading(true);

        // Fetch containers with their items
        const containersRes = await fetch(
          API_BASE + "/api/containers/with-items"
        );
        const containersData = await containersRes.json();

        // Fetch items not in any container
        const unplacedRes = await fetch(API_BASE + "/api/items/unplaced");
        const unplacedData = await unplacedRes.json();
        console.log(containersData);

        if (containersData.success) setContainers(containersData.containers);
        if (unplacedData.success) setUnplacedItems(unplacedData.items);
      } catch (error) {
        console.error("Error fetching inventory:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchInventory();
  }, []);

  const toggleContainer = (containerId) => {
    setExpandedContainer(
      expandedContainer === containerId ? null : containerId
    );
  };

  if (loading) {
    return <div className="loading">Loading inventory...</div>;
  }

  return (
    <div className="inventory-page">
      <h1>Space Station Inventory</h1>

      <div className="unplaced-items-section">
        <h2>Unplaced Items</h2>
        {unplacedItems.length > 0 ? (
          <table className="unplaced-items-table">
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Name</th>
                <th>Dimensions (WxDxH)</th>
                <th>Priority</th>
                <th>Preferred Zone</th>
              </tr>
            </thead>
            <tbody>
              {unplacedItems.map((item) => (
                <tr key={item.item_id}>
                  <td>{item.item_id}</td>
                  <td>{item.name}</td>
                  <td>
                    {item.width} × {item.depth} × {item.height} cm
                  </td>
                  <td>{item.priority}</td>
                  <td>{item.preferred_zone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>All items are properly placed in containers.</p>
        )}
      </div>

      <div className="container-cards">
        {containers.map((container) => (
          <div
            key={container.container_id}
            className={`container-card ${
              expandedContainer === container.container_id ? "expanded" : ""
            }`}
          >
            <div
              className="container-header"
              onClick={() => toggleContainer(container.container_id)}
            >
              <h3>
                {container.container_id}
                <span className="zone-badge">{container.zone}</span>
              </h3>
              <div className="space-usage">
                <div className="space-bar">
                  <div
                    className="space-used"
                    style={{
                      width: `${
                        ((container.total_volume - container.available_volume) /
                          container.total_volume) *
                        100
                      }%`,
                    }}
                  ></div>
                </div>
                <span className="space-text">
                  {container.total_volume - container.available_volume} /{" "}
                  {container.total_volume} cm³
                </span>
              </div>
              <span className="toggle-icon">
                {expandedContainer === container.container_id ? "▼" : "►"}
              </span>
            </div>

            {expandedContainer === container.container_id && (
              <div className="container-items">
                {container.items.length > 0 ? (
                  <table className="items-table">
                    <thead>
                      <tr>
                        <th>Item ID</th>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Dimensions</th>
                        <th>Priority</th>
                        <th>Status</th>
                        <th>Usage Limit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {container.items.map((item) => (
                        <tr key={item.item_id}>
                          <td>{item.item_id}</td>
                          <td>{item.name}</td>
                          <td>
                            ({item.start_coordinates.width},
                            {item.start_coordinates.depth},
                            {item.start_coordinates.height})
                          </td>
                          <td>
                            {item.width} × {item.depth} × {item.height} cm
                          </td>
                          <td>
                            <span
                              className={`priority-badge priority-${Math.floor(
                                item.priority / 20
                              )}`}
                            >
                              {item.priority}
                            </span>
                          </td>
                          <td>
                            {item.is_waste ? (
                              <span className="waste-badge">Waste</span>
                            ) : item.usage_limit <= 0 ? (
                              <span className="depleted-badge">Depleted</span>
                            ) : (
                              <span className="active-badge">Active</span>
                            )}
                          </td>
                          <td>{item.usage_limit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="empty-container">This container is empty.</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
