"""AWS Lambda entry point for FloodRescue AI API Gateway HTTP API."""
import json
import logging
from typing import Any, Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Attempt to load Mangum adapter if installed, or fallback to native event parser
try:
    from mangum import Mangum
    from backend.api.app import app
    handler = Mangum(app, lifespan="off")
except ImportError:
    from backend.api.app import app

    def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Simple native Lambda proxy fallback if Mangum is not packaged."""
        from fastapi.testclient import TestClient
        client = TestClient(app)

        http_info = event.get("requestContext", {}).get("http", {})
        method = http_info.get("method", event.get("httpMethod", "GET"))
        raw_path = event.get("rawPath", event.get("path", "/health"))
        query_string = event.get("rawQueryString", "")
        if query_string:
            raw_path += f"?{query_string}"

        body = event.get("body", None)
        headers = event.get("headers", {})

        response = client.request(method=method, url=raw_path, content=body, headers=headers)
        return {
            "statusCode": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "isBase64Encoded": False,
        }
