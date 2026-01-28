from flask import Flask, Response, request
import json
import time

app = Flask(__name__)

def sse(data):
    return f"data: {json.dumps(data)}\n\n"

@app.route("/mcp/tools", methods=["GET"])
def list_tools():
    def stream():
        yield sse({
            "type": "tools",
            "tools": [
                {
                    "name": "say_hello",
                    "description": "Say hello to a user",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }
            ]
        })
        time.sleep(0.1)

    return Response(stream(), content_type="text/event-stream")

@app.route("/mcp/tools/call", methods=["POST"])
def call_tool():
    data = request.get_json(force=True)

    def stream():
        yield sse({
            "type": "content",
            "content": [
                {
                    "type": "text",
                    "text": f"Hello, {data.get('arguments', {}).get('name', 'there')} 👋"
                }
            ]
        })
        time.sleep(0.1)

    return Response(stream(), content_type="text/event-stream")

@app.route("/", methods=["GET"])
def root():
    def stream():
        yield sse({
            "type": "mcp",
            "name": "hello-mcp-python",
            "version": "0.0.1",
            "endpoints": {
                "tools": "/mcp/tools",
                "call": "/mcp/tools/call"
            }
        })
    return Response(stream(), content_type="text/event-stream")

if __name__ == "__main__":
    app.run(port=3333, threaded=True)
