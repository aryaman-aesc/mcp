from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json, asyncio, uuid

app = FastAPI()

def sse(data):
    return f"data: {json.dumps(data)}\n\n"

def ping():
    return ": keep-alive\n\n"

@app.get("/")
async def root():
    return "MCP server alive"

@app.get("/mcp/tools")
async def list_tools():
    async def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
                "tools": [
                    {
                        "name": "say_hello",
                        "description": "Say hello",
                        "inputSchema": {
                            "type": "object",
                            "properties": { "name": {"type": "string"} },
                            "required": ["name"]
                        }
                    }
                ]
            }
        })
        while True:
            await asyncio.sleep(10)
            yield ping()
    return StreamingResponse(stream(), media_type="text/event-stream")

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    payload = await request.json()
    async def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": payload.get("id", str(uuid.uuid4())),
            "result": {
                "content": [
                    {"type": "text", "text": f"Hello, {payload['params']['arguments'].get('name','there')} 👋"}
                ]
            }
        })
        while True:
            await asyncio.sleep(10)
            yield ping()
    return StreamingResponse(stream(), media_type="text/event-stream")
