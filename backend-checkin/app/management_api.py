import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


class ManagementApiError(Exception):
    def __init__(self, body, status):
        super().__init__(body.get("error", {}).get("message", "Management API request failed."))
        self.body = body
        self.status = status


def post(path, payload):
    url = f"{current_app.config['MANAGEMENT_API_URL']}/{path.lstrip('/')}"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Checkin-Service-Token": current_app.config["CHECKIN_SERVICE_TOKEN"],
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=current_app.config["MANAGEMENT_API_TIMEOUT"]) as response:
            return json.loads(response.read().decode("utf-8")), response.status
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {"error": {"code": "MANAGEMENT_API_ERROR", "message": "The management service returned an invalid response."}}
        raise ManagementApiError(body, exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ManagementApiError(
            {"error": {"code": "MANAGEMENT_API_UNAVAILABLE", "message": "The management service is temporarily unavailable."}},
            503,
        ) from exc
