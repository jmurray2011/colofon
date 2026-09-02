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
    "colofon_init_project",
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


def call_error(process, request_id, name, arguments, timeout=30):
    send(process, {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    response = receive(process, timeout)
    result = response.get("result", {})
    structured = result.get("structuredContent", {})
    if not result.get("isError") or structured.get("ok") is not False:
        raise RuntimeError(f"{name} unexpectedly succeeded: {response}")
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
        initialized_project = call(process, 4, "colofon_init_project", {
            "brand": "example-studio",
        })
        expected_starters = {
            "documents/example-report.md",
            "book/book.yaml",
            "book/chapters/01-welcome.md",
            "packages/local/example-studio/0.1.0/lib.typ",
        }
        if not expected_starters.issubset(initialized_project.get("files", [])):
            raise RuntimeError(f"project init omitted starter files: {initialized_project}")
        refusal = call_error(process, 5, "colofon_init_project", {
            "brand": "example-studio",
        })
        if "overwrite" not in json.dumps(refusal).lower():
            raise RuntimeError(f"repeated init did not explain its refusal: {refusal}")
        call(process, 6, "colofon_lint", {
            "sources": ["documents/example-report.md", "book/chapters/01-welcome.md"],
        })
        initialized_document = call(process, 7, "colofon_build_document", {
            "source": "documents/example-report.md",
            "output": "build/mcp-init-report.pdf",
        })
        if not initialized_document.get("results", [{}])[0].get("checks", {}).get("verified"):
            raise RuntimeError(f"initialized document was not verified: {initialized_document}")
        initialized_book = call(process, 8, "colofon_build_book", {
            "source": "book/book.yaml",
            "output": "build/mcp-init-book.pdf",
        })
        if not initialized_book.get("checks", {}).get("verified"):
            raise RuntimeError(f"initialized book was not verified: {initialized_book}")
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
