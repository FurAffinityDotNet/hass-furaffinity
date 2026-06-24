"""Fur Affinity Status API client."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 60


class FurAffinityStatusError(Exception):
    """Base error for the Fur Affinity Status integration."""


class FurAffinityStatusApi:
    """Client for the Fur Affinity status API with rate limiting.

    The public Fur Affinity status API limits callers to 60 requests per
    minute. This client enforces that limit on all HTTP requests by tracking
    a sliding window of recent request timestamps. Calls that would exceed
    the limit wait (asynchronously) until a slot is available, or raise
    :class:`FurAffinityStatusError` if ``bypass_when_limited`` is False and
    no slot will be free soon.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    async def _acquire_slot(self, timeout: float = 30.0) -> None:
        """Acquire a rate-limit slot, waiting if necessary."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        async with self._lock:
            while True:
                now = loop.time()
                cutoff = now - RATE_LIMIT_WINDOW_SECONDS
                self._request_times = [t for t in self._request_times if t > cutoff]

                if len(self._request_times) < RATE_LIMIT_MAX_REQUESTS:
                    self._request_times.append(now)
                    return

                if loop.time() >= deadline:
                    raise FurAffinityStatusError(
                        "Rate limit of 60 requests per minute exceeded"
                    )

                sleep_for = self._request_times[0] + RATE_LIMIT_WINDOW_SECONDS - loop.time()
                sleep_for = max(0.05, min(sleep_for, 1.0))
                _LOGGER.debug(
                    "Rate limit reached, sleeping %.2fs before next request",
                    sleep_for,
                )
                await asyncio.sleep(sleep_for)

    def release_slot(self) -> None:
        """Release the most recent rate-limit slot.

        Should be called when a request fails or times out, so it does not
        count against the quota.
        """
        if self._request_times:
            self._request_times.pop()

    @property
    def requests_in_window(self) -> int:
        """Return how many requests have been made in the current window."""
        now = time.monotonic()
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        return sum(1 for t in self._request_times if t > cutoff)

    async def async_get_status(self) -> dict[str, Any]:
        """Fetch the current status payload from the API."""
        await self._acquire_slot()
        try:
            async with asyncio.timeout(15):
                async with self._session.get(API_URL) as response:
                    if response.status == 429:
                        self.release_slot()
                        raise FurAffinityStatusError(
                            "API returned HTTP 429: rate limited"
                        )
                    if response.status != 200:
                        self.release_slot()
                        raise FurAffinityStatusError(
                            f"Unexpected status from API: {response.status}"
                        )
                    return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            self.release_slot()
            raise FurAffinityStatusError(
                f"Error communicating with API: {err}"
            ) from err
