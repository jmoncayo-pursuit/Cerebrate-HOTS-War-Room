import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp", "--auto-connect", "--channel=canary"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(json.dumps([t.model_dump() for t in tools.tools], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
