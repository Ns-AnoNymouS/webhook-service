from fastapi import HTTPException

def bad_request(message="Bad request"):
    raise HTTPException(status_code=400, detail=message)

def not_found(message="Not found"):
    raise HTTPException(status_code=404, detail=message)