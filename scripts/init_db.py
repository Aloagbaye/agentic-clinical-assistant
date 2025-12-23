"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from agentic_clinical_assistant.config import settings


async def init_db() -> None:
    """Initialize database (create if doesn't exist)."""
    # Extract database name from URL
    db_url = settings.DATABASE_URL
    # For postgresql+asyncpg://user:pass@host:port/dbname
    if "+asyncpg" in db_url:
        db_url_clean = db_url.replace("+asyncpg", "")
    else:
        db_url_clean = db_url
    
    # Get database name (everything after last /)
    db_name = db_url_clean.split("/")[-1].split("?")[0]
    
    # Get base URL (without database name)
    base_url = "/".join(db_url_clean.split("/")[:-1])
    
    # Extract host and port for better error messages
    try:
        if "@" in base_url:
            host_part = base_url.split("@")[1].split("/")[0]
            host = host_part.split(":")[0] if ":" in host_part else host_part
        else:
            host = "localhost"
    except Exception:
        host = "unknown"
    
    print(f"Connecting to PostgreSQL server at {host}...")
    print(f"Database name: {db_name}")
    print()
    
    # Connect to postgres database to create target database
    # Use asyncpg for admin connection too
    admin_url = f"{base_url}/postgres"
    if "+asyncpg" not in admin_url and "postgresql://" in admin_url:
        admin_url = admin_url.replace("postgresql://", "postgresql+asyncpg://")
    
    admin_engine = create_async_engine(admin_url, echo=False)
    
    try:
        async with admin_engine.begin() as conn:
            # Check if database exists
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            )
            exists = result.scalar()
            
            if not exists:
                print(f"Creating database '{db_name}'...")
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"✓ Database '{db_name}' created successfully!")
            else:
                print(f"✓ Database '{db_name}' already exists.")
    except ConnectionRefusedError:
        print("✗ ERROR: Could not connect to PostgreSQL server.")
        print()
        print("PostgreSQL is not running or not accessible. Please:")
        print("  1. Start PostgreSQL service, OR")
        print("  2. Use Docker Compose: docker-compose up -d postgres")
        print("  3. Update DATABASE_URL in .env file if using different host/port")
        print()
        print(f"Attempted to connect to: {host}")
        raise
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        print()
        print("Please check:")
        print("  - PostgreSQL is installed and running")
        print("  - DATABASE_URL in .env is correct")
        print("  - Network connectivity to database server")
        raise
    finally:
        await admin_engine.dispose()
    
    # Test connection to target database
    print(f"\nTesting connection to '{db_name}'...")
    test_engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with test_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Connection successful!")
    except Exception as e:
        print(f"✗ ERROR: Could not connect to database '{db_name}': {e}")
        raise
    finally:
        await test_engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())

