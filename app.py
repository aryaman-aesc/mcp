from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid

app = FastAPI(
    title="MCP Greeting Server",
    description="A simple MCP server with greeting functionality",
    version="1.0.0",
    servers=[
        {
            "url": "http://localhost:8000",  # Change to your actual domain in production
            "description": "Development server"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sse(data):
    """Format data as Server-Sent Event"""
    return f"data: {json.dumps(data)}\n\n"

def ping():
    """Send keep-alive ping"""
    return ": keep-alive\n\n"

@app.get("/")
async def root():
    """Root endpoint with server metadata for ChatGPT connector discovery"""
    return {
        "name": "MCP Greeting Server",
        "version": "1.0.0",
        "description": "A simple MCP server that can greet people",
        "mcp_version": "2024-11-05",
        "capabilities": {
            "tools": True
        },
        "endpoints": {
            "tools": "/mcp/tools",
            "call_tool": "/mcp/tools/call"
        },
        "openapi_schema": "/openapi.json"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-server"}

@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools"""
    async def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
                "tools": [
                    {
                        "name": "say_hello",
                        "description": "Say hello to someone by name",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The name of the person to greet"
                                }
                            },
                            "required": ["name"]
                        }
                    }
                ]
            }
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(15)
            yield ping()
    
    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Execute an MCP tool"""
    try:
        payload = await request.json()
        tool_name = payload.get("params", {}).get("name")
        arguments = payload.get("params", {}).get("arguments", {})
        request_id = payload.get("id", str(uuid.uuid4()))
        
        async def stream():
            if tool_name == "say_hello":
                name = arguments.get("name", "there")
                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Hello, {name}! 👋 Nice to meet you!"
                            }
                        ]
                    }
                })
            else:
                # Tool not found error
                yield sse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}",
                        "data": {
                            "available_tools": ["say_hello"]
                        }
                    }
                })
            
            # Keep connection alive for potential streaming responses
            while True:
                await asyncio.sleep(15)
                yield ping()
        
        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
