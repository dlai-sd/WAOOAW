"""Debug test to see what routes are registered"""
import pytest


@pytest.mark.unit
def test_list_all_routes(client):
    """List all registered routes for debugging"""
    from main import app
    
    # Collect route info
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = list(route.methods) if route.methods else []
            routes.append(f"{methods[0] if methods else 'N/A':6} {route.path}")
    
    # Test the specific endpoint
    response = client.get("/api/auth/google/login")
    
    # If it fails, show all routes in the assertion error
    assert response.status_code != 404, (
        f"Expected /api/auth/google/login to exist but got 404.\n"
        f"Registered routes ({len(routes)}):\n" + "\n".join(routes)
    )
