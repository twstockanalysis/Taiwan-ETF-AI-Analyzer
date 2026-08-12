"""Smoke-check native FastAPI and Streamlit services on separate local ports."""

import argparse
import json
import urllib.error
import urllib.request


def request(url: str, token: str | None = None) -> tuple[int, bytes]:
    headers = {"X-Owner-Token": token} if token else {}
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=15
        ) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def run_smoke(api_url: str, frontend_url: str, owner_token: str) -> dict[str, bool]:
    api = api_url.rstrip("/")
    frontend = frontend_url.rstrip("/")
    health_status, health_body = request(f"{api}/health")
    anonymous_status, _ = request(f"{api}/api/v1/decision-profile")
    wrong_status, _ = request(
        f"{api}/api/v1/decision-profile",
        "wrong-local-validation-token-00000",
    )
    owner_status, _ = request(
        f"{api}/api/v1/decision-profile", owner_token
    )
    frontend_status, _ = request(frontend)
    streamlit_health, _ = request(f"{frontend}/_stcore/health")
    return {
        "api_health": health_status == 200
        and json.loads(health_body).get("status") == "healthy",
        "anonymous_private_denied": anonymous_status == 401,
        "wrong_token_denied": wrong_status == 401,
        "owner_private_allowed": owner_status == 200,
        "frontend_available": frontend_status == 200,
        "streamlit_health": streamlit_health == 200,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:8501")
    parser.add_argument("--owner-token", required=True)
    args = parser.parse_args()
    results = run_smoke(args.api_url, args.frontend_url, args.owner_token)
    print(json.dumps(results, indent=2))
    if not all(results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
