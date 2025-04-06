import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";
export default function PlacementRecommendations() {
  const [containers, setContainers] = useState([]);
  const [items, setItems] = useState([]);
  const [placements, setPlacements] = useState([]);
  const [rearrangements, setRearrangements] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch containers and items when component mounts
    async function fetchData() {
      try {
        setLoading(true);

        // Fetch containers
        const containersRes = await fetch(API_BASE + "/api/containers");
        if (!containersRes.ok) throw new Error("Failed to fetch containers");
        const containersData = await containersRes.json();

        if (containersData.success) {
          setContainers(containersData.containers);
        } else {
          throw new Error(
            containersData.message || "Failed to load containers"
          );
        }

        // Fetch items
        const itemsRes = await fetch(API_BASE + "/api/items");
        if (!itemsRes.ok) throw new Error("Failed to fetch items");
        const itemsData = await itemsRes.json();

        if (itemsData.success) {
          setItems(itemsData.items);
        } else {
          throw new Error(itemsData.message || "Failed to load items");
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        // You might want to add error state handling here
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleGeneratePlacements = async () => {
    try {
      console.log(containers);

      setLoading(true);
      const response = await fetch(API_BASE + "/api/placement", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          containers: containers.map((c) => ({
            containerId: c.container_id,
            zone: c.zone,
            available_volume: c.available_volume,
            width: c.width,
            depth: c.depth,
            height: c.height,
          })),
          items: items.map((i) => ({
            itemId: i.item_id,
            name: i.name,
            width: i.width,
            depth: i.depth,
            height: i.height,
            priority: i.priority,
            preferredZone: i.preferred_zone,
          })),
        }),
      });

      const result = await response.json();

      console.log(result);
      if (result.success) {
        setPlacements(result.placements);
        setRearrangements(result.rearrangements);
      }
    } catch (error) {
      console.error("Error generating placements:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="placement-recommendations">
      <h2>Placement Recommendations</h2>

      <button
        onClick={handleGeneratePlacements}
        disabled={loading || containers.length === 0 || items.length === 0}
      >
        {loading ? "Generating..." : "Generate Placement Recommendations"}
      </button>

      {placements.length > 0 && (
        <div className="results">
          <h3>Placement Recommendations</h3>
          <table>
            <thead>
              <tr>
                <th>Item ID</th>
                <th>Container ID</th>
                <th>Zone</th>
                <th>Position</th>
              </tr>
            </thead>
            <tbody>
              {placements.map((placement, index) => {
                const container = containers.find(
                  (c) => c.container_id === placement.containerId
                );
                return (
                  <tr key={index}>
                    <td>{placement.itemId}</td>
                    <td>{placement.containerId}</td>
                    <td>{container?.zone}</td>
                    <td>
                      ({placement.position.startCoordinates.width},
                      {placement.position.startCoordinates.depth},
                      {placement.position.startCoordinates.height}) to (
                      {placement.position.endCoordinates.width},
                      {placement.position.endCoordinates.depth},
                      {placement.position.endCoordinates.height})
                    </td>
                  </tr>
                );
              })}
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
  );
}
