import asyncio
import asyncpg
import os

async def check():
    db_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {db_url}")
    try:
        conn = await asyncpg.connect(db_url)
        print("Connected successfully!")
        
        # Read init.sql
        with open('/app/init.sql', 'r') as f:
            sql = f.read()
            
        print("Executing init.sql...")
        await conn.execute(sql)
        print("Schema initialized!")

        rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Tables:", [r['table_name'] for r in rows])
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
