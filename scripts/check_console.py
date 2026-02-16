
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp", "--auto-connect", "--channel=canary", "--browserUrl", "http://127.0.0.1:56991"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. List console messages
            print("--- CONSOLE LOGS ---")
            try:
                logs = await session.call_tool("list_console_messages", arguments={})
                for content in logs.content:
                    print(content.text)
            except Exception as e:
                print(f"Error fetching logs: {e}")
            
            # 2. Get DOM snapshot (briefly)
            print("\n--- DOM SUMMARY ---")
            try:
                dom = await session.call_tool("evaluate_script", arguments={
                    "function": "() => { return document.body.innerText.substring(0, 500) }"
                })
                for content in dom.content:
                    print(content.text)
            except Exception as e:
                print(f"Error fetching DOM: {e}")

if __name__ == "__main__":
    asyncio.run(main())
