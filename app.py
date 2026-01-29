from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def sse(data: dict):
    return f"data: {json.dumps(data)}\n\n"

def ping():
    return ": keep-alive\n\n"

# ✅ REQUIRED: HEAD handler for OpenAI
@app.head("/")
async def head_root():
    return Response(
        status_code=200,
        headers={"Content-Type": "text/event-stream"}
    )

# ✅ REQUIRED: ROOT MUST BE SSE
@app.get("/")
async def root():
    async def stream():
        # Immediate byte flush (CRITICAL)
        yield ping()

        # MCP handshake response
        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
                "capabilities": {
                    "tools": {
                        "say_hello": {
                            "description": "Say hello to someone",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    }
                                },
                                "required": ["name"]
                            }
                        }
                    }
                }
            }
        })

        # Signal completion
        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

        # Keep stream alive
        while True:
            await asyncio.sleep(15)
            yield ping()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# ✅ Tool execution endpoint (OpenAI WILL call this)
@app.post("/")
async def call_tool(request: Request):
    payload = await request.json()
    tool = payload.get("params", {}).get("name")
    args = payload.get("params", {}).get("arguments", {})
    req_id = payload.get("id", str(uuid.uuid4()))

    async def stream():
        if tool == "say_hello":
            name = args.get("name", "there")
            yield sse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Hello {name}! 👋"
                        }
                    ]
                }
            })
        else:
            yield sse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": "Tool not found"
                }
            })

        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

        while True:
            await asyncio.sleep(15)
            yield ping()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
