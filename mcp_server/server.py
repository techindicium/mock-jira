import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mock-jira-mcp")


def main() -> None:
    import mcp_server.tools.issues
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)

    port = os.environ.get("PORT")
    if port:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
