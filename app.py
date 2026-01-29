from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# SSE helpers
# -----------------------------
def sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

def ping() -> str:
    return ": keep-alive\n\n"

# -----------------------------
# Root (JSON is OK here)
# -----------------------------
@app.get("/")
async def root():
    return JSONResponse({
        "name": "AIRA MCP Connector",
        "version": "1.0.0",
        "mcp_version": "2024-11-05",
        "description": "Read-only MCP server for OpenAI Connectors",
        "capabilities": {
            "tools": {}
        }
    })

# -----------------------------
# MCP discovery
# -----------------------------
@app.get("/.well-known/mcp.json")
async def well_known():
    return JSONResponse({
        "mcpServers": {
            "aira": {
                "url": "/mcp"
            }
        }
    })

# -----------------------------
# Health
# -----------------------------
@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy"})

# -----------------------------
# MCP TOOLS LIST (SSE REQUIRED)
# -----------------------------
@app.get("/mcp/tools")
async def list_tools():
    async def stream():
        # 🔴 MUST yield immediately (forces SSE)
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
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "fetch",
                        "description": "Fetch a document by id",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Document ID"
                                }
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

    return StreamingResponse(
        stream(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )

# -----------------------------
# MCP TOOL CALL (SSE REQUIRED)
# -----------------------------
@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    try:
        payload = await request.json()
        tool_name = payload.get("params", {}).get("name")
        arguments = payload.get("params", {}).get("arguments", {})
        request_id = payload.get("id", str(uuid.uuid4()))

        async def stream():
            # 🔴 MUST yield immediately
            yield ":\n\n"

            if tool_name == "search":
                query = arguments.get("query", "")

                # TODO: replace with real AIRA search
                results = [
                    {
                        "id": "candidate_123",
                        "title": "Backend Engineer – Node.js",
                        "url": "aira://candidate/123"
                    },
                    {
                        "id": "jd_456",
                        "title": "Senior Backend Engineer JD",
                        "url": "aira://jd/456"
                    }
                ]

                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(results)
                            }
                        ]
                    }
                })

            elif tool_name == "fetch":
                doc_id = arguments.get("id")

                # TODO: replace with real AIRA fetch
                document = {
                    "id": doc_id,
                    "type": "candidate",
                    "content": (
                        "Candidate: John Doe\n"
                        "Role: Backend Engineer\n"
                        "Skills: Node.js, TypeScript, PostgreSQL\n"
                        "Experience: 5 years\n"
                        "Interview Summary: Strong system design and API skills."
                    )
                }

                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(document)
                            }
                        ]
                    }
                })

            else:
                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
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
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# CORS preflight
# -----------------------------
@app.options("/mcp/tools")
async def options_tools():
    return JSONResponse({}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })

@app.options("/mcp/tools/call")
async def options_call():
    return JSONResponse({}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })

# -----------------------------
# Local run
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
