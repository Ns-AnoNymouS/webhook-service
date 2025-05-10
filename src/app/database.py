from motor.motor_asyncio import AsyncIOMotorClient

from .config import DB_NAME, MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
