# -*- coding: utf-8 -*-
"""Send a python file to the Fusion 360 MCP endpoint (fusion_mcp_execute).
Usage: python tools/cloud.py <script.py>       (or --tools to list MCP tools)"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:27182/mcp"
_op = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _post(p, sid=None, tmo=1800):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if sid:
        h["MCP-Session-Id"] = sid
    r = _op.open(urllib.request.Request(URL, data=json.dumps(p).encode(), headers=h), timeout=tmo)
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


def call(name, args, sid=None):
    sid = sid or session()
    _, raw = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": name, "arguments": args}}, sid)
    if not raw.strip():
        return ""
    d = json.loads(raw)
    txt = "\n".join(c.get("text", "") for c in d.get("result", {}).get("content", []))
    if d.get("error"):
        txt += "\n=== ERROR ===\n" + json.dumps(d["error"], ensure_ascii=False)
    return txt


if __name__ == "__main__":
    if sys.argv[1] == "--tools":
        _, raw = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session())
        for t in json.loads(raw)["result"]["tools"]:
            print(t["name"], "::", t["description"][:120].replace("\n", " "))
    else:
        src = open(sys.argv[1], encoding="utf-8").read()
        print(call("fusion_mcp_execute", {"featureType": "script",
                                          "object": {"script": src, "readOnly": False}}))
