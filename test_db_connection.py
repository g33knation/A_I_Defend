import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user="postgres",
            password="changeit",
            host="localhost",
            port=5432,
            database="defense"
        )
        print("✅ Successfully connected to the database!")
        
        # Test a simple query
        version = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {version}")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")

# Run the test
asyncio.get_event_loop().run_until_complete(test_connection())
