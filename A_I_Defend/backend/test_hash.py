from passlib.context import CryptContext
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("Hashing 'admin123'...")
    hash = pwd_context.hash("admin123")
    print(f"Success: {hash}")
except Exception as e:
    print(f"Error: {e}")
