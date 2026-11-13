# MCP (Model Context Protocol) server for testbed_micropython.

Install with
```bash
pip install -e ".[mcp]"
```

Run with
```bash
uv run mpmcp
# runs the server over stdio
uv run mcp run mpmcp
# registers it with Claude Desktop
uv run mcp install mpmcp
# runs the browser interface
uv run mcp dev mpmcp
```

python -m testbed_micropython.mpmcp.server
npx @modelcontextprotocol/inspector python -m testbed_micropython.mpmcp.server


## VSCode launch configuration for debugging

I added the configuration to [launch.json](.vscode/launch.json). I haven't run it yet.

- **Two entries**, after "mcp list_tentacles":
  - **"mcp debug: listen"**: VS Code waits on port 5678 for the server to connect to it.
  - **"mcp debug: inspector"**: starts the Inspector with the server running under `debugpy --connect`. It uses `.venv/bin/python`, which already has debugpy.
- **A compound**, at the end of the file: **"mcp debug: inspector + debugger"** starts both together.

To use it, run the compound with F5, open the Inspector URL from the terminal and click **Connect**. Your breakpoints in the server code will then be hit.

The Inspector times out requests after about 10 s. If you'll pause on a breakpoint for longer, raise "Request Timeout" in the Inspector's **Configuration** panel.

