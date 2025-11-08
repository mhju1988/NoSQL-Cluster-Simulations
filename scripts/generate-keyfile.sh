#!/bin/bash
# Generate MongoDB replica set keyFile

KEYFILE_PATH="./mongodb-keyfile/mongodb-keyfile"

# Check if keyfile already exists
if [ -f "$KEYFILE_PATH" ]; then
    echo "KeyFile already exists at $KEYFILE_PATH"
    exit 0
fi

# Generate random keyfile (1024 bytes of base64 encoded random data)
openssl rand -base64 756 > "$KEYFILE_PATH"

# Set correct permissions (must be 400 or 600)
# Using 600 for better compatibility with Docker volume mounts
chmod 600 "$KEYFILE_PATH"

echo "MongoDB keyFile generated successfully at $KEYFILE_PATH"
echo "Permissions: $(ls -l $KEYFILE_PATH | awk '{print $1}')"
