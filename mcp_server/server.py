from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mock-jira-mcp")


def main() -> None:
    import mcp_server.tools.issues
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)

    mcp.run()


if __name__ == "__main__":
    main()
