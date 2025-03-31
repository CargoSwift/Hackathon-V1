import { Link } from "react-router-dom";

export default function Navigation() {
  return (
    <nav className="navigation">
      <ul>
        <li>
          <Link to="/">Dashboard</Link>
        </li>
        <li>
          <Link to="/retrieval">Retrieval</Link>
        </li>
        <li>
          <Link to="/rearrangement">Rearrangement</Link>
        </li>
        <li>
          <Link to="/waste">Waste Management</Link>
        </li>
        <li>
          <Link to="/simulation">Time Simulation</Link>
        </li>

        <li>
          <Link to="/inventory">Inventory</Link>
        </li>
        <li>
          <Link to="/logs">Logs</Link>
        </li>
      </ul>
    </nav>
  );
}
