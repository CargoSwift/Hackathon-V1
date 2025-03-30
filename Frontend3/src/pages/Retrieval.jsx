import { useState } from 'react'
import { api } from '../utils/api'

export default function Retrieval() {
  const [searchTerm, setSearchTerm] = useState('')
  const [userId, setUserId] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [placement, setPlacement] = useState(null)

  const handleSearch = async () => {
    if (!searchTerm) return
    
    try {
      setLoading(true)
      const params = {}
      if (searchTerm.startsWith('ITEM')) {
        params.itemId = searchTerm
      } else {
        params.itemName = searchTerm
      }
      if (userId) params.userId = userId
      
      const result = await api.searchItem(params)
      setSearchResults(result)
      
      if (result.found) {
        setPlacement(result.placement)
      }
    } catch (error) {
      console.error('Error searching for item:', error)
      alert('Error searching for item')
    } finally {
      setLoading(false)
    }
  }

  const handleRetrieve = async () => {
    if (!searchResults?.found || !userId) return
    
    try {
      setLoading(true)
      const result = await api.retrieveItem({
        itemId: searchResults.item.item_id,
        userId: userId
      })
      
      if (result.success) {
        alert(`Item retrieved successfully! Steps: ${result.steps}`)
        // Refresh search results to show updated usage
        handleSearch()
      }
    } catch (error) {
      console.error('Error retrieving item:', error)
      alert('Error retrieving item')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="retrieval">
      <h1>Item Retrieval</h1>
      
      <div className="search-section">
        <div className="form-group">
          <label>Search by Item ID or Name:</label>
          <input 
            type="text" 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
            placeholder="Enter item ID or name"
          />
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
        
        <button onClick={handleSearch} disabled={!searchTerm || loading}>
          {loading ? 'Searching...' : 'Search Item'}
        </button>
      </div>
      
      {searchResults && (
        <div className="results-section">
          {searchResults.found ? (
            <>
              <h2>Item Found</h2>
              <div className="item-details">
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
                  <h3>Placement Information</h3>
                  <p><strong>Container:</strong> {placement.container_id}</p>
                  <p><strong>Zone:</strong> {placement.zone}</p>
                  <p><strong>Retrieval Steps:</strong> {searchResults.retrievalSteps}</p>
                  
                  <h4>Retrieval Instructions:</h4>
                  <ol>
                    {searchResults.instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ol>
                </div>
              )}
              
              <button 
                onClick={handleRetrieve} 
                disabled={!userId || loading}
                className="retrieve-button"
              >
                {loading ? 'Retrieving...' : 'Retrieve Item'}
              </button>
            </>
          ) : (
            <p>No item found matching your search.</p>
          )}
        </div>
      )}
    </div>
  )
}