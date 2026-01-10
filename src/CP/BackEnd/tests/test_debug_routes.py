"""Debug test to see what routes are registered"""
import pytest


@pytest.mark.unit
def test_list_all_routes(client):
    """List all registered routes for debugging"""
    from main import app
    
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = list(route.methods) if route.methods else []
            print(f"{methods[0] if methods else 'N/A':6} {route.path}")
    print("=== END ROUTES ===\n")
    
    # Also test the specific endpoint
    response = client.get("/api/auth/google/login")
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    # This test always passes - just for debugging
    assert True
