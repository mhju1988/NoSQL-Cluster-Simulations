# Windows Setup Guide

This guide provides Windows-specific instructions for running the NoSQL Cluster Simulation framework.

## Prerequisites

### Required Software

1. **Docker Desktop for Windows** (version 4.0+)
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure WSL 2 backend is enabled (Settings → General → Use WSL 2)

2. **Git for Windows** (Git Bash)
   - Download from: https://git-scm.com/download/win
   - Includes Bash shell for running scripts

3. **System Requirements**
   - Windows 10/11 (64-bit)
   - WSL 2 enabled
   - 8GB RAM minimum
   - 20GB free disk space

## Important Windows-Specific Notes

### 1. MongoDB KeyFile Permissions

**Issue:** Windows does not support Unix file permissions like Linux/Mac. Running `chmod 600` on Windows doesn't actually set the permissions correctly, which causes MongoDB to reject the keyFile.

**Solution:** The framework automatically generates the keyFile **inside a Docker container** where Linux permissions work properly. This happens automatically when you run `./start.sh`.

### 2. Line Endings (CRLF vs LF)

**Issue:** Windows uses CRLF line endings, but Linux/Docker expects LF. This can cause scripts to fail.

**Solution:** Git for Windows should auto-convert line endings. If you see errors like `^M: bad interpreter`, run:

```bash
# Convert line endings for all shell scripts
find . -name "*.sh" -exec dos2unix {} \;

# Or use git to fix them
git config core.autocrlf input
git rm --cached -r .
git reset --hard
```

### 3. Docker Compose Command

**Issue:** Newer Docker Desktop uses `docker compose` (V2) instead of `docker-compose` (V1).

**Solution:** The `start.sh` script uses `docker-compose`, but if you see "command not found":

```bash
# Option 1: Edit start.sh and replace 'docker-compose' with 'docker compose'
sed -i 's/docker-compose/docker compose/g' start.sh

# Option 2: Run commands manually
docker compose up -d
```

### 4. Volume Mounting Paths

**Issue:** Windows paths (e.g., `C:\Users\...`) need to be converted to Unix-style paths for Docker.

**Current Setup:** The docker-compose.yml uses relative paths (./mongodb-keyfile, ./scripts) which work correctly on Windows with Docker Desktop.

**If you need absolute paths:**
```yaml
# Windows path: E:\Projects\NoSQL-Cluster-Simulations
# Docker path: /e/Projects/NoSQL-Cluster-Simulations
volumes:
  - /e/Projects/NoSQL-Cluster-Simulations/mongodb-keyfile:/keyfile
```

## Quick Start on Windows

### Step 1: Open Git Bash

Right-click in your project folder and select "Git Bash Here"

### Step 2: Clean Any Existing Setup

```bash
# Stop and remove containers
docker compose down -v

# Remove old keyFile
rm -f ./mongodb-keyfile/mongodb-keyfile
```

### Step 3: Start the Cluster

```bash
# Make scripts executable
chmod +x *.sh
chmod +x scripts/*.sh
chmod +x chaos/*.sh

# Start the cluster
./start.sh
```

**Expected Output:**
```
Step 1: Generating MongoDB keyFile using Docker...
KeyFile generated successfully
-r--------    1 mongodb  mongodb       1024 Nov  8 01:00 /keyfile/mongodb-keyfile
Permissions: 400

Step 2: Starting Docker containers...
✔ Container mongo1 Started
✔ Container mongo2 Started
✔ Container mongo3 Started
...
```

### Step 4: Verify Everything Works

```bash
# Check status
./status.sh

# Run a quick test
docker exec test-orchestrator python load_generator.py --duration 10
```

## Common Windows Issues

### Issue: "permission denied: ./start.sh"

**Solution:**
```bash
chmod +x start.sh
./start.sh
```

### Issue: "docker: command not found"

**Cause:** Docker Desktop is not running or not in PATH

**Solution:**
1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Verify: `docker --version`

### Issue: "Cannot connect to Docker daemon"

**Cause:** Docker Desktop not running or WSL 2 integration disabled

**Solution:**
1. Start Docker Desktop
2. Go to Settings → Resources → WSL Integration
3. Enable integration for your WSL distro
4. Click "Apply & Restart"

### Issue: Scripts show ^M characters

**Cause:** CRLF line endings

**Solution:**
```bash
# Option 1: Use dos2unix
dos2unix start.sh

# Option 2: Use sed
sed -i 's/\r$//' start.sh

# Option 3: Use Git to checkout with LF
git config core.autocrlf input
git checkout .
```

### Issue: MongoDB containers keep restarting

**Check logs:**
```bash
docker logs mongo1
```

**Common causes:**
1. KeyFile permissions incorrect → Solution: Regenerate keyFile
   ```bash
   rm -f mongodb-keyfile/mongodb-keyfile
   bash scripts/generate-keyfile.sh
   ```

2. Port already in use → Solution: Change ports in docker-compose.yml or stop conflicting process
   ```powershell
   # Find what's using port 27017
   netstat -ano | findstr :27017
   ```

3. Insufficient resources → Solution: Increase Docker Desktop resources
   - Settings → Resources → Advanced
   - Increase CPUs and Memory

## Performance Tips for Windows

### 1. Use WSL 2 (Not Hyper-V)

WSL 2 is significantly faster than the Hyper-V backend.

**Verify WSL 2:**
```bash
docker info | grep "Operating System"
# Should show: Operating System: Docker Desktop (WSL 2)
```

### 2. Store Project in WSL Filesystem

For better performance, clone the repo inside WSL:

```bash
# From WSL terminal
cd ~
git clone <repository-url>
cd NoSQL-Cluster-Simulations
./start.sh
```

### 3. Allocate Sufficient Resources

Docker Desktop Settings → Resources:
- **CPUs:** At least 4 cores
- **Memory:** At least 8GB
- **Swap:** 2GB
- **Disk:** 20GB

### 4. Disable Antivirus Scanning

Add Docker directories to antivirus exclusions:
- `C:\Program Files\Docker`
- `C:\ProgramData\Docker`
- Your project directory

## Running Chaos Scenarios on Windows

### Using Git Bash

```bash
# Interactive mode
./chaos/chaos-scenarios.sh

# Specific scenario
./chaos/chaos-scenarios.sh node-failure mongo1
```

### Using PowerShell

```powershell
# Use bash to run the script
bash ./chaos/chaos-scenarios.sh
```

## Monitoring on Windows

### Access Grafana

Open in your browser:
```
http://localhost:3000
```

Default credentials:
- Username: `admin`
- Password: `admin`

### Access Prometheus

```
http://localhost:9090
```

## Troubleshooting Commands (Windows)

```bash
# Check Docker is running
docker info

# Check containers
docker compose ps

# View logs
docker compose logs -f mongo1

# Check MongoDB connection
docker exec -it mongo1 mongosh -u admin -p password123 --authenticationDatabase admin

# Check keyFile permissions (using Docker)
docker run --rm -v "$(pwd)/mongodb-keyfile:/keyfile" mongo:7.0 ls -l /keyfile/mongodb-keyfile

# Clean restart
docker compose down -v
rm -rf mongodb-keyfile/mongodb-keyfile
./start.sh
```

## Development Tools for Windows

### Recommended

1. **VS Code** with extensions:
   - Docker
   - Remote - WSL
   - MongoDB for VS Code

2. **Windows Terminal** (better than Git Bash)
   - Available from Microsoft Store
   - Supports tabs, better rendering

3. **MongoDB Compass** (GUI for MongoDB)
   - Download: https://www.mongodb.com/products/compass
   - Connection string: `mongodb://admin:password123@localhost:27017/?authSource=admin`

## Differences from Linux/Mac

| Feature | Linux/Mac | Windows |
|---------|-----------|---------|
| KeyFile generation | Direct `chmod` works | Uses Docker container |
| Line endings | LF | CRLF (auto-converted by Git) |
| Docker command | `docker compose` or `docker-compose` | Usually `docker compose` |
| File paths | /home/user/... | C:\Users\... (converted by Docker Desktop) |
| Shell scripts | Native bash | Git Bash or WSL |
| Performance | Native | Via WSL 2 or Hyper-V |

## Getting Help

If you encounter Windows-specific issues:

1. Check this guide first
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check Docker Desktop logs: Settings → Troubleshoot → View logs
4. Check WSL status: `wsl --status`
5. Open an issue on GitHub with:
   - Windows version
   - Docker Desktop version
   - Error messages
   - Output of `docker info`

## External Resources

- [Docker Desktop for Windows Documentation](https://docs.docker.com/desktop/windows/)
- [WSL 2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Git for Windows](https://gitforwindows.org/)
- [MongoDB on Windows](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/)
