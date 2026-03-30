#!/usr/bin/env python3
"""本地 webhook 接收器，用于安全验证企业微信消息发送。"""

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class WebhookSinkHandler(BaseHTTPRequestHandler):
    output_file: Path | None = None

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""
        body_text = raw_body.decode("utf-8", errors="replace")

        payload = {
            "timestamp": datetime.now().isoformat(),
            "path": self.path,
            "headers": dict(self.headers),
            "body_text": body_text,
        }

        try:
            payload["body_json"] = json.loads(body_text)
        except json.JSONDecodeError:
            payload["body_json"] = None

        print("=" * 80, flush=True)
        print(f"[{payload['timestamp']}] POST {self.path}", flush=True)
        if payload["body_json"] is not None:
            print(json.dumps(payload["body_json"], ensure_ascii=False, indent=2), flush=True)
        else:
            print(body_text, flush=True)

        if self.output_file is not None:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            with self.output_file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        response = {"errcode": 0, "errmsg": "ok", "path": self.path}
        response_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Run a local webhook sink for safe message testing.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8787, help="Bind port, default 8787")
    parser.add_argument(
        "--output-file",
        default="state/local_webhook_sink.ndjson",
        help="Append captured requests to this NDJSON file",
    )
    args = parser.parse_args()

    WebhookSinkHandler.output_file = Path(args.output_file)
    server = ThreadingHTTPServer((args.host, args.port), WebhookSinkHandler)

    print(f"Listening on http://{args.host}:{args.port}", flush=True)
    print("Example endpoints:", flush=True)
    print(f"  http://{args.host}:{args.port}/pending/default", flush=True)
    print(f"  http://{args.host}:{args.port}/pending/org-a", flush=True)
    print(f"Captured payloads will also be appended to {WebhookSinkHandler.output_file}", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Webhook sink stopped.", flush=True)


if __name__ == "__main__":
    main()
