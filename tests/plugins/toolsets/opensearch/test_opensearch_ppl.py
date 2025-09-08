from unittest.mock import MagicMock, patch

import requests

from holmes.core.tools import ToolResultStatus
from holmes.plugins.toolsets.opensearch.opensearch_ppl import OpenSearchPPLToolset
from holmes.plugins.toolsets.opensearch.opensearch_utils import BaseOpenSearchConfig


def _setup_toolset() -> OpenSearchPPLToolset:
    toolset = OpenSearchPPLToolset()
    toolset.config = BaseOpenSearchConfig(
        opensearch_url="http://os.example",
        index_pattern="logs",
        opensearch_auth_header="Bearer token",
    )
    return toolset


def test_run_ppl_query_formats_request_correctly():
    toolset = _setup_toolset()
    query = "source=logs | stats count()"
    with patch(
        "holmes.plugins.toolsets.opensearch.opensearch_ppl.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"hits": {"total": 1}}
        mock_post.return_value = mock_response

        tool = toolset.tools[0]
        result = tool.invoke({"query": query})

        assert result.status == ToolResultStatus.SUCCESS
        called_args = mock_post.call_args
        assert called_args[1]["url"] == "http://os.example/_plugins/_ppl"
        assert called_args[1]["json"] == {"query": query}
        assert called_args[1]["headers"]["Authorization"] == "Bearer token"


def test_run_ppl_query_handles_http_error():
    toolset = _setup_toolset()
    query = "source=logs | stats count()"
    with patch(
        "holmes.plugins.toolsets.opensearch.opensearch_ppl.requests.post"
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "boom"
        mock_post.return_value = mock_response

        tool = toolset.tools[0]
        result = tool.invoke({"query": query})

        assert result.status == ToolResultStatus.ERROR
        assert result.error == "boom"
        assert result.return_code == 500


def test_run_ppl_query_handles_timeout():
    toolset = _setup_toolset()
    with patch(
        "holmes.plugins.toolsets.opensearch.opensearch_ppl.requests.post",
        side_effect=requests.Timeout,
    ):
        tool = toolset.tools[0]
        result = tool.invoke({"query": "source=logs"})

        assert result.status == ToolResultStatus.ERROR
        assert "timed out" in result.error.lower()
