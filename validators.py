#!/usr/bin/env python3

import sys
import json
import time
import datetime
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_VALIDATORS = [
    "http://localhost:9151",
]

TIMEOUT = 5
INTERVAL = 30


@dataclass
class ValidatorStatus:
    url: str
    online: bool
    block_number: Optional[int] = None
    ping_ok: Optional[bool] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z")


def rpc_call(base_url, method, params=[]):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }).encode()

    req = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/api",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


def check_validator(url):
    status = ValidatorStatus(url=url, online=False)

    try:
        t0 = time.monotonic()
        resp = rpc_call(url, "gen_dbg_ping")
        status.latency_ms = round((time.monotonic() - t0) * 1000, 1)
        status.ping_ok = "result" in resp
        status.online = True
    except urllib.error.URLError as e:
        status.error = f"connection failed: {e.reason}"
        return status
    except Exception as e:
        status.error = str(e)
        return status

    try:
        resp = rpc_call(url, "eth_blockNumber")
        status.block_number = int(resp.get("result", "0x0"), 16)
    except Exception as e:
        status.error = f"eth_blockNumber failed: {e}"

    return status


def print_status(s):
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
        print(f"  block        : unavailable{f' ({s.error})' if s.error else ''}")


def run_checks(validators):
    results = [check_validator(url) for url in validators]
    for s in results:
        print_status(s)

    total = len(results)
    online = sum(1 for r in results if r.online)
    print(f"\ntotal: {total}  online: {online}  offline: {total - online}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    watch = "--watch" in sys.argv
    validators = args if args else DEFAULT_VALIDATORS

    if watch:
        try:
            while True:
                print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC]")
                run_checks(validators)
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            pass
    else:
        run_checks(validators)


if __name__ == "__main__":
    main()
