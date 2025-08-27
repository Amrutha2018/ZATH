# db/connection.py

import asyncpg
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "zathdb")
DB_USER = os.getenv("DB_USER", "zathuser")
DB_PASS = os.getenv("DB_PASS", "zathpass")

_connection_pool = None

async def init_db_pool():
    global _connection_pool
    _connection_pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        min_size=1,
        max_size=10,
    )

async def close_db_pool():
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()

async def get_pool():
    return _connection_pool
