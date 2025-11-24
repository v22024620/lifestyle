"""Basic import test to ensure app loads."""
from app.main import app


def test_health_route_exists() -> None:
    routes = {route.path for route in app.router.routes}
    assert "/health" in routes
