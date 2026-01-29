from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Root endpoint - returns JSON, not SSE"""
    return JSONResponse({
        "name": "MCP Greeting Server",
        "version": "1.0.0",
        "description": "A simple MCP server that can greet people",
        "mcp_version": "2024-11-05",
        "capabilities": {
            "tools": {}
        }
    })

@app.get("/.well-known/mcp.json")
async def well_known():
    """Well-known endpoint for MCP discovery"""
    return JSONResponse({
        "mcpServers": {
            "greeting": {
                "url": "/mcp"
            }
        }
    })

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy"})

@app.get("/mcp/tools")
async def list_tools():
    """List all available MCP tools - SSE endpoint"""
    async def stream():
        # Send the tools list
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
        
        # Send completion event
        yield sse({
            "jsonrpc": "2.0",
            "method": "notifications/complete"
        })
        
        # Keep connection alive
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

@app.post("/mcp/tools/call")
async def call_tool(request: Request):
    """Execute an MCP tool - SSE endpoint"""
    try:
        payload = await request.json()
        tool_name = payload.get("params", {}).get("name")
        arguments = payload.get("params", {}).get("arguments", {})
        request_id = payload.get("id", str(uuid.uuid4()))
        
        async def stream():
            if tool_name == "say_hello":
                name = arguments.get("name", "there")
                
                # Send result
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
                
                # Send completion
                yield sse({
                    "jsonrpc": "2.0",
                    "method": "notifications/complete"
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
            
            # Keep connection alive
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
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Add OPTIONS handler for CORS preflight
@app.options("/mcp/tools")
async def options_tools():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.options("/mcp/tools/call")
async def options_call():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
