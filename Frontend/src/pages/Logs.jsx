import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import "./Logs.css"

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    itemId: '',
    userId: '',
    actionType: '',
    limit: 50,
    offset: 0
  });
  const [totalLogs, setTotalLogs] = useState(0);

  useEffect(() => {
    fetchLogs();
  }, [filters.limit, filters.offset]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const result = await api.getLogs(filters);
      if (result.success) {
        setLogs(result.logs);
        setTotalLogs(result.total);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleApplyFilters = () => {
    setFilters(prev => ({ ...prev, offset: 0 }));
  };

  const handleResetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      itemId: '',
      userId: '',
      actionType: '',
      limit: 50,
      offset: 0
    });
  };

  const handlePageChange = (newOffset) => {
    setFilters(prev => ({ ...prev, offset: newOffset }));
  };

  return (
    <div className="logs">
      <h1>Activity Logs</h1>
      
      <div className="filters">
        <div className="filter-group">
          <label>Start Date:</label>
          <input 
            type="date" 
            name="startDate"
            value={filters.startDate}
            onChange={handleFilterChange}
          />
        </div>
        
        <div className="filter-group">
          <label>End Date:</label>
          <input 
            type="date" 
            name="endDate"
            value={filters.endDate}
            onChange={handleFilterChange}
          />
        </div>
        
        <div className="filter-group">
          <label>Item ID:</label>
          <input 
            type="text" 
            name="itemId"
            value={filters.itemId}
            onChange={handleFilterChange}
            placeholder="Filter by item ID"
          />
        </div>
        
        <div className="filter-group">
          <label>User ID:</label>
          <input 
            type="text" 
            name="userId"
            value={filters.userId}
            onChange={handleFilterChange}
            placeholder="Filter by user ID"
          />
        </div>
        
        <div className="filter-group">
          <label>Action Type:</label>
          <select 
            name="actionType"
            value={filters.actionType}
            onChange={handleFilterChange}
          >
            <option value="">All Actions</option>
            <option value="placement">Placement</option>
            <option value="retrieval">Retrieval</option>
            <option value="rearrangement">Rearrangement</option>
            <option value="disposal">Disposal</option>
            <option value="import">Import</option>
            <option value="export">Export</option>
            <option value="simulation">Simulation</option>
          </select>
        </div>
        
        <div className="filter-buttons">
          <button onClick={handleApplyFilters}>Apply Filters</button>
          <button onClick={handleResetFilters}>Reset Filters</button>
        </div>
      </div>
      
      <div className="logs-list">
        {loading ? (
          <p>Loading logs...</p>
        ) : logs.length > 0 ? (
          <>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Item ID</th>
                  <th>User ID</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.log_id}>
                    <td>{new Date(log.logged_at).toLocaleString()}</td>
                    <td>{log.action_type}</td>
                    <td>{log.item_id || 'N/A'}</td>
                    <td>{log.user_id || 'System'}</td>
                    <td>{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            <div className="pagination">
              <button 
                onClick={() => handlePageChange(Math.max(0, filters.offset - filters.limit))}
                disabled={filters.offset === 0}
              >
                Previous
              </button>
              <span>
                Showing {filters.offset + 1} to {Math.min(filters.offset + filters.limit, totalLogs)} of {totalLogs} logs
              </span>
              <button 
                onClick={() => handlePageChange(filters.offset + filters.limit)}
                disabled={filters.offset + filters.limit >= totalLogs}
              >
                Next
              </button>
            </div>
          </>
        ) : (
          <p>No logs found matching your filters.</p>
        )}
      </div>
    </div>
  );
}