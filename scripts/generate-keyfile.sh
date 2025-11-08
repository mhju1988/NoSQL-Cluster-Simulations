#!/bin/bash
# Generate MongoDB replica set keyFile using Docker (cross-platform)

set -e

KEYFILE_DIR="./mongodb-keyfile"
KEYFILE_PATH="$KEYFILE_DIR/mongodb-keyfile"

# Get absolute path for Docker volume mounting
# Create directory first to ensure it exists
mkdir -p "$KEYFILE_DIR"

# Convert Windows path to Docker-compatible path if on Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$(uname -s)" == MINGW* ]]; then
    # On Windows (Git Bash/MINGW), convert path
    ABS_PATH=$(cd "$KEYFILE_DIR" && pwd -W 2>/dev/null || pwd)
else
    # On Linux/Mac, use absolute path
    ABS_PATH=$(cd "$KEYFILE_DIR" && pwd)
fi

# Check if keyfile already exists
if [ -f "$KEYFILE_PATH" ]; then
    echo "KeyFile already exists at $KEYFILE_PATH"

    # Verify permissions using Docker
    docker run --rm -v "$ABS_PATH:/keyfile" mongo:7.0 sh -c "
        ls -l /keyfile/mongodb-keyfile
        PERMS=\$(stat -c '%a' /keyfile/mongodb-keyfile 2>/dev/null || stat -f '%Lp' /keyfile/mongodb-keyfile)
        if [ \"\$PERMS\" = \"600\" ] || [ \"\$PERMS\" = \"400\" ]; then
            echo 'KeyFile permissions are correct'
            exit 0
        else
            echo 'KeyFile permissions need to be fixed'
            exit 1
        fi
    " || {
        echo "Fixing keyFile permissions..."
        docker run --rm -v "$ABS_PATH:/keyfile" mongo:7.0 chmod 400 /keyfile/mongodb-keyfile
    }
    exit 0
fi

echo "Generating MongoDB keyFile using Docker..."
echo "Mounting directory: $ABS_PATH"

# Generate keyfile inside a Docker container (works on all platforms)
docker run --rm -v "$ABS_PATH:/keyfile" mongo:7.0 sh -c "
    openssl rand -base64 756 > /keyfile/mongodb-keyfile
    chmod 400 /keyfile/mongodb-keyfile
    chown 999:999 /keyfile/mongodb-keyfile
    echo 'KeyFile generated successfully'
    ls -l /keyfile/mongodb-keyfile
"

echo "MongoDB keyFile generated successfully at $KEYFILE_PATH"
echo "Verifying permissions..."

docker run --rm -v "$ABS_PATH:/keyfile" mongo:7.0 sh -c "
    ls -l /keyfile/mongodb-keyfile
    stat -c 'Permissions: %a' /keyfile/mongodb-keyfile 2>/dev/null || stat -f 'Permissions: %Lp' /keyfile/mongodb-keyfile
"
