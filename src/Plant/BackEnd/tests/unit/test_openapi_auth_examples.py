from fastapi.testclient import TestClient

from main import app


def test_openapi_description_contains_auth_examples_in_3_languages() -> None:
    client = TestClient(app)

    res = client.get("/openapi.json")
    assert res.status_code == 200

    spec = res.json()
    description = (((spec.get("info") or {}).get("description")) or "")

    assert "Mint an access token" in description
    assert "```bash" in description
    assert "```python" in description
    assert "```javascript" in description
