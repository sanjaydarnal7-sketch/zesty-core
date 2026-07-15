"""
Zesty OS
HTTP Client Test

Mission 20
"""

from providers.http_client import HTTPClient


def test_http_client():

    client = HTTPClient()

    result = client.check_connection()

    assert result["status"] == "ready"

    print("✅ HTTP Client Test Passed")


if __name__ == "__main__":

    test_http_client()