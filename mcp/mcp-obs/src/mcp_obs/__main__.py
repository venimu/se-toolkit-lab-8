"""Entry point for the MCP observability server."""

import asyncio

from mcp_obs.server import server


def main() -> None:
    """Run the MCP observability server."""
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
