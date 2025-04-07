# Stage 1: Frontend build
FROM node:18 as frontend-builder
WORKDIR /app/frontend
COPY Frontend/package*.json ./
RUN npm install
COPY Frontend .
RUN npm run build

# Stage 2: Final image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    POSTGRES_USER=cargo_admin \
    POSTGRES_PASSWORD=admin \
    POSTGRES_DB=cargo_db \
    DB_HOST=db \
    DB_NAME=cargo_db \
    DB_USER=cargo_admin \
    DB_PASSWORD=admin \
    DB_PORT=5432 \
    VITE_API_URL=http://localhost:8000/api

# Install system dependencies including Python 3.10 and PostgreSQL
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3-pip \
    postgresql \
    postgresql-client \
    postgresql-contrib \
    libpq-dev \
    python3-dev \
    gcc \
    ca-certificates \
    curl \
    gnupg2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Copy backend code
COPY Backend /app/backend
WORKDIR /app/backend

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy built frontend
COPY --from=frontend-builder /app/frontend /app/frontend

# Initialize PostgreSQL
RUN service postgresql start && \
    su - postgres -c "psql -c \"CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';\"" && \
    su - postgres -c "createdb -O $POSTGRES_USER $POSTGRES_DB" && \
    [ -f /app/backend/psql.sql ] && su - postgres -c "psql -d $POSTGRES_DB -f /app/backend/psql.sql" || echo "No SQL file found" && \
    service postgresql stop

# Verify installations
RUN python3 --version && \
    pip3 list && \
    python3 -c "import flask; print(f'Flask version: {flask.__version__}')" && \
    python3 -c "import psycopg2; print(f'Psycopg2 version: {psycopg2.__version__}')" && \
    node --version && \
    npm --version

# Expose ports
EXPOSE 5173 8000 5432

# Create startup script
RUN echo "#!/bin/bash\n\
service postgresql start\n\
cd /app/backend && python3 server.py &\n\
cd /app/frontend && npm run dev -- --host 0.0.0.0 &\n\
tail -f /dev/null" > /start.sh && \
    chmod +x /start.sh

WORKDIR /app
CMD ["/start.sh"]