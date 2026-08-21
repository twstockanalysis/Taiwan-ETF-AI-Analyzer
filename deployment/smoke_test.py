"""Post-deployment public and owner-boundary smoke checks."""

import argparse
import json
import os
import urllib.error
import urllib.request


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        del request, file_pointer, code, message, headers, new_url
        return None


def request(url: str, token: str | None = None) -> tuple[int, bytes]:
    headers = {"X-Owner-Token": token} if token else {}
    opener = urllib.request.build_opener(_NoRedirectHandler)
    try:
        with opener.open(
            urllib.request.Request(url, headers=headers),
            timeout=15,
        ) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def run_smoke(base_url: str, owner_token: str) -> dict[str, bool]:
    base = base_url.rstrip("/")
    results = {}
    health_status, health_body = request(f"{base}/health")
    results["health"] = (
        health_status == 200
        and json.loads(health_body).get("status") == "healthy"
    )
    anonymous_status, _ = request(f"{base}/api/v1/decision-profile")
    results["anonymous_private_denied"] = anonymous_status == 401
    owner_status, _ = request(
        f"{base}/api/v1/decision-profile",
        owner_token,
    )
    results["owner_private_allowed"] = owner_status == 200
    frontend_status, _ = request(base)
    results["frontend"] = frontend_status == 200
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--owner-token-env", default="TW_ETF_OWNER_TOKEN")
    args = parser.parse_args()
    owner_token = os.environ.get(args.owner_token_env, "")
    if not owner_token:
        parser.error(
            "owner token environment variable is empty: "
            f"{args.owner_token_env}"
        )
    results = run_smoke(args.base_url, owner_token)
    print(json.dumps(results, indent=2))
    if not all(results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
