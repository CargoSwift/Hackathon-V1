-- CREATE ROLE cargo_admin WITH
-- 	LOGIN
-- 	NOSUPERUSER
-- 	NOCREATEDB
-- 	NOCREATEROLE
-- 	INHERIT
-- 	NOREPLICATION
-- 	CONNECTION LIMIT -1
-- 	PASSWORD 'admin';

-- CREATE DATABASE cargo_db
--     WITH
--     OWNER = cargo_admin
--     ENCODING = 'UTF8'
--     CONNECTION LIMIT = -1
--     IS_TEMPLATE = False;


CREATE TABLE items (
    item_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the item
    name VARCHAR(100) NOT NULL, -- Name of the item
    width NUMERIC NOT NULL, -- Width of the item (cm)
    depth NUMERIC NOT NULL, -- Depth of the item (cm)
    height NUMERIC NOT NULL, -- Height of the item (cm)
    mass NUMERIC NOT NULL, -- Mass of the item (kg)
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 100), -- Priority (1-100)
    expiry_date DATE, -- Expiry date of the item (if applicable)
    usage_limit INTEGER, -- Number of uses remaining
    preferred_zone VARCHAR(50) NOT NULL, -- Preferred zone for placement
    current_zone VARCHAR(50), -- Current zone where the item is placed
    is_waste BOOLEAN DEFAULT FALSE -- Whether the item is marked as waste
);


CREATE TABLE containers (
    container_id VARCHAR(50) PRIMARY KEY, -- Unique identifier for the container
    zone VARCHAR(50) NOT NULL, -- Zone where the container is located
    width NUMERIC NOT NULL, -- Width of the container (cm)
    depth NUMERIC NOT NULL, -- Depth of the container (cm)
    height NUMERIC NOT NULL, -- Height of the container (cm)
    available_volume NUMERIC NOT NULL -- Available volume in the container (cm³)
);


CREATE TABLE placements (
    placement_id SERIAL PRIMARY KEY, -- Unique identifier for the placement
    item_id VARCHAR(50) REFERENCES items(item_id) ON DELETE CASCADE, -- Item placed
    container_id VARCHAR(50) REFERENCES containers(container_id) ON DELETE CASCADE, -- Container where the item is placed
    start_coordinates JSONB NOT NULL, -- Start coordinates of the item (width, depth, height)
    end_coordinates JSONB NOT NULL, -- End coordinates of the item (width, depth, height)
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp when the item was placed
);



CREATE TABLE retrievals (
    retrieval_id SERIAL PRIMARY KEY, -- Unique identifier for the retrieval
    item_id VARCHAR(50) REFERENCES items(item_id) ON DELETE CASCADE, -- Item retrieved
    user_id VARCHAR(50) NOT NULL, -- Astronaut who retrieved the item
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of retrieval
    steps INTEGER NOT NULL, -- Number of steps required for retrieval
    from_container VARCHAR(50) REFERENCES containers(container_id) ON DELETE SET NULL, -- Container from which the item was retrieved
    to_container VARCHAR(50) REFERENCES containers(container_id) ON DELETE SET NULL -- Container where the item was placed back (if applicable)
);



CREATE TABLE waste (
    waste_id SERIAL PRIMARY KEY, -- Unique identifier for the waste entry
    item_id VARCHAR(50) REFERENCES items(item_id) ON DELETE CASCADE, -- Item marked as waste
    reason VARCHAR(100) NOT NULL, -- Reason for marking as waste (e.g., "Expired", "Out of Uses")
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp when the item was marked as waste
);




CREATE TABLE return_plans (
    plan_id SERIAL PRIMARY KEY, -- Unique identifier for the return plan
    undocking_container_id VARCHAR(50) REFERENCES containers(container_id) ON DELETE SET NULL, -- Container used for undocking
    undocking_date DATE NOT NULL, -- Date of undocking
    max_weight NUMERIC NOT NULL, -- Maximum weight limit for the undocking container
    total_volume NUMERIC NOT NULL, -- Total volume of waste in the plan
    total_weight NUMERIC NOT NULL, -- Total weight of waste in the plan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp when the plan was created
);



CREATE TABLE logs (
    log_id SERIAL PRIMARY KEY, -- Unique identifier for the log entry
    action_type VARCHAR(50) NOT NULL, -- Type of action (e.g., "placement", "retrieval", "rearrangement", "disposal")
    item_id VARCHAR(50) REFERENCES items(item_id) ON DELETE SET NULL, -- Item involved in the action
    user_id VARCHAR(50), -- Astronaut who performed the action
    details TEXT, -- Additional details about the action
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of the action
);



ALTER TABLE IF EXISTS public.containers
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.items
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.logs
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.placements
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.retrievals
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.return_plans
    OWNER TO cargo_admin;

ALTER TABLE IF EXISTS public.waste
    OWNER TO cargo_admin;
