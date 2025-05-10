from typing import Optional, List

from ..database import db  # motor client

collection = db.subscriptions

async def create_subscription(data: dict):
    await collection.insert_one(data)

async def delete_subscription(sub_id: str):
    await collection.delete_one({"_id": sub_id})
    
async def get_subscription(sub_id: str, event_type: Optional[List[str]] = None) -> Optional[dict]:
    query = {"_id": sub_id}
    
    # If event_type is provided, include a check for event_type in the subscription's event_types
    if event_type:
        query["event_types"] = {"$in": event_type}  # If event_type exists in the list of event_types

    return await collection.find_one(query)

async def list_subscriptions() -> list:
    cursor = collection.find({})
    return await cursor.to_list(length=100)

async def update_subscription(sub_id: str, data: dict):
    await collection.update_one({"_id": sub_id}, {"$set": data})
