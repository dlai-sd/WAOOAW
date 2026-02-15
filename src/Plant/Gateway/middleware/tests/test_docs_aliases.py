from fastapi.testclient import TestClient

from main import app


def test_api_openapi_alias_matches_openapi() -> None:
    with TestClient(app) as client:
        r1 = client.get("/openapi.json", headers={"host": "example.com"})
        r2 = client.get("/api/openapi.json", headers={"host": "example.com"})

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()


def test_api_docs_alias_serves_html() -> None:
    with TestClient(app) as client:
        r = client.get("/api/docs")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")


def test_swagger_dark_css_served() -> None:
    with TestClient(app) as client:
        r = client.get("/swagger-ui-dark.css")
        assert r.status_code == 200
        assert "text/css" in r.headers.get("content-type", "")
        assert ":root" in r.text
