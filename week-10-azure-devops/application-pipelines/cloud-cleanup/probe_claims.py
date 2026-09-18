"""Print only public federation binding metadata from an already authenticated native WIF task."""
import base64
import importlib.util
import json
import os
from pathlib import Path

spec = importlib.util.spec_from_file_location("canary_worker", Path(__file__).with_name("worker.py"))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def metadata(token):
    worker.require(isinstance(token, str) and len(token) <= 16384 and token.count(".") == 2, "oidc_shape")
    encoded = token.split(".")[1]
    claims = worker.load_json(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    worker.require(isinstance(claims, dict), "oidc_shape")
    worker.require(worker.matches(r"https://login\.microsoftonline\.com/" + worker.UUID + r"/v2\.0", claims.get("iss"))
                   and worker.matches(r"[A-Za-z0-9_:/.-]{10,400}", claims.get("sub"))
                   and claims.get("aud") == "api://AzureADTokenExchange"
                   and (claims.get("azp") is None or worker.matches(worker.UUID, claims.get("azp"))), "oidc_claims")
    return {"issuer": claims["iss"], "subject": claims["sub"], "authorized_party": claims.get("azp")}


def main():
    try:
        result = metadata(os.environ.pop("idToken", None))
        print(json.dumps({"federation": result, "aws_exchange_verified": False,
                          "canary_cleanup_verified": False, "workload_cleanup_ready": False}, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError):
        print('{"status":"claim_metadata_unavailable"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
