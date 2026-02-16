import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import time
import os
import re

async def run_mcp_command(session, tool_name, arguments):
    print(f"Calling tool: {tool_name} with args: {arguments}")
    result = await session.call_tool(tool_name, arguments=arguments)
    if result.isError:
        error_msg = result.content[0].text if result.content else "Unknown error"
        raise Exception(f"Tool {tool_name} failed: {error_msg}")
    return result

async def main():
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "chrome-devtools-mcp", "--browserUrl", "http://127.0.0.1:56991"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. List pages
            pages_res = await run_mcp_command(session, "list_pages", {})
            raw_text = pages_res.content[0].text
            page_matches = re.findall(r'(\d+):\s+(https?://\S+)', raw_text)
            pages = [{"id": int(m[0]), "url": m[1]} for m in page_matches]
            
            target_page = next((p for p in pages if "localhost:5173" in p["url"]), None)
            if not target_page:
                print("Opening localhost:5173...")
                await run_mcp_command(session, "new_page", {"url": "http://localhost:5173"})
                await asyncio.sleep(2)
                pages_res = await run_mcp_command(session, "list_pages", {})
                page_matches = re.findall(r'(\d+):\s+(https?://\S+)', pages_res.content[0].text)
                pages = [{"id": int(m[0]), "url": m[1]} for m in page_matches]
                target_page = next((p for p in pages if "localhost:5173" in p["url"]), None)

            await run_mcp_command(session, "select_page", {"pageId": target_page["id"], "bringToFront": True})
            
            # 2. Click Archive tab
            snapshot_res = await run_mcp_command(session, "take_snapshot", {})
            snapshot = snapshot_res.content[0].text
            
            archive_uid = next((m.group(1) for line in snapshot.split('\n') if "ARCHIVE" in line for m in [re.search(r'uid=([\d_]+)', line)] if m), None)
            if archive_uid:
                print(f"Clicking Archive tab {archive_uid}")
                await run_mcp_command(session, "click", {"uid": archive_uid})
                await asyncio.sleep(2)

            # 3. Find and click match
            snapshot_res = await run_mcp_command(session, "take_snapshot", {})
            snapshot = snapshot_res.content[0].text
            
            match_uid = next((m.group(1) for line in snapshot.split('\n') if "2ba9403cd33f83ff" in line for m in [re.search(r'uid=([\d_]+)', line)] if m), None)
            if not match_uid:
                # Try search if match not visible
                search_uid = next((m.group(1) for line in snapshot.split('\n') if "search" in line.lower() for m in [re.search(r'uid=([\d_]+)', line)] if m), None)
                if search_uid:
                    print(f"Searching for match via {search_uid}")
                    await run_mcp_command(session, "fill", {"uid": search_uid, "value": "2ba9403cd33f83ff"})
                    await asyncio.sleep(2)
                    snapshot_res = await run_mcp_command(session, "take_snapshot", {})
                    snapshot = snapshot_res.content[0].text
                    match_uid = next((m.group(1) for line in snapshot.split('\n') if "2ba9403cd33f83ff" in line for m in [re.search(r'uid=([\d_]+)', line)] if m), None)

            if not match_uid:
                # Fallback to Hanamura
                match_uid = next((m.group(1) for line in snapshot.split('\n') if "Hanamura" in line for m in [re.search(r'uid=([\d_]+)', line)] if m), None)

            if match_uid:
                print(f"Clicking Match {match_uid}")
                await run_mcp_command(session, "click", {"uid": match_uid})
                await asyncio.sleep(2)
            else:
                print("FAILED to find match.")

            # 4. Click Analysis
            snapshot_res = await run_mcp_command(session, "take_snapshot", {})
            snapshot = snapshot_res.content[0].text
            analysis_uid = next((m.group(1) for line in snapshot.split('\n') if "Analysis" in line for m in [re.search(r'uid=([\d_]+)', line)] if m), None)
            if analysis_uid:
                print(f"Clicking Analysis {analysis_uid}")
                await run_mcp_command(session, "click", {"uid": analysis_uid})
                await asyncio.sleep(1)

            # 5. Verify and Screenshot
            snapshot_res = await run_mcp_command(session, "take_snapshot", {})
            snapshot = snapshot_res.content[0].text
            
            results = {
                "Kill Streak": "Kill Streak" in snapshot,
                "Mercenary Camps": "Mercenary Camps" in snapshot,
                "Downtime": "Downtime" in snapshot,
                "Minion XP": "Minion XP" in snapshot
            }
            print(f"Verification Results: {results}")
            
            screenshot_path = os.path.abspath("analysis_ui_final.png")
            await run_mcp_command(session, "take_screenshot", {"filePath": screenshot_path})
            print(f"Final screenshot: {screenshot_path}")

if __name__ == "__main__":
    asyncio.run(main())
