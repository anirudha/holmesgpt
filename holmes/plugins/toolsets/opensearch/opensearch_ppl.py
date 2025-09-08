import json
import logging
from typing import Dict
from urllib.parse import urljoin

import requests  # type: ignore
from requests import RequestException  # type: ignore

from holmes.core.tools import (
    CallablePrerequisite,
    StructuredToolResult,
    Tool,
    ToolParameter,
    ToolResultStatus,
    ToolsetTag,
)
from holmes.plugins.toolsets.opensearch.opensearch_utils import (
    BaseOpenSearchToolset,
    add_auth_header,
)
from holmes.plugins.toolsets.utils import (
    get_param_or_raise,
    toolset_name_for_one_liner,
)


class RunPPLQuery(Tool):
    def __init__(self, toolset: "OpenSearchPPLToolset"):
        super().__init__(
            name="run_ppl_query",
            description="Execute a PPL query against an OpenSearch cluster",
            parameters={
                "query": ToolParameter(
                    description="The PPL query to run",
                    type="string",
                    required=True,
                )
            },
        )
        self._toolset = toolset

    def _invoke(
        self, params: dict, user_approved: bool = False
    ) -> StructuredToolResult:
        try:
            query = get_param_or_raise(params, "query")
            body = {"query": query}
            headers = {"Content-Type": "application/json"}
            headers.update(
                add_auth_header(self._toolset.opensearch_config.opensearch_auth_header)
            )
            url = urljoin(
                self._toolset.opensearch_config.opensearch_url,
                "/_plugins/_ppl",
            )
            response = requests.post(
                url=url,
                timeout=180,
                verify=True,
                json=body,
                headers=headers,
            )
            if response.status_code == 200:
                return StructuredToolResult(
                    status=ToolResultStatus.SUCCESS,
                    data=json.dumps(response.json()),
                    params=params,
                )
            return StructuredToolResult(
                status=ToolResultStatus.ERROR,
                return_code=response.status_code,
                error=response.text,
                params=params,
            )
        except requests.Timeout:
            logging.warning("Timeout while running OpenSearch PPL query", exc_info=True)
            return StructuredToolResult(
                status=ToolResultStatus.ERROR,
                error="Request timed out while running OpenSearch PPL query",
                params=params,
            )
        except RequestException as e:
            logging.warning(
                "Network error while running OpenSearch PPL query", exc_info=True
            )
            return StructuredToolResult(
                status=ToolResultStatus.ERROR,
                error=f"Network error while running OpenSearch PPL query: {str(e)}",
                params=params,
            )
        except Exception as e:
            logging.warning(
                "Unexpected error while running OpenSearch PPL query", exc_info=True
            )
            return StructuredToolResult(
                status=ToolResultStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
                params=params,
            )

    def get_parameterized_one_liner(self, params: Dict) -> str:
        query = params.get("query", "")
        return (
            f"{toolset_name_for_one_liner(self._toolset.name)}: Run PPL Query ({query})"
        )


class OpenSearchPPLToolset(BaseOpenSearchToolset):
    def __init__(self):
        super().__init__(
            name="opensearch/ppl",
            description="Run PPL queries against OpenSearch",
            docs_url="https://holmesgpt.dev/data-sources/builtin-toolsets/opensearch-ppl/",
            icon_url="https://opensearch.org/assets/brand/PNG/Mark/opensearch_mark_default.png",
            prerequisites=[CallablePrerequisite(callable=self.prerequisites_callable)],
            tools=[],
            tags=[
                ToolsetTag.CORE,
            ],
        )
        self.tools = [RunPPLQuery(self)]
