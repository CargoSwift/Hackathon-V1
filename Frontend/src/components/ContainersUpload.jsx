import { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function ContainersUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(API_BASE + "/api/import/containers", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      setMessage(result.message);
    } catch (error) {
      setMessage("Error uploading containers");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Initialize System with Containers</h2>
      <p>
        Upload a CSV file with container definitions to initialize the system
      </p>

      <input type="file" accept=".csv" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? "Uploading..." : "Upload Containers"}
      </button>

      {message && <p>{message}</p>}
    </div>
  );
}
