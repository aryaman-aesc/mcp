from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid

app = FastAPI()

# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Helpers
# -----------------------
def sse(data):
    return f"data: {json.dumps(data)}\n\n"

def ping():
    return ": keep-alive\n\n"

# -----------------------
# Fake dataset (replace with AIRA / DB / vector store)
# -----------------------
DOCUMENTS = {
    "cand-1": {
        "id": "cand-1",
        "title": "Backend Engineer – John Doe",
        "text": "John Doe has 5 years of experience in Node.js, TypeScript, AWS, and PostgreSQL.",
        "url": "aira://candidates/cand-1",
        "metadata": {"type": "candidate"}
    },
    "jd-1": {
        "id": "jd-1",
        "title": "Job Description – Backend Engineer",
        "text": "Looking for a Backend Engineer skilled in Node.js, TypeScript, AWS, and system design.",
        "url": "aira://jobs/jd-1",
        "metadata": {"type": "job_description"}
    }
}

# -----------------------
# Root / discovery
# -----------------------
@app.get("/")
async def root():
    return JSONResponse({
        "name": "AIRA Connector MCP",
        "version": "1.0.0",
        "description": "Read-only MCP server for OpenAI Connectors",
        "mcp_version": "2024-11-05"
    })

@app.get("/.well-known/mcp.json")
async def well_known():
    return JSONResponse({
        "mcpServers": {
            "aira": {
                "url": "/mcp"
            }
        }
    })

@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy"})

# -----------------------
# List tools (SSE)
# -----------------------
@app.get("/mcp/tools")
async def list_tools():
    async def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search AIRA documents",
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
                        "description": "Fetch full document by ID",
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

        try:
            while True:
                await asyncio.sleep(15)
                yield ping()
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )

# -----------------------
# Tool execution (SSE)
# -----------------------
@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    payload = await request.json()
    tool_name = payload.get("params", {}).get("name")
    args = payload.get("params", {}).get("arguments", {})
    request_id = payload.get("id", str(uuid.uuid4()))

    async def stream():
        # -------- search --------
        if tool_name == "search":
            query = args.get("query", "").lower()

            results = []
            for doc in DOCUMENTS.values():
                if query in doc["title"].lower() or query in doc["text"].lower():
                    results.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "url": doc["url"]
                    })

            yield sse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"results": results})
                        }
                    ]
                }
            })

        # -------- fetch --------
        elif tool_name == "fetch":
            doc_id = args.get("id")
            doc = DOCUMENTS.get(doc_id)

            if not doc:
                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": f"Document not found: {doc_id}"
                    }
                })
            else:
                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(doc)
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

        try:
            while True:
                await asyncio.sleep(15)
                yield ping()
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )

# -----------------------
# CORS preflight
# -----------------------
@app.options("/mcp/tools")
async def options_tools():
    return JSONResponse(content={}, headers={"Access-Control-Allow-Origin": "*"})

@app.options("/mcp/tools/call")
async def options_call():
    return JSONResponse(content={}, headers={"Access-Control-Allow-Origin": "*"})

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
