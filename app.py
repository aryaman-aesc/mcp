from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json, uuid

app = FastAPI()

SSE_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

def sse(obj):
    return f"data: {json.dumps(obj)}\n\n"

# -------------------------------------------------
# ROOT — MUST BE SSE
# -------------------------------------------------
@app.get("/")
async def root():
    async def stream():
        # flush immediately
        yield ":ok\n\n"

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

    return StreamingResponse(stream(), headers=SSE_HEADERS)

# -------------------------------------------------
# MCP HANDSHAKE
# -------------------------------------------------
@app.get("/mcp")
async def mcp():
    async def stream():
        yield ":ok\n\n"
        yield sse({"jsonrpc": "2.0", "result": "ok"})
        yield sse({"jsonrpc": "2.0", "method": "notifications/complete"})

    return StreamingResponse(stream(), headers=SSE_HEADERS)

# -------------------------------------------------
# TOOL DISCOVERY
# -------------------------------------------------
@app.get("/mcp/tools")
async def tools():
    async def stream():
        yield ":ok\n\n"

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
                        "description": "Fetch AIRA document",
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

        yield sse({"jsonrpc": "2.0", "method": "notifications/complete"})

    return StreamingResponse(stream(), headers=SSE_HEADERS)

# -------------------------------------------------
# TOOL EXECUTION
# -------------------------------------------------
@app.post("/mcp/tools/call")
async def call_tool(req: Request):
    body = await req.json()
    name = body["params"]["name"]
    args = body["params"]["arguments"]
    rid = body.get("id", str(uuid.uuid4()))

    async def stream():
        yield ":ok\n\n"

        if name == "search":
            payload = [{"id": "cand_1", "title": "Backend Engineer"}]
        else:
            payload = {"id": args.get("id"), "text": "Candidate profile"}

        yield sse({
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "content": [{
                    "type": "text",
                    "text": json.dumps(payload)
                }]
            }
        })

        yield sse({"jsonrpc": "2.0", "method": "notifications/complete"})

    return StreamingResponse(stream(), headers=SSE_HEADERS)
