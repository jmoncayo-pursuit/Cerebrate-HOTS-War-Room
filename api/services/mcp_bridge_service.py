import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from api.logger import ColoredLogger
import json

class MCPBridgeService:
    def __init__(self):
        self.session = None
        self._connected = False
        self._loop = None
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "chrome-devtools-mcp", "--auto-connect"],
            env=None
        )

    def start_background(self):
        """Start the MCP bridge in a background thread."""
        import threading
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            loop.run_until_complete(self.connect_forever())

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def connect_forever(self):
        """Maintain a persistent connection to the MCP server."""
        while True:
            try:
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        self.session = session
                        await self.session.initialize()
                        self._connected = True
                        ColoredLogger.success("Neural Link: Connected to Chrome DevTools MCP Server", "MCP")
                        
                        # Keep alive loop
                        while self._connected:
                            await asyncio.sleep(5)
                            # Could do a heartbeat check here
            except Exception as e:
                self._connected = False
                ColoredLogger.error(f"Neural Link Connection Lost: {e}. Retrying in 10s...", "MCP")
                await asyncio.sleep(10)

    async def get_dom_snapshot(self):
        """Fetch a snapshot of the current DOM."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        
        try:
            # MCP Tool call to 'get_dom_snapshot' or similar
            # We list tools first to find the exact name
            tools = await self.session.list_tools()
            # Find the tool that provides DOM info
            # For @modelcontextprotocol/server-chrome-devtools, tool name might be 'capture_console_logs', 'inspect_dom', etc.
            # Base implementation:
            result = await self.session.call_tool("inspect_dom", arguments={})
            return result
        except Exception as e:
            return {"error": str(e)}

    async def get_console_logs(self):
        """Fetch recent console logs."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        
        try:
            result = await self.session.call_tool("get_console_logs", arguments={})
            return result
        except Exception as e:
            return {"error": str(e)}

    def is_healthy(self):
        return self._connected

# Singleton instance
mcp_bridge = MCPBridgeService()
