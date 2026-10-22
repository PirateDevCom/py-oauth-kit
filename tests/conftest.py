from collections.abc import Callable
from typing import Any

import httpx
import pytest

Route = Callable[[httpx.Request], httpx.Response]


class MockAPI:
    """Fake provider API: serves registered routes and records requests.

    Attributes:
        requests (list[httpx.Request]): Requests sent, in order.
        client (httpx.Client): Client to pass to providers.
    """

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], Route | Exception] = {}
        self.requests: list[httpx.Request] = []
        self.client = httpx.Client(transport=httpx.MockTransport(self._handle))

    def add(
        self,
        method: str,
        url: str,
        *,
        status: int = 200,
        json: Any = None,
        text: str | None = None,
    ) -> None:
        """Register a response for a URL, ignoring its query string.

        Args:
            method (str): HTTP method, e.g. ``"GET"``.
            url (str): URL without query string.
            status (int): Response status code.
            json (Any): JSON body. Ignored if ``text`` is given.
            text (str | None): Raw body.
        """

        def route(request: httpx.Request) -> httpx.Response:
            if text is not None:
                return httpx.Response(status, text=text)
            return httpx.Response(status, json=json)

        self._routes[(method, url)] = route

    def fail(self, method: str, url: str, exc: Exception) -> None:
        """Make requests to a URL raise ``exc``, like a network error."""
        self._routes[(method, url)] = exc

    def count(self, url: str) -> int:
        """Return how many requests were sent to a URL."""
        return sum(1 for r in self.requests if str(r.url.copy_with(query=None)) == url)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = (request.method, str(request.url.copy_with(query=None)))
        route = self._routes.get(key)
        if route is None:
            raise AssertionError(f"Unexpected request: {key}")
        if isinstance(route, Exception):
            raise route
        return route(request)


@pytest.fixture
def api() -> MockAPI:
    return MockAPI()
