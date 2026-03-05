# OmniNode Troubleshooting Guide

## Common Issues & Solutions

### 1. PostgreSQL Won't Start

**Symptom:** Container exits immediately or shows permission errors.

```bash
# Check logs
docker logs omninode-infra-postgres-1

# Common fixes:
# a) Permission issue on data volume
docker volume rm omninode-infra_postgres_data
./deploy_all.sh --execute --phase 2

# b) Insufficient shared memory
# Add to docker-compose or Docker daemon config:
# --shm-size=256m
```

### 2. Redpanda Broker Unreachable

**Symptom:** Services can't connect to Kafka on port 29092.

```bash
# Check if port is in use by something else
ss -tlnp | grep 29092

# Check Redpanda logs
docker logs omninode-infra-redpanda-1

# Redpanda needs minimum 512MB memory
# Verify: docker stats omninode-infra-redpanda-1
```

### 3. Database Migrations Fail

**Symptom:** Phase 2 reports migration errors.

```bash
# Check current migration state
psql -h localhost -p 5436 -U postgres -d omnibase_infra \
  -c "SELECT version, applied_at FROM schema_migrations ORDER BY version DESC LIMIT 10"

# Re-run migrations manually
cd ~/omninode-workspace/omnibase_infra
python3 scripts/run-migrations.py --apply

# Nuclear option: drop and recreate
psql -h localhost -p 5436 -U postgres -c "DROP DATABASE omnibase_infra"
psql -h localhost -p 5436 -U postgres -c "CREATE DATABASE omnibase_infra"
# Then re-run Phase 2
```

### 4. Infisical Bootstrap Fails

**Symptom:** `bootstrap-infisical.sh` exits with errors.

```bash
# Check Infisical is running
curl -sf http://localhost:8880/api/status

# Verify bootstrap credentials in .env:
# INFISICAL_ENCRYPTION_KEY must be 16+ bytes hex
# INFISICAL_AUTH_SECRET must be 32+ bytes hex

# Re-run bootstrap
cd ~/omninode-workspace/omnibase_infra
bash scripts/bootstrap-infisical.sh
```

### 5. Service Health Check Timeout

**Symptom:** Phase 3 hangs waiting for services.

```bash
# Check Docker container states
docker ps --filter "name=omninode" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific service logs
docker logs omninode-infra-runtime-1

# Common cause: slow machine / insufficient resources
# Increase timeout by re-running with VERBOSE:
./deploy_all.sh --execute --phase 3 --verbose
```

### 6. Port Already In Use

**Symptom:** "Port XXXX is already in use" during pre-flight checks.

```bash
# Find what's using the port
ss -tlnp | grep :8085
# Or on macOS:
lsof -i :8085

# Kill the process
kill <PID>

# Or change the port in .env
sed -i 's/RUNTIME_PORT=8085/RUNTIME_PORT=8185/' ~/omninode-workspace/omnibase_infra/docker/.env
```

### 7. OmniClaude Shows STANDALONE

**Symptom:** Expected FULL_ONEX but banner shows STANDALONE.

```bash
# Step 1: Check Kafka connectivity
(echo >/dev/tcp/localhost/29092) && echo "OK" || echo "FAIL"

# Step 2: Check intelligence-api
curl -sf http://localhost:8053/health && echo "OK" || echo "FAIL"

# Step 3: Verify .env has KAFKA_BOOTSTRAP_SERVERS
grep KAFKA_BOOTSTRAP_SERVERS ~/omninode-workspace/omniclaude/.env

# Step 4: Delete cached capabilities
rm -f ~/.claude/.onex_capabilities

# Step 5: Restart Claude Code session
# The probe runs automatically on SessionStart
```

### 8. OmniDash Database Error

**Symptom:** OmniDash shows database connection errors.

```bash
cd ~/omninode-workspace/omnidash

# Check the database URL
cat .env | grep DB_URL

# Push Drizzle schema
npm run db:push

# Run SQL migrations
npm run db:migrate

# Check if omnidash_analytics database exists
psql -h localhost -p 5436 -U postgres -c "\\l" | grep omnidash
```

### 9. Qdrant/Memgraph Not Starting

**Symptom:** Memory services fail in Phase 4.

```bash
# Check OmniMemory containers
cd ~/omninode-workspace/omnimemory
docker compose ps
docker compose logs

# Common: port conflict with local Redis on 6379
# Fix: change MEMORY_VALKEY_PORT in .env

# Qdrant needs storage space
df -h /var/lib/docker
```

### 10. Python Import Errors

**Symptom:** Phase 1 verification fails with import errors.

```bash
# Check Python version
python3 --version  # Must be 3.12+

# Check if packages are installed
python3 -c "import omnibase_spi; print(omnibase_spi.__version__)"
python3 -c "import omnibase_core; print(omnibase_core.__version__)"

# Reinstall with editable mode
cd ~/omninode-workspace/omnibase_spi && pip install -e .
cd ~/omninode-workspace/omnibase_core && pip install -e .
```

### 11. Docker Network Issues

**Symptom:** Containers can't communicate with each other.

```bash
# Check if omninode-network exists
docker network ls | grep omninode

# Create it manually if missing
docker network create omninode-network

# Verify containers are on the network
docker network inspect omninode-network
```

### 12. Disk Space Issues

**Symptom:** Services fail randomly, Docker build errors.

```bash
# Check disk usage
df -h /var/lib/docker
docker system df

# Clean up
docker system prune -af --volumes
docker builder prune -af
```

## Diagnostic Commands

```bash
# Full system status
docker ps --filter "name=omninode" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Service logs (last 50 lines)
docker logs --tail 50 <container_name>

# Database connectivity test
pg_isready -h localhost -p 5436 -U postgres

# Kafka topic list
docker exec omninode-infra-redpanda-1 rpk topic list

# Verify all ports
ss -tlnp | grep -E '(5436|16379|29092|8085|8053|6333|7687|3000)'

# Run comprehensive verification
./verify_deployment.sh --live
```

