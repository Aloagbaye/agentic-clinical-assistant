# Database Setup Guide

This guide explains how to set up PostgreSQL and Redis for the agentic clinical assistant.

## Quick Start with Docker Compose (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs postgres
docker-compose logs redis
```

This will start:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`

Default credentials:
- **PostgreSQL**: `postgres/postgres` (user/password)
- **Database**: `clinical_assistant`

## Manual PostgreSQL Setup

### Windows

1. **Download PostgreSQL**
   - Download from: https://www.postgresql.org/download/windows/
   - Or use installer: https://www.postgresql.org/download/windows/installer/

2. **Install PostgreSQL**
   - Run the installer
   - Remember the password you set for the `postgres` user
   - Default port is `5432`

3. **Start PostgreSQL Service**
   ```powershell
   # Check if service is running
   Get-Service postgresql*

   # Start service if not running
   Start-Service postgresql-x64-15  # Adjust version number
   ```

4. **Create Database**
   ```powershell
   # Connect to PostgreSQL
   psql -U postgres

   # Create database
   CREATE DATABASE clinical_assistant;

   # Exit
   \q
   ```

### Linux/Mac

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install postgresql postgresql-contrib

   # macOS (Homebrew)
   brew install postgresql
   brew services start postgresql

   # CentOS/RHEL
   sudo yum install postgresql-server postgresql-contrib
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   ```

2. **Create Database**
   ```bash
   # Switch to postgres user
   sudo -u postgres psql

   # Create database
   CREATE DATABASE clinical_assistant;

   # Exit
   \q
   ```

## Manual Redis Setup

### Windows

1. **Download Redis**
   - Option 1: Use WSL2 with Redis
   - Option 2: Use Docker: `docker run -d -p 6379:6379 redis:7-alpine`
   - Option 3: Use Memurai (Windows Redis alternative): https://www.memurai.com/

2. **Start Redis**
   ```powershell
   # If using Docker
   docker run -d -p 6379:6379 --name redis redis:7-alpine
   ```

### Linux/Mac

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS (Homebrew)
brew install redis
brew services start redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

## Configuration

### Update .env File

After setting up PostgreSQL and Redis, update your `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_assistant

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Important**: Replace `postgres:postgres` with your actual PostgreSQL username and password if different.

### Test Connection

```bash
# Test PostgreSQL connection
python scripts/init_db.py

# Test Redis connection
python -c "import redis; r = redis.Redis(); print('Redis connected:', r.ping())"
```

## Troubleshooting

### Connection Refused Error

**Error**: `ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection`

**Solutions**:

1. **Check if PostgreSQL is running**
   ```powershell
   # Windows
   Get-Service postgresql*

   # Linux/Mac
   sudo systemctl status postgresql
   # or
   ps aux | grep postgres
   ```

2. **Start PostgreSQL service**
   ```powershell
   # Windows
   Start-Service postgresql-x64-15

   # Linux/Mac
   sudo systemctl start postgresql
   # or
   sudo service postgresql start
   ```

3. **Check PostgreSQL port**
   ```bash
   # Check if port 5432 is listening
   netstat -an | findstr 5432  # Windows
   netstat -an | grep 5432     # Linux/Mac
   ```

4. **Verify connection string**
   - Check `.env` file has correct `DATABASE_URL`
   - Format: `postgresql+asyncpg://user:password@host:port/database`
   - Default: `postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_assistant`

### Docker Compose Issues

**Port already in use**:
```bash
# Check what's using the port
netstat -ano | findstr 5432  # Windows
lsof -i :5432                # Linux/Mac

# Stop conflicting service or change port in docker-compose.yml
```

**Container won't start**:
```bash
# Check logs
docker-compose logs postgres

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

### Database Already Exists

If you see "database already exists" error:
```bash
# Connect to PostgreSQL
psql -U postgres

# Drop and recreate (WARNING: deletes all data)
DROP DATABASE clinical_assistant;
CREATE DATABASE clinical_assistant;
```

## Next Steps

After setting up the database:

1. **Initialize database schema**:
   ```bash
   python scripts/init_db.py
   ```

2. **Create migrations**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

3. **Apply migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Verify tables created**:
   ```bash
   psql -U postgres -d clinical_assistant -c "\dt"
   ```

## Production Considerations

For production deployments:

1. **Use strong passwords**
   - Change default `postgres` password
   - Use environment variables for credentials

2. **Enable SSL**
   - Update `DATABASE_URL` to use SSL: `postgresql+asyncpg://...?ssl=require`

3. **Backup strategy**
   - Set up regular PostgreSQL backups
   - Use `pg_dump` for backups

4. **Connection pooling**
   - Adjust `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW` in `.env`
   - Monitor connection usage

5. **Redis persistence**
   - Configure Redis persistence (RDB or AOF)
   - Set up Redis replication for high availability

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

