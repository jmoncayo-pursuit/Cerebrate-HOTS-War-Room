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
            args=["-y", "chrome-devtools-mcp", "--autoConnect"],
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
                ColoredLogger.error(f"Neural Link Linkage Failure: {e}", "MCP")
                ColoredLogger.warn("Manual Action Required: Ensure 'Remote Debugging' is enabled at chrome://inspect/#remote-debugging", "MCP")
                await asyncio.sleep(10)

    async def get_dom_snapshot(self):
        """Fetch a snapshot of the current DOM."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        
        try:
            # Use 'evaluate_script' with a proper function declaration
            # Schema requires a string that is a JS function declaration
            result = await self.session.call_tool("evaluate_script", arguments={
                "function": "() => { return document.documentElement.outerHTML }"
            })
            
            if result.isError:
                error_msg = result.content[0].text if result.content else "Unknown MCP Error"
                return {"error": f"MCP Tool Error: {error_msg}"}
                
            # Parse the content
            # The result is usually a JSON string wrapped in text
            if result.content:
                return {"dom": result.content[0].text}
            return {"dom": ""}
            
        except Exception as e:
            return {"error": str(e)}

    async def get_console_logs(self):
        """Fetch recent console logs."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        
        try:
            # Tool name: list_console_messages
            result = await self.session.call_tool("list_console_messages", arguments={})
            
            if result.isError:
                error_msg = result.content[0].text if result.content else "Unknown MCP Error"
                return {"error": f"MCP Tool Error: {error_msg}"}

            if result.content:
                return {"logs": result.content[0].text}
            return {"logs": []}
            
        except Exception as e:
            return {"error": str(e)}

    async def start_performance_trace(self):
        """Start a performance trace (requires Chrome >= 144)."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        try:
            # blog ref: reload=True, autoStop=True
            result = await self.session.call_tool("performance_start_trace", arguments={
                "reload": True,
                "autoStop": True
            })
            return result
        except Exception as e:
            return {"error": str(e)}

    async def get_performance_insights(self):
        """Analyze trace for performance insights."""
        if not self._connected or not self.session:
            return {"error": "Not connected to DevTools"}
        try:
            result = await self.session.call_tool("performance_analyze_insight", arguments={})
            return result
        except Exception as e:
            return {"error": str(e)}

    def is_healthy(self):
        return self._connected

# Singleton instance
mcp_bridge = MCPBridgeService()
