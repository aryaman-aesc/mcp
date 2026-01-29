from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()

# ---- MCP SSE STREAM ----
@app.get("/")
async def mcp_root(request: Request):
    async def event_generator():
        # 1️⃣ MCP initialization
        init_event = {
            "type": "initialize",
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "aira-mcp",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": True
            }
        }
        yield f"data: {json.dumps(init_event)}\n\n"

        # 2️⃣ Tool registration
        tools_event = {
            "type": "tools/list",
            "tools": [
                {
                    "name": "get_candidates",
                    "description": "Fetch candidates from AIRA dataset",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string"
                            }
                        }
                    }
                }
            ]
        }
        yield f"data: {json.dumps(tools_event)}\n\n"

        # 3️⃣ Keep connection alive
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(15)
            yield ":\n\n"  # SSE heartbeat

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
