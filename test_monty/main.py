from typing import Any

from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE
from port_ocean.clients.port.types import UserAgentType
from client import SplunkClient, ResourceCategory


# Required
# Listen to the resync event of all the kinds specified in the mapping inside port.
# Called each time with a different kind that should be returned from the source system.
@ocean.on_resync()
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    # 1. Get all data from the source system
    # 2. Return a list of dictionaries with the raw data of the state to run the core logic of the framework for
    # Example:
    # if kind == "project":
    #     return [{"some_project_key": "someProjectValue", ...}]
    # if kind == "issues":
    #     return [{"some_issue_key": "someIssueValue", ...}]

    # Initial stub to show complete flow, replace this with your own logic
    if kind == "test_monty-example-kind":
        return [
            {
                "id": "AddBYZrEFEF",
                "metadata": {
                    "ETS_key1": "detector",
                    "ETS_key2": False,
                    "ETS_key3": 1001,
                },
                "properties": {
                    "is": "ok",
                    "sf_notificationWasSent": True,
                    "was": "anomalous",
                },
                "sf_eventCategory": "USER_DEFINED",
                "sf_eventCreatedOnMs": 1553678621002,
                "sf_eventType": "string",
                "timestamp": 1554672630000,
                "tsId": "XzZYApXCDCD",
            }
        ]

    return []


def init_client() -> SplunkClient:
    return SplunkClient(
        ocean.integration_config["token"],
        ocean.integration_config["server_url"],
        ocean.integration_config["ignore_server_error"],
        ocean.integration_config["allow_insecure"],
    )


@ocean.on_resync(kind=ResourceCategory.Event)
async def on_resources_resync(kind: str):
    argocd_client = init_client()
    return await argocd_client.get_events({"query": "is:ok"})


# The same sync logic can be registered for one of the kinds that are available in the mapping in port.
# @ocean.on_resync('project')
# async def resync_project(kind: str) -> list[dict[Any, Any]]:
#     # 1. Get all projects from the source system
#     # 2. Return a list of dictionaries with the raw data of the state
#     return [{"some_project_key": "someProjectValue", ...}]
#
# @ocean.on_resync('issues')
# async def resync_issues(kind: str) -> list[dict[Any, Any]]:
#     # 1. Get all issues from the source system
#     # 2. Return a list of dictionaries with the raw data of the state
#     return [{"some_issue_key": "someIssueValue", ...}]


# Optional
# Listen to the start event of the integration. Called once when the integration starts.


@ocean.on_start()
async def on_start() -> None:
    print("Starting Splunk integration")
    ocean.register_user_agent(UserAgentType.INTEGRATION, "splunk")


@ocean.router.post("/webhook")
async def on_application_event_webhook_handler(request) -> None:
    data = await request.json()
    print(f"received webhook event data: {data}")
    splunk_client = init_client()

    transformed = splunk_client.transform_event(data["event"])
    await ocean.register_raw(kind="splunkEvent", items=[transformed])
    return {"status": "success"}
