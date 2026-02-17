"""API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello, World!"}


@router.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get an item by ID."""
    return {"item_id": item_id}
