#!/bin/bash
# MongoDB Replica Set Initialization Script

set -e

echo "Waiting for MongoDB nodes to be ready..."
sleep 10

echo "Initializing replica set..."
mongosh --host mongo1:27017 -u admin -p password123 --authenticationDatabase admin <<EOF
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 1 }
  ]
});
EOF

echo "Waiting for replica set to initialize..."
sleep 15

echo "Checking replica set status..."
mongosh --host mongo1:27017 -u admin -p password123 --authenticationDatabase admin <<EOF
rs.status();
EOF

echo "Creating test database and collection..."
mongosh --host mongo1:27017 -u admin -p password123 --authenticationDatabase admin <<EOF
use testdb;
db.createCollection("testcollection");
db.testcollection.createIndex({ timestamp: 1 });
db.testcollection.createIndex({ key: 1 }, { unique: true });
EOF

echo "Replica set initialization complete!"
