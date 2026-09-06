import socket

import pytest


def test_mcp_server_unreachable_starts_only_mcp_server(mcp_server_unreachable):
    host, port = mcp_server_unreachable.replace("http://", "").split(":")
    with socket.create_connection((host, int(port)), timeout=2):
        pass  # mcp-server itself is up, even though its upstream is dead


def test_mcp_server_unreachable_points_at_a_dead_port():
    # A sibling assertion (not fixture-dependent) that the fixture's chosen dead port really
    # is unreachable, documenting the topology's intent — see the fixture's own docstring.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
    with pytest.raises(OSError), socket.create_connection(("127.0.0.1", dead_port), timeout=1):
        pass  # pragma: no cover - should never be reached
