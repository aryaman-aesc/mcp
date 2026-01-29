from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import json, uuid

app = FastAPI()

def sse(data):
    return f"data: {json.dumps(data)}\n\n"

# ---------------- ROOT (SSE, FINITE) ----------------
@app.get("/")
async def root():
    async def stream():
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

    return StreamingResponse(stream(), media_type="text/event-stream")

# ---------------- MCP HANDSHAKE ----------------
@app.get("/mcp")
async def mcp():
    async def stream():
        yield ":\n\n"
        yield sse({"jsonrpc": "2.0", "result": "ok"})
        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

    return StreamingResponse(stream(), media_type="text/event-stream")

# ---------------- DISCOVERY ----------------
@app.get("/.well-known/mcp.json")
async def well_known():
    return JSONResponse({
        "mcpServers": {
            "aira": {
                "url": "/mcp"
            }
        }
    })

# ---------------- TOOLS LIST ----------------
@app.get("/mcp/tools")
async def tools():
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
                        "description": "Fetch document",
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

    return StreamingResponse(stream(), media_type="text/event-stream")

# ---------------- TOOL CALL ----------------
@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    body = await request.json()
    name = body["params"]["name"]
    args = body["params"]["arguments"]
    rid = body.get("id", str(uuid.uuid4()))

    async def stream():
        yield ":\n\n"

        if name == "search":
            result = [{"id": "cand_1", "title": "Backend Engineer"}]
        else:
            result = {"id": args.get("id"), "content": "Candidate profile"}

        yield sse({
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result)
                }]
            }
        })

        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })

    return StreamingResponse(stream(), media_type="text/event-stream")
