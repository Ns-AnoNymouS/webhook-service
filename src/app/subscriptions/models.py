import logging
from typing import Optional, List

from ..cache import (
    get_cached_subscription,
    set_cached_subscription,
    invalidate_cached_subscription,
)
from ..database import db  # motor client

# Initialize logger
logger = logging.getLogger(__name__)
collection = db.subscriptions


async def create_subscription(data: dict):
    """
    Create a new subscription by inserting it into the database.

    Args:
        data (dict): The subscription data to insert.
    """
    await collection.insert_one(data)
    # Cache the new subscription
    await set_cached_subscription(str(data["_id"]), data)
    logger.info(f"Created and cached subscription with ID {data['_id']}.")


async def delete_subscription(sub_id: str):
    """
    Delete a subscription from the database and invalidate the cache.

    Args:
        sub_id (str): The unique ID of the subscription to delete.
    """
    await collection.delete_one({"_id": sub_id})
    # Invalidate the cache
    await invalidate_cached_subscription(sub_id)
    logger.info(f"Deleted subscription with ID {sub_id} and invalidated cache.")


async def get_subscription(
    sub_id: str, event_type: Optional[List[str]] = None
) -> Optional[dict]:
    """
    Retrieve a subscription from the database or cache.

    Args:
        sub_id (str): The unique ID of the subscription.
        event_type (Optional[List[str]], optional): List of event types to filter subscriptions. Defaults to None.

    Returns:
        Optional[dict]: The subscription if found, otherwise None.
    """
    # Try fetching from the cache first
    cached_data = await get_cached_subscription(sub_id)
    if cached_data:
        logger.info(f"Cache hit for subscription ID {sub_id}.")
        return cached_data

    # If not in cache, fetch from the database
    query = {"_id": sub_id}
    if event_type:
        query["event_types"] = {"$in": event_type}

    subscription = await collection.find_one(query)

    # Cache the result for future access
    if subscription:
        await set_cached_subscription(sub_id, subscription)
        logger.info(
            f"Cache miss for subscription ID {sub_id}, fetched from DB and cached."
        )

    return subscription


async def list_subscriptions() -> list:
    """
    List all subscriptions from the database.

    Returns:
        list: A list of all subscriptions.
    """
    cursor = collection.find({})
    return await cursor.to_list(length=100)


async def update_subscription(sub_id: str, data: dict):
    """
    Update an existing subscription in the database with the provided changes
    and refresh the cache.

    Args:
        sub_id (str): The unique ID of the subscription to update.
        data (dict): The fields to update in the subscription.
    """
    # Fetch the current subscription
    subscription = await collection.find_one({"_id": sub_id})
    if not subscription:
        logger.error(f"Subscription with ID {sub_id} not found for update.")
        return None

    # Merge the existing data with the updated data, prioritizing the updated values
    updated_subscription = {**subscription, **data}

    # Update only the modified fields in the database
    await collection.update_one({"_id": sub_id}, {"$set": data})

    # Cache the updated subscription (only modified fields)
    await set_cached_subscription(sub_id, updated_subscription)

    logger.info(f"Updated subscription with ID {sub_id} and cached the updated data.")
    return updated_subscription
