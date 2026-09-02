import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from config.settings import settings


class FilesystemMCP:
    """Read text files through the configured MCP filesystem server."""

    async def _read_async(self, path: Path) -> str:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server = StdioServerParameters(
            command=settings.MCP_FILESYSTEM_COMMAND,
            args=["-y", settings.MCP_FILESYSTEM_PACKAGE, str(settings.BASE_DIR)],
            env=os.environ.copy(),
        )
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("read_text_file", {"path": str(path.resolve())})
                for item in result.content:
                    text = getattr(item, "text", None)
                    if text is not None:
                        return text
        raise ValueError(f"MCP filesystem returned no text for {path}")

    def read_text_or_local(self, path: str | Path) -> str:
        path = Path(path)
        if not settings.MCP_FILESYSTEM_ENABLED:
            return path.read_text(encoding="utf-8", errors="ignore")
        try:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(self._read_async(path))
            with ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(lambda: asyncio.run(self._read_async(path))).result()
        except Exception:
            return path.read_text(encoding="utf-8", errors="ignore")