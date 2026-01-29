from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json, asyncio, uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SSE helpers ----------------
def sse(data):
    return f"data: {json.dumps(data)}\n\n"

def ping():
    return ": keep-alive\n\n"

# ---------------- ROOT ----------------
@app.get("/")
async def root():
    return {"status": "ok"}

# ---------------- MCP HANDSHAKE (CRITICAL) ----------------
@app.get("/mcp")
async def mcp_handshake():
    async def stream():
        # MUST yield immediately
        yield ":\n\n"

        yield sse({
            "jsonrpc": "2.0",
            "result": {
                "name": "AIRA MCP Connector",
                "version": "1.0.0",
                "mcp_version": "2024-11-05"
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
        }
    )

# ---------------- MCP DISCOVERY ----------------
@app.get("/.well-known/mcp.json")
async def well_known():
    return {
        "mcpServers": {
            "aira": {
                "url": "/mcp"
            }
        }
    }

# ---------------- TOOLS LIST ----------------
@app.get("/mcp/tools")
async def list_tools():
    async def stream():
        yield ":\n\n"

        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search AIRA dataset",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "fetch",
                        "description": "Fetch document by id",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"}
                            },
                            "required": ["id"]
                        }
                    }
                ]
            }
        })

        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

        while True:
            await asyncio.sleep(15)
            yield ping()

    return StreamingResponse(stream(), media_type="text/event-stream")

# ---------------- TOOL CALL ----------------
@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    payload = await request.json()
    name = payload["params"]["name"]
    args = payload["params"]["arguments"]
    rid = payload.get("id", str(uuid.uuid4()))

    async def stream():
        yield ":\n\n"

        if name == "search":
            yield sse({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps([
                            {"id": "cand_1", "title": "Backend Engineer"}
                        ])
                    }]
                }
            })

        elif name == "fetch":
            yield sse({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": "Candidate: Backend Engineer, Node.js, 5 yrs"
                    }]
                }
            })

        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

        while True:
            await asyncio.sleep(15)
            yield ping()

    return StreamingResponse(stream(), media_type="text/event-stream")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
