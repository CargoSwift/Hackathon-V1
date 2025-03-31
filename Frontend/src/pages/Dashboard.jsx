import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import './Dashboard.css'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalItems: 0,
    totalContainers: 0,
    availableVolume: 0,
    wasteItems: 0,
    highPriorityItems: 0
  })
  const [recentLogs, setRecentLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const logsRes = await api.getLogs({ limit: 5 }) // Ensure this function is correct
        setRecentLogs(logsRes.logs || []) // Ensure logsRes.logs exists

        // Mock stats - replace with actual API calls
        setStats({
          totalItems: 1243,
          totalContainers: 42,
          availableVolume: 12500,
          wasteItems: 28,
          highPriorityItems: 156
        })
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) return <div>Loading dashboard...</div>

  return (
    <div className="dashboard">
      <h1>Cargo Management Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Items</h3>
          <p>{stats.totalItems}</p>
        </div>
        <div className="stat-card">
          <h3>Containers</h3>
          <p>{stats.totalContainers}</p>
        </div>
        <div className="stat-card">
          <h3>Available Volume (cm³)</h3>
          <p>{stats.availableVolume.toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <h3>Waste Items</h3>
          <p>{stats.wasteItems}</p>
        </div>
        <div className="stat-card">
          <h3>High Priority Items</h3>
          <p>{stats.highPriorityItems}</p>
        </div>
      </div>

      <div className="recent-activity">
        <h2>Recent Activity</h2>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Action</th>
              <th>Item</th>
              <th>User</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {recentLogs.map((log, index) => (
              <tr key={log.log_id || index}> {/* Ensure unique key */}
                <td>{new Date(log.logged_at).toLocaleString()}</td>
                <td>{log.action_type}</td>
                <td>{log.item_id || 'N/A'}</td>
                <td>{log.user_id || 'System'}</td>
                <td>{log.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
