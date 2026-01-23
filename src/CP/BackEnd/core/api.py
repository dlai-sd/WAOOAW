"""
API versioning for the application
"""

from fastapi import APIRouter

router_v1 = APIRouter()
router_v2 = APIRouter()

@router_v1.get("/items/")
async def read_items():
    return [{"item_id": "Foo"}, {"item_id": "Bar"}]

@router_v2.get("/items/")
async def read_items_v2():
    return [{"item_id": "Foo", "description": "A Foo item"}, {"item_id": "Bar", "description": "A Bar item"}]
