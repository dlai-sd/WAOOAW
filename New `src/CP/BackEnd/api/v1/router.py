from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1")

# Define your routes here
@api_v1_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Add more routes as needed
