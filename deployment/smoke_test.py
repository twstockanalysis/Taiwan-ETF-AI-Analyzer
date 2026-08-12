"""Post-deployment public and owner-boundary smoke checks."""

import argparse
import json
import urllib.error
import urllib.request


def request(url: str, token: str | None = None) -> tuple[int, bytes]:
    headers = {"X-Owner-Token": token} if token else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--owner-token", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    results = {}
    health_status, health_body = request(f"{base}/health")
    results["health"] = health_status == 200 and json.loads(health_body)["status"] == "healthy"
    anonymous_status, _ = request(f"{base}/api/v1/decision-profile")
    results["anonymous_private_denied"] = anonymous_status == 401
    owner_status, _ = request(f"{base}/api/v1/decision-profile", args.owner_token)
    results["owner_private_allowed"] = owner_status == 200
    frontend_status, _ = request(base)
    results["frontend"] = frontend_status == 200
    print(json.dumps(results, indent=2))
    if not all(results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
