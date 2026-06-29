import json

import pytest
from paper_to_deck import mcp_server


def test_handler_returns_parsed_paper_json(sample_pdf, tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_TO_DECK_SANDBOX", str(tmp_path))
    payload = mcp_server._handle_parse_paper(str(sample_pdf))
    data = json.loads(payload)
    assert "title" in data and "figures" in data
    assert isinstance(data["figures"], list)


@pytest.mark.asyncio
async def test_server_lists_parse_paper_tool():
    server = mcp_server.build_server()
    import mcp.types as types
    request = types.ListToolsRequest(method="tools/list")
    handler = server.request_handlers[types.ListToolsRequest]
    response = await handler(request)
    names = [t.name for t in response.root.tools]
    assert "parse_paper" in names
