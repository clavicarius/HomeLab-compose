import json
import os
import re
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


HOST_PATTERN = re.compile(r"Host\((?P<hosts>[^)]*)\)")
QUOTED_HOST = re.compile(r"[`\"](?P<host>[^`\"]+)[`\"]")
TECHNICAL_SERVICES = {"api@internal", "noop@internal"}
STATIC_DIR = Path(__file__).parent / "static"


def hostnames_from_rule(rule):
    match = HOST_PATTERN.search(rule or "")
    if not match:
        return []
    return [item.group("host").strip() for item in QUOTED_HOST.finditer(match.group("hosts"))]


def display_name(host):
    label = host.split(".", 1)[0].replace("-", " ").replace("_", " ")
    return label.title()


def normalize_routers(routers):
    services = {}
    for router in routers:
        provider = router.get("Provider", "")
        name = router.get("Name", "")
        service = router.get("Service", "")
        if provider != "docker" and not name.endswith("@docker"):
            continue
        if service in TECHNICAL_SERVICES:
            continue
        for host in hostnames_from_rule(router.get("Rule", "")):
            if "*" in host or host in services:
                continue
            services[host] = {
                "name": display_name(host),
                "host": host,
                "url": f"https://{host}",
                "tls": router.get("TLS") is not None,
            }
    return sorted(services.values(), key=lambda item: item["name"].lower())


class DashboardState:
    def __init__(self, api_url, api_host, refresh_seconds):
        self.api_url = api_url
        self.api_host = api_host
        self.refresh_seconds = refresh_seconds
        self.services = []
        self.lock = threading.Lock()

    def update(self):
        request = Request(self.api_url, headers={"Host": self.api_host})
        context = ssl._create_unverified_context()
        with urlopen(request, context=context, timeout=10) as response:
            payload = json.load(response)
        services = normalize_routers(payload if isinstance(payload, list) else [])
        with self.lock:
            self.services = services

    def snapshot(self):
        with self.lock:
            return list(self.services)


def refresh_loop(state):
    while True:
        try:
            state.update()
        except Exception as error:
            print(f"Traefik API refresh failed: {error}", flush=True)
        time.sleep(state.refresh_seconds)


def handler_for(state):
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/services":
                self.send_json(state.snapshot())
                return
            if self.path == "/health":
                self.send_json({"status": "ok"})
                return
            if self.path == "/" or self.path == "/index.html":
                self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
                return
            if self.path == "/app.js":
                self.send_file(STATIC_DIR / "app.js", "text/javascript; charset=utf-8")
                return
            if self.path == "/styles.css":
                self.send_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
                return
            self.send_error(404)

        def send_json(self, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_file(self, path, content_type):
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return DashboardHandler


def main():
    state = DashboardState(
        os.environ.get("TRAEFIK_API_URL", "https://traefik-homelab/api/http/routers"),
        os.environ.get("TRAEFIK_API_HOST", "traefik.home.arpa"),
        int(os.environ.get("REFRESH_SECONDS", "30")),
    )
    threading.Thread(target=refresh_loop, args=(state,), daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(state))
    server.serve_forever()


if __name__ == "__main__":
    main()