import asyncpg
import asyncio
import os

async def init_db():
    # Database configuration - Match with docker-compose.yml
    DB_USER = "postgres"
    DB_PASSWORD = "changeit"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "defense"

    conn = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    try:
        # Create events table
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            type TEXT NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)

        # Create detections table
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source TEXT NOT NULL,
            details JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)

        # Create detection_feedback table
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS detection_feedback (
            id SERIAL PRIMARY KEY,
            detection_id INTEGER REFERENCES detections(id) ON DELETE CASCADE,
            feedback TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)

        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init_db())
