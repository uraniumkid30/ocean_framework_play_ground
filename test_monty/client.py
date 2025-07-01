from enum import StrEnum
from typing import Any, Optional

import httpx
from loguru import logger

from port_ocean.utils import http_async_client


class ResourceCategory(StrEnum):
    Event = "event/find"


class SplunkClient:
    def __init__(
        self,
        xsf_token: str,
        ignore_server_error: bool,
        allow_insecure: bool,
        server_url: str = None,
    ):
        self.token = xsf_token
        server_url = (
            "https://api.eu1.signalfx.com" if server_url is None else server_url
        )
        self.api_url = f"{server_url}/v2"
        self.ignore_server_error = ignore_server_error
        self.allow_insecure = allow_insecure
        self.api_auth_header = {"X-SF-Token": f"{self.token}"}
        if self.allow_insecure:
            # This is not recommended for production use
            logger.warning(
                "Insecure mode is enabled. This will disable SSL verification \
                for the Splunk API client, which is not recommended for production use."
            )
            self.http_client = httpx.AsyncClient(verify=False)
        else:
            self.http_client = http_async_client
        self.http_client.headers.update(self.api_auth_header)

    async def _send_api_request(
        self,
        url: str,
        method: str = "GET",
        query_params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        logger.info(f"Sending request to Splunk API: {method} {url}")
        try:
            async with self._semaphore:
                response = await self.http_client.request(
                    method=method,
                    url=url,
                    params=query_params,
                    json=json_data,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Encountered an HTTP error with status code: \
                    {e.response.status_code} and response text: {e.response.text}"
            )
            if self.ignore_server_error:
                return {}
            raise e
        except httpx.HTTPError as e:
            logger.error(
                f"Encountered an HTTP error {e} while sending a request to {method} {url} with query_params: {query_params}"
            )
            if self.ignore_server_error:
                return {}
            raise e

    async def get_events(
        self, query_params: Optional[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        url = f"{self.api_url}/{ResourceCategory.event}"
        try:
            response_data = await self._send_api_request(url=url)
            return response_data or []
        except Exception as e:
            logger.error(f"Failed to fetch resources of {ResourceCategory.event}: {e}")
            if self.ignore_server_error:
                return []
            raise e
    @staticmethod
    def transform_event(event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "identifier": event["event_id"],
            "title": event["event_name"],
            "properties": {
                "eventName": event["event_name"],
                "eventCode": event["event_code"],
                "timestamp": event["_time"],
                "category": event["category"],
                "severity": event["severity"].lower(),
                "splunkLink": f"{os.environ['SPLUNK_URL']}/app/search/search?q=event_id%3D{event['event_id']}"
            },
            "relations": {
                "relatedService": event["service_name"]
            }
        }
