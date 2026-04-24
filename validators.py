#!/usr/bin/env python3

import sys
import json
import time
import datetime
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional, Any, Dict


class RPCContractError(Exception):
    pass


class RPCClient:
    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, method: str, params=None) -> Dict[str, Any]:
        if params is None:
            params = []

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }).encode()

        req = urllib.request.Request(
            url=self.base_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise RPCContractError(f"http error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise RPCContractError(f"connection failed: {e.reason}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise RPCContractError(f"invalid json response: {raw!r}")

        if "error" in data:
            raise RPCContractError(f"rpc error: {json.dumps(data['error'])}")

        if "result" not in data:
            raise RPCContractError("missing 'result' field")

        return data


@dataclass
class ValidatorStatus:
    url: str
    online: bool
    ping_ok: Optional[bool] = None
    latency_ms: Optional[float] = None
    block_number: Optional[int] = None
    error: Optional[str] = None
    checked_at: str = field(
        default_factory=lambda: datetime.datetime.utcnow()
        .isoformat(timespec="seconds") + "Z"
    )


def check_ping(client: RPCClient) -> float:
    t0 = time.monotonic()
    client.call("gen_dbg_ping")
    return round((time.monotonic() - t0) * 1000, 1)


def check_block_number(client: RPCClient) -> int:
    resp = client.call("eth_blockNumber")
    result = resp["result"]

    if not isinstance(result, str) or not result.startswith("0x"):
        raise RPCContractError(f"invalid block format: {result}")

    return int(result, 16)


def evaluate_validator(url: str) -> ValidatorStatus:
    client = RPCClient(url)
    status = ValidatorStatus(url=url, online=False)

    try:
        latency = check_ping(client)
        status.latency_ms = latency
        status.ping_ok = True
        status.online = True
    except Exception as e:
        status.error = str(e)
        return status

    try:
        status.block_number = check_block_number(client)
    except Exception as e:
        status.error = f"eth_blockNumber failed: {e}"

    return status


def print_status(s: ValidatorStatus):
    state = "online" if s.online else "offline"
    print(f"\n[{state}] {s.url}")
    print(f"  checked_at   : {s.checked_at}")

    if not s.online:
        print(f"  error        : {s.error}")
        return

    print(f"  ping         : {'ok' if s.ping_ok else 'fail'}")
    print(f"  latency      : {s.latency_ms} ms")

    if s.block_number is not None:
        print(f"  block        : {s.block_number}")
    else:
        msg = f"unavailable ({s.error})" if s.error else "unavailable"
        print(f"  block        : {msg}")


def run(validators):
    results = [evaluate_validator(v) for v in validators]

    for r in results:
        print_status(r)

    total = len(results)
    online = sum(1 for r in results if r.online)

    print(f"\ntotal: {total}  online: {online}  offline: {total - online}")


DEFAULT_VALIDATORS = ["http://localhost:9151"]
INTERVAL = 30


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    watch = "--watch" in sys.argv

    validators = args if args else DEFAULT_VALIDATORS

    if watch:
        try:
            while True:
                now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{now} UTC]")
                run(validators)
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            pass
    else:
        run(validators)


if __name__ == "__main__":
    main()
