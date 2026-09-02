#!/usr/bin/env python3
"""Perform an MCP initialize and tool-discovery exchange with a command."""

import argparse
import json
import selectors
import subprocess
import sys

EXPECTED_TOOLS = {
    "colofon_build_book",
    "colofon_build_document",
    "colofon_describe",
    "colofon_lint",
}


def send(process, payload):
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()


def receive(process, timeout=15):
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    if not selector.select(timeout):
        raise RuntimeError("timed out waiting for the MCP server")
    line = process.stdout.readline()
    if not line:
        stderr = process.stderr.read().strip()
        raise RuntimeError(f"MCP server closed before responding: {stderr}")
    return json.loads(line)


def call(process, request_id, name, arguments, timeout=180):
    send(process, {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    response = receive(process, timeout)
    result = response.get("result", {})
    structured = result.get("structuredContent", {})
    if result.get("isError") or not structured.get("ok"):
        raise RuntimeError(f"{name} failed: {response}")
    return structured


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        ap.error("a server command is required after --")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        send(process, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "capabilities": {},
                "clientInfo": {"name": "colofon-smoke", "version": "1"},
                "protocolVersion": "2026-07-28",
            },
        })
        initialized = receive(process)
        if initialized.get("id") != 1 or "result" not in initialized:
            raise RuntimeError(f"initialize failed: {initialized}")
        if "colofon_describe" not in initialized["result"].get("instructions", ""):
            raise RuntimeError(f"initialize omitted Colofon workflow instructions: {initialized}")
        send(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(process, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = receive(process)
        tools = {tool["name"] for tool in listed.get("result", {}).get("tools", [])}
        if tools != EXPECTED_TOOLS:
            raise RuntimeError(f"tools/list returned {sorted(tools)}, expected {sorted(EXPECTED_TOOLS)}")
        described = call(process, 3, "colofon_describe", {})
        if "report" not in described.get("document_schemas", {}):
            raise RuntimeError(f"describe omitted document schemas: {described}")
        call(process, 4, "colofon_lint", {
            "sources": ["tools/factory-examples/sample-report.md"],
        })
        document = call(process, 5, "colofon_build_document", {
            "source": "tools/factory-examples/sample-report.md",
            "output": "build/mcp-smoke-report.pdf",
        })
        if not document.get("results", [{}])[0].get("checks", {}).get("verified"):
            raise RuntimeError(f"document result was not verified: {document}")
        book = call(process, 6, "colofon_build_book", {
            "source": "tools/factory-examples/book/book.yaml",
            "output": "build/mcp-smoke-book.pdf",
        })
        if not book.get("checks", {}).get("verified"):
            raise RuntimeError(f"book result was not verified: {book}")
        print("MCP smoke test: ok (" + ", ".join(sorted(tools)) + ")")
        return 0
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"mcp_smoke: {error}", file=sys.stderr)
        sys.exit(1)
