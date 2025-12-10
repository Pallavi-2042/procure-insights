#!/bin/bash

# Install and configure PostgreSQL with pgvector
echo "Setting up PostgreSQL with pgvector..."

# Install PostgreSQL
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib postgresql-server-dev-all

# Install pgvector
cd /tmp
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Start PostgreSQL
sudo service postgresql start

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE procurement_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE procurement_db TO postgres;
\c procurement_db
CREATE EXTENSION vector;
EOF

echo "PostgreSQL with pgvector setup complete!"