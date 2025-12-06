try:
    import bcrypt
    print(f"bcrypt version: {bcrypt.__version__}")
    print("bcrypt imported successfully")
except Exception as e:
    print(f"Error importing bcrypt: {e}")
