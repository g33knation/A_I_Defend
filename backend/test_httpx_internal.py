import httpx
import asyncio
import os

async def test_ollama():
    url = "http://model-server:11434/api/tags"
    print(f"Testing URL: {url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            print(f"Status: {resp.status_code}")
            print(f"Content: {resp.text[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
