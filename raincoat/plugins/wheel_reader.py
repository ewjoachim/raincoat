from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import functools
import io
import logging
import zipfile

import httpx

logger = logging.getLogger(__name__)


class HTTPRangeReader(io.RawIOBase):
    """A file-like object that uses HTTP Range requests to read parts of a remote file."""

    def __init__(self, *, url: str, client: httpx.Client):
        super().__init__()
        self.url = url
        self.pos = 0
        self.size: int | None = None
        self.client = client
        self.bytes_read = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def close(self) -> None:
        logger.debug(
            "Closing HTTPRangeReader. "
            f"Total bytes read: {self.bytes_read} bytes in this session",
        )
        self.client.close()
        super().close()

    def init_size(self) -> None:
        """Get the total file size using HEAD request."""
        if self.size is None:
            logger.debug(f"HEAD request to {self.url} to get file size")
            response = self.client.head(self.url)
            response.raise_for_status()
            self.size = int(response.headers["content-length"])
            logger.debug(f"File size: {self.size} bytes")

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        self.init_size()
        assert self.size is not None

        old_pos = self.pos
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.size + offset
        logger.debug(
            f"Seeking from {old_pos} to {self.pos} "
            f"(whence={whence!r}, offset={offset})",
        )
        return self.pos

    def tell(self) -> int:
        return self.pos

    def _request_range(self, *, size: int) -> bytes:
        """Make an HTTP range request for the specified size from current position."""
        http_range = f"bytes={self.pos}-{self.pos + size - 1}"
        logger.debug(f"HTTP Range request: {http_range} ({size} bytes)")

        response = self.client.get(
            url=self.url,
            headers={"Range": http_range},
        )
        response.raise_for_status()
        return response.content

    def readinto(self, buffer: memoryview) -> int:
        """Read bytes into a pre-allocated buffer."""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        self.init_size()
        assert self.size is not None

        if self.pos >= self.size:
            return 0  # EOF

        size = len(buffer)
        data = self._request_range(size=size)
        size = len(data)
        buffer[:size] = data
        self.pos += size
        self.bytes_read += size
        return size

    def read(self, size: int = -1) -> bytes:
        """Read size bytes from current position."""
        if self.closed:
            raise ValueError("I/O operation on closed file")

        self.init_size()
        assert self.size is not None

        if size == -1:
            size = self.size - self.pos

        if size == 0:
            return b""

        data = self._request_range(size=size)
        data_size = len(data)
        self.pos += data_size
        self.bytes_read += data_size
        return data


def sync_read_file_from_wheel(
    *, url: str, path: str, client: httpx.Client | None = None
) -> str:
    """
    Read a single file from a wheel without downloading the entire file.

    Uses ZipFile with a custom file-like object that performs HTTP Range requests.

    This is a synchronous function, because ZipFile does not support async I/O.
    See `read_file_from_wheel` for the async version.

    Parameters
    ----------
    url : str
        URL of the wheel file
    path : str
        Path to the file within the wheel to read
    client : httpx.Client | None
        Optional HTTP client to use for requests. If not provided, a new client
        will be created. The client will be closed when done if it was created
        internally.

    Returns
    -------
    str
        The contents of the file
    """
    with contextlib.ExitStack() as stack:
        if client is None:
            client = stack.enter_context(httpx.Client())
        range_file = stack.enter_context(HTTPRangeReader(url=url, client=client))
        zf = stack.enter_context(zipfile.ZipFile(file=range_file))
        return zf.read(name=path).decode(encoding="utf-8")


async def read_file_from_wheel(
    *,
    url: str,
    path: str,
    executor: concurrent.futures.ThreadPoolExecutor | None = None,
) -> str:
    """
    This is an async wrapper around sync_read_file_from_wheel that runs it in a thread.
    """
    call = functools.partial(sync_read_file_from_wheel, url=url, path=path)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor=executor, func=call)
