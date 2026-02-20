
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp", "--browserUrl", "http://127.0.0.1:56991"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n🔄 REFRESHING PAGE...")
            try:
                # evaluate_script to reload
                await session.call_tool("evaluate_script", arguments={
                    "function": "() => { window.location.reload() }"
                })
                print("Wait 5s for reload...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Reload failed: {e}")

            print("\n🔍 FETCHING CONSOLE LOGS...")
            try:
                result = await session.call_tool("list_console_messages", arguments={})
                if result.isError:
                    print(f"Error: {result.content[0].text}")
                else:
                    for content in result.content:
                        print(content.text)
            except Exception as e:
                print(f"Exception calling tool: {e}")
            
            print("\n👁️ CHECKING DOM...")
            try:
                dom = await session.call_tool("evaluate_script", arguments={
                    "function": "() => { return document.body.innerText.substring(0, 500) }"
                })
                for content in dom.content:
                    print(content.text)
            except Exception as e:
                print(f"DOM check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
