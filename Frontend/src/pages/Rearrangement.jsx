import { useState, useEffect } from "react";
import "./Rearrangement.css";

const API_BASE = "http://localhost:8000";

export default function Rearrangement() {
  const [containers, setContainers] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rearrangementPlan, setRearrangementPlan] = useState(null);
  const [executionResults, setExecutionResults] = useState(null);
  const [selectedContainer, setSelectedContainer] = useState("");

  // Fetch containers and items data
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [containersRes, itemsRes] = await Promise.all([
          fetch(API_BASE + "/api/containers"),
          fetch(API_BASE + "/api/items?include_waste=false"),
        ]);

        const containersData = await containersRes.json();
        const itemsData = await itemsRes.json();

        if (containersData.success) setContainers(containersData.containers);
        if (itemsData.success) setItems(itemsData.items);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const generateRearrangementPlan = async () => {
    if (!selectedContainer) return;

    try {
      setLoading(true);
      const response = await fetch(API_BASE + "/api/rearrange", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          containerId: selectedContainer,
          items: items.filter((i) => i.current_zone === selectedContainer),
        }),
      });

      const result = await response.json();
      if (result.success) {
        setRearrangementPlan(result.plan);
      }
    } catch (error) {
      console.error("Error generating rearrangement plan:", error);
    } finally {
      setLoading(false);
    }
  };

  const executeRearrangement = async () => {
    if (!rearrangementPlan) return;

    try {
      setLoading(true);
      const response = await fetch(API_BASE + "/api/rearrange/execute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          planId: rearrangementPlan.planId,
        }),
      });

      const result = await response.json();
      if (result.success) {
        setExecutionResults(result);
        // Refresh data
        const containersRes = await fetch(API_BASE + "/api/containers");
        const containersData = await containersRes.json();
        if (containersData.success) setContainers(containersData.containers);
      }
    } catch (error) {
      console.error("Error executing rearrangement:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rearrangement">
      <h1>Space Management and Rearrangement</h1>

      <div className="container-selection">
        <h2>Select Container to Optimize</h2>
        <select
          value={selectedContainer}
          onChange={(e) => setSelectedContainer(e.target.value)}
          disabled={loading}
        >
          <option value="">Select a container</option>
          {containers.map((container) => (
            <option key={container.container_id} value={container.container_id}>
              {container.container_id} ({container.zone}) - Available:{" "}
              {container.available_volume} cm³ / Total:{" "}
              {container.width * container.depth * container.height} cm³
            </option>
          ))}
        </select>

        <button
          onClick={generateRearrangementPlan}
          disabled={!selectedContainer || loading}
        >
          {loading ? "Analyzing..." : "Generate Rearrangement Plan"}
        </button>
      </div>

      {rearrangementPlan && (
        <div className="rearrangement-plan">
          <h2>Rearrangement Plan for {selectedContainer}</h2>

          <div className="plan-stats">
            <p>
              <strong>Estimated Space Freed:</strong>{" "}
              {rearrangementPlan.spaceFreed} cm³
            </p>
            <p>
              <strong>Items to Move:</strong>{" "}
              {rearrangementPlan.itemsToMove.length}
            </p>
            <p>
              <strong>Estimated Time:</strong> {rearrangementPlan.estimatedTime}{" "}
              minutes
            </p>
          </div>

          <div className="steps">
            <h3>Step-by-Step Instructions</h3>
            <ol>
              {rearrangementPlan.steps.map((step, index) => (
                <li key={index}>
                  {step.action === "move" ? (
                    <>
                      Move <strong>{step.itemId}</strong> from{" "}
                      {step.fromContainer} to {step.toContainer}
                    </>
                  ) : (
                    <>
                      Rotate <strong>{step.itemId}</strong> to{" "}
                      {step.newOrientation}
                    </>
                  )}
                  {step.reason && (
                    <span className="reason"> - {step.reason}</span>
                  )}
                </li>
              ))}
            </ol>
          </div>

          <button
            onClick={executeRearrangement}
            disabled={loading}
            className="execute-button"
          >
            {loading ? "Executing..." : "Execute Rearrangement"}
          </button>
        </div>
      )}

      {executionResults && (
        <div className="execution-results">
          <h3>Rearrangement Results</h3>
          <p>
            <strong>Status:</strong>{" "}
            {executionResults.success ? "Success" : "Failed"}
          </p>
          {executionResults.message && <p>{executionResults.message}</p>}
          {executionResults.itemsMoved && (
            <p>
              <strong>Items Moved:</strong> {executionResults.itemsMoved}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
