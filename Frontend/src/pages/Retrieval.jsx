import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import './Retrieval.css'

export default function Retrieval() {
  const [items, setItems] = useState([]);
  const [containers, setContainers] = useState([]);
  const [selectedItem, setSelectedItem] = useState('');
  const [userId, setUserId] = useState('AS101');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [placement, setPlacement] = useState(null);
  const [newContainer, setNewContainer] = useState('');
  const [newPosition, setNewPosition] = useState({
    width: 0,
    depth: 0,
    height: 0
  });

  // Fetch all items and containers on component mount
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [itemsRes, containersRes] = await Promise.all([
          fetch('/api/items'),
          fetch('/api/containers')
        ]);
        
        const itemsData = await itemsRes.json();
        const containersData = await containersRes.json();
        
        if (itemsData.success) setItems(itemsData.items);
        if (containersData.success) setContainers(containersData.containers);
        
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleSearch = async () => {
    if (!selectedItem) return;
    
    try {
      setLoading(true);
      const result = await api.searchItem({
        itemId: selectedItem,
        userId: userId
      });
      setSearchResults(result);
      
      if (result.found) {
        setPlacement(result.placement);
      }
    } catch (error) {
      console.error('Error searching for item:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieve = async () => {
    if (!searchResults?.found || !userId) return;
    
    try {
      setLoading(true);
      const result = await api.retrieveItem({
        itemId: searchResults.item.item_id,
        userId: userId
      });
      
      if (result.success) {
        alert(`Item retrieved successfully! Steps: ${result.steps}`);
        handleSearch(); // Refresh search results
      }
    } catch (error) {
      console.error('Error retrieving item:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlaceItem = async () => {
    if (!searchResults?.found || !userId || !newContainer) return;
    
    try {
      setLoading(true);
      const result = await api.placeItem({
        itemId: searchResults.item.item_id,
        userId: userId,
        containerId: newContainer,
        position: {
          startCoordinates: newPosition,
          endCoordinates: {
            width: newPosition.width + searchResults.item.width,
            depth: newPosition.depth + searchResults.item.depth,
            height: newPosition.height + searchResults.item.height
          }
        }
      });
      
      if (result.success) {
        alert('Item placed successfully!');
        setNewContainer('');
        setNewPosition({ width: 0, depth: 0, height: 0 });
        handleSearch();
      }
    } catch (error) {
      console.error('Error placing item:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="retrieval">
      <h1>Item Retrieval and Placement</h1>
      
      <div className="search-section">
        <div className="form-group">
          <label>Select Item:</label>
          <select
            value={selectedItem}
            onChange={(e) => setSelectedItem(e.target.value)}
            disabled={loading || items.length === 0}
          >
            <option value="">Select an item</option>
            {items.map(item => (
              <option key={item.item_id} value={item.item_id}>
                {item.item_id} - {item.name} {item.expiry_date ? `(Expires: ${new Date(item.expiry_date).toLocaleDateString()})` : ''}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label>Astronaut ID:</label>
          <input 
            type="text" 
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Your astronaut ID"
          />
        </div>
        
        <button 
          onClick={handleSearch} 
          disabled={!selectedItem || loading}
        >
          {loading ? 'Searching...' : 'Find Item'}
        </button>
      </div>
      
      {searchResults && (
        <div className="results-section">
          {searchResults.found ? (
            <>
              <div className="item-details">
                <h2>Item Found</h2>
                <p><strong>Name:</strong> {searchResults.item.name}</p>
                <p><strong>ID:</strong> {searchResults.item.item_id}</p>
                <p><strong>Priority:</strong> {searchResults.item.priority}</p>
                <p><strong>Current Zone:</strong> {searchResults.item.current_zone}</p>
                {searchResults.item.usage_limit !== null && (
                  <p><strong>Remaining Uses:</strong> {searchResults.item.usage_limit}</p>
                )}
                {searchResults.item.expiry_date && (
                  <p><strong>Expiry Date:</strong> {new Date(searchResults.item.expiry_date).toLocaleDateString()}</p>
                )}
              </div>
              
              {placement && (
                <div className="placement-details">
                  <h3>Current Placement</h3>
                  <p><strong>Container:</strong> {placement.container_id}</p>
                  <p><strong>Zone:</strong> {placement.zone}</p>
                  <p><strong>Retrieval Steps:</strong> {searchResults.retrievalSteps}</p>
                  
                  <h4>Retrieval Instructions:</h4>
                  <ol>
                    {searchResults.instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ol>
                  
                  <button 
                    onClick={handleRetrieve} 
                    disabled={!userId || loading}
                    className="retrieve-button"
                  >
                    {loading ? 'Retrieving...' : 'Retrieve Item'}
                  </button>
                </div>
              )}
              
              <div className="placement-form">
                <h3>Place Item in New Location</h3>
                <div className="form-group">
                  <label>New Container:</label>
                  <select
                    value={newContainer}
                    onChange={(e) => setNewContainer(e.target.value)}
                    disabled={loading || containers.length === 0}
                  >
                    <option value="">Select a container</option>
                    {containers.map(container => (
                      <option key={container.container_id} value={container.container_id}>
                        {container.container_id} - {container.zone} 
                        (Available: {container.available_volume} cm³)
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Position (Width, Depth, Height):</label>
                  <div className="position-inputs">
                    <input 
                      type="number" 
                      value={newPosition.width}
                      onChange={(e) => setNewPosition({...newPosition, width: parseFloat(e.target.value) || 0})}
                      placeholder="Width"
                    />
                    <input 
                      type="number" 
                      value={newPosition.depth}
                      onChange={(e) => setNewPosition({...newPosition, depth: parseFloat(e.target.value) || 0})}
                      placeholder="Depth"
                    />
                    <input 
                      type="number" 
                      value={newPosition.height}
                      onChange={(e) => setNewPosition({...newPosition, height: parseFloat(e.target.value) || 0})}
                      placeholder="Height"
                    />
                  </div>
                </div>
                
                <button 
                  onClick={handlePlaceItem} 
                  disabled={!newContainer || loading}
                  className="place-button"
                >
                  {loading ? 'Placing...' : 'Place Item'}
                </button>
              </div>
            </>
          ) : (
            <p>No item found matching your search.</p>
          )}
        </div>
      )}
    </div>
  );
}