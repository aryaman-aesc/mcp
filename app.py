from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- MCP METADATA ----
SERVER_INFO = {
    "name": "hello-mcp-python",
    "version": "0.0.1"
}

# ---- LIST TOOLS ----
@app.route("/mcp/tools", methods=["GET"])
def list_tools():
    return jsonify({
        "tools": [
            {
                "name": "say_hello",
                "description": "Say hello to a user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" }
                    },
                    "required": ["name"]
                }
            }
        ]
    })

# ---- CALL TOOL ----
@app.route("/mcp/tools/call", methods=["POST", "OPTIONS"], strict_slashes=False)
def call_tool():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(force=True)
    tool_name = data.get("name")
    args = data.get("arguments", {})

    if tool_name == "say_hello":
        name = args.get("name", "there")
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Hello, {name}! 👋 This is your MCP server speaking."
                }
            ]
        })

    return jsonify({"error": f"Unknown tool: {tool_name}"}), 400


if __name__ == "__main__":
    app.run(port=3333)
