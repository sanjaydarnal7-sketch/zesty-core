"""
Zesty OS
HTTP Client
Version: 1.0

Mission 18A

Shared HTTP Client for all AI Providers.
"""

from typing import Optional, Dict, Any
import requests


class HTTPClient:

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):

        response = requests.get(
            url=url,
            headers=headers,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ):

        response = requests.post(
            url=url,
            headers=headers,
            json=json,
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response

    def check_connection(self):

        return {
            "status": "ready",
            "timeout": self.timeout
        }


if __name__ == "__main__":

    client = HTTPClient()

    print(client.check_connection())