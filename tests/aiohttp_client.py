"""Real HTTP client implementation using aiohttp."""

from __future__ import annotations

from typing import Any

import aiohttp

from pynetro.http import AsyncHTTPResponse


class AiohttpResponse:
    """Adapter for aiohttp.ClientResponse to match AsyncHTTPResponse protocol."""

    def __init__(self, response: aiohttp.ClientResponse) -> None:
        """Initialize with aiohttp response."""
        self._response = response
        self.status = response.status

    async def json(self) -> Any:
        """Return JSON data from response."""
        return await self._response.json()

    async def text(self) -> str:
        """Return text data from response."""
        return await self._response.text()

    def raise_for_status(self) -> None:
        """Raise exception for HTTP errors."""
        self._response.raise_for_status()

    async def __aenter__(self) -> AiohttpResponse:
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        self._response.close()


class AiohttpClient:
    """Real HTTP client using aiohttp that implements AsyncHTTPClient protocol."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize with optional session."""
        self._session = session
        self._own_session = session is None

    async def __aenter__(self) -> AiohttpClient:
        """Context manager entry."""
        if self._own_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""
        if self._own_session and self._session:
            await self._session.close()

    def get(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Make GET request."""
        if not self._session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        # Adapt parameters for aiohttp
        aiohttp_kwargs = self._adapt_kwargs(kwargs)
        response = self._session.get(url, **aiohttp_kwargs)
        return AiohttpResponseContextManager(response)

    def post(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Make POST request."""
        if not self._session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        aiohttp_kwargs = self._adapt_kwargs(kwargs)
        response = self._session.post(url, **aiohttp_kwargs)
        return AiohttpResponseContextManager(response)

    def put(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Make PUT request."""
        if not self._session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        aiohttp_kwargs = self._adapt_kwargs(kwargs)
        response = self._session.put(url, **aiohttp_kwargs)
        return AiohttpResponseContextManager(response)

    def delete(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Make DELETE request."""
        if not self._session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        aiohttp_kwargs = self._adapt_kwargs(kwargs)
        response = self._session.delete(url, **aiohttp_kwargs)
        return AiohttpResponseContextManager(response)

    def _adapt_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Adapt generic HTTP kwargs to aiohttp format."""
        adapted = {}

        if "headers" in kwargs:
            adapted["headers"] = kwargs["headers"]

        if "params" in kwargs:
            adapted["params"] = kwargs["params"]

        if "timeout" in kwargs:
            # aiohttp utilise aiohttp.ClientTimeout
            adapted["timeout"] = aiohttp.ClientTimeout(total=kwargs["timeout"])

        if "json" in kwargs:
            adapted["json"] = kwargs["json"]

        if "data" in kwargs:
            adapted["data"] = kwargs["data"]

        return adapted


class AiohttpResponseContextManager:
    """Context manager wrapper for aiohttp response."""

    def __init__(self, response_coro) -> None:
        """Initialize with response coroutine."""
        self._response_coro = response_coro
        self._response = None

    async def __aenter__(self) -> AiohttpResponse:
        """Enter context and get response."""
        aiohttp_response = await self._response_coro.__aenter__()
        self._response = AiohttpResponse(aiohttp_response)
        return self._response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Exit context."""
        if self._response:
            await self._response.__aexit__(exc_type, exc, tb)
        await self._response_coro.__aexit__(exc_type, exc, tb)
