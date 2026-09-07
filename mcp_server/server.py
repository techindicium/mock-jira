import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mock-jira-mcp")


def main() -> None:
    import mcp_server.tools.issues
    import mcp_server.tools.projects
    import mcp_server.tools.users  # noqa: F401  (import registers the tools as a side effect)

    # Re-fetch the canonical MCPServer instance via its fully-qualified module name, rather
    # than using the `mcp` global above directly. When this file is run as the entrypoint
    # (`python -m mcp_server.server`), Python loads it into sys.modules as `__main__`, which is
    # a *separate* module object from `mcp_server.server`. The absolute imports above (inside
    # mcp_server/tools/*.py, `from mcp_server.server import mcp`) trigger a second, independent
    # import of this same file under its real package name, creating a second MCPServer instance
    # and registering all @mcp.tool()-decorated tools onto *that* instance — not onto the
    # `__main__`-local `mcp` global above. Running `mcp.run(...)` here would then serve an
    # instance with zero registered tools. Re-importing by qualified name after the tool modules
    # have loaded resolves to the same (already-registered) instance in both invocation styles:
    # as `__main__`, `mcp_server.server` is already cached in sys.modules by the tool imports
    # above; imported normally (e.g. by tests), this is simply the same module-level `mcp`.
    from mcp_server.server import mcp as _mcp

    port = os.environ.get("PORT")
    if port:
        _mcp.run(transport="streamable-http", host="0.0.0.0", port=int(port))
    else:
        _mcp.run()


if __name__ == "__main__":
    main()
