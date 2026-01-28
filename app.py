from flask import Flask, Response, request
import json, time, uuid

app = Flask(__name__)

def sse(data):
    return f"data: {json.dumps(data)}\n\n"

def ping():
    return ": keep-alive\n\n"

@app.route("/", methods=["GET"])
def root():
    return "MCP server alive", 200


@app.route("/mcp/tools", methods=["GET"])
def list_tools():
    def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "result": {
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
            }
        })

        while True:
            time.sleep(15)
            yield ping()

    return Response(
        stream(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.route("/mcp/tools/call", methods=["POST"])
def call_tool():
    payload = request.get_json(force=True)

    def stream():
        yield sse({
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Hello, {payload['params']['arguments'].get('name','there')} 👋"
                    }
                ]
            }
        })

        while True:
            time.sleep(15)
            yield ping()

    return Response(
        stream(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    app.run(port=3333, threaded=True)
