"""Protocol definitions for asynchronous HTTP client and response interfaces."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AsyncHTTPResponse(Protocol):
    """Protocol for asynchronous HTTP response objects.

    Defines the required interface for HTTP response objects used with asynchronous HTTP clients.
    """

    status: int
    async def json(self) -> Any:
        """Return the response body parsed as JSON."""
        ...
    async def text(self) -> str:
        """Return the response body as a string."""
        ...
    def raise_for_status(self) -> None:
        """Raise an exception if the HTTP response status indicates an error."""
        ...
    async def __aenter__(self) -> AsyncHTTPResponse:
        """Enter the runtime context related to this object."""
        ...
    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Exit the runtime context related to this object."""
        ...

@runtime_checkable
class AsyncHTTPClient(Protocol):
    """Protocol for asynchronous HTTP client objects.

    Defines the required interface for HTTP client objects that support asynchronous HTTP methods.
    """

    def get(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Send an asynchronous HTTP GET request.

        Args:
            url (str): The URL to send the GET request to.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            AsyncHTTPResponse: The response object for the request.
        """
        ...
    def post(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Send an asynchronous HTTP POST request.

        Args:
            url (str): The URL to send the POST request to.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            AsyncHTTPResponse: The response object for the request.
        """
        ...
    def put(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Send an asynchronous HTTP PUT request.

        Args:
            url (str): The URL to send the PUT request to.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            AsyncHTTPResponse: The response object for the request.
        """
        ...
    def delete(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Send an asynchronous HTTP DELETE request.

        Args:
            url (str): The URL to send the DELETE request to.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            AsyncHTTPResponse: The response object for the request.
        """
        ...
