# -*- coding: utf-8 -*-
"""Minimal client for the Fusion 360 MCP endpoint (fusion_mcp_execute).

    python tools/fusion.py script.py     run a python file inside Fusion
    python tools/fusion.py --hello       version / document probe
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:27182/mcp"
_op = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _post(payload, sid=None, tmo=3600):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if sid:
        h["MCP-Session-Id"] = sid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h)
    r = _op.open(req, timeout=tmo)
    body = r.read().decode()
    if "text/event-stream" in r.headers.get("Content-Type", ""):
        body = "\n".join(l[5:].strip() for l in body.splitlines() if l.startswith("data:"))
    return dict(r.headers), body


def session():
    hd, _ = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                              "clientInfo": {"name": "f1dev", "version": "1"}}})
    sid = hd.get("MCP-Session-Id") or hd.get("mcp-session-id")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return sid


def call(name, args):
    _, raw = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": name, "arguments": args}}, session())
    if not raw.strip():
        return ""
    d = json.loads(raw)
    out = "\n".join(c.get("text", "") for c in d.get("result", {}).get("content", []))
    if d.get("error"):
        out += "\n=== ERROR ===\n" + json.dumps(d["error"], ensure_ascii=False)
    return out


def run_script(src):
    return call("fusion_mcp_execute", {"featureType": "script",
                                       "object": {"script": src, "readOnly": False}})


if __name__ == "__main__":
    if sys.argv[1] == "--hello":
        print(run_script("import adsk.core\ndef run(c):\n    a=adsk.core.Application.get()\n"
                         "    print(a.version)\n    print([d.name for d in a.documents])\n"))
    else:
        print(run_script(open(sys.argv[1], encoding="utf-8").read()))
