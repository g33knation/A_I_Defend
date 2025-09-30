from setuptools import setup, find_packages

setup(
    name="a_i_defend",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # Add your project's dependencies here
        'fastapi',
        'uvicorn',
        'httpx',
        'python-multipart',
        'python-jose[cryptography]',
        'passlib[bcrypt]',
        'sqlalchemy',
        'psycopg2-binary',
        'pydantic',
        'python-multipart',
        'python-dotenv',
        'yara-python',
        'pyyaml',
        'python-magic',
        'aiofiles',
    ],
)
