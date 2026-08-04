import json
import os
import re
import socket
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


HOST_PATTERN = re.compile(r"Host\((?P<hosts>[^)]*)\)")
QUOTED_HOST = re.compile(r"[`\"](?P<host>[^`\"]+)[`\"]")
TECHNICAL_SERVICES = {"api@internal", "noop@internal"}
DEFAULT_CATEGORY = "Other"
DOCKER_SOCKET = "/var/run/docker.sock"
LABEL_PREFIX = "homelab."
STATIC_DIR = Path(__file__).parent / "static"


def hostnames_from_rule(rule):
    match = HOST_PATTERN.search(rule or "")
    if not match:
        return []
    return [item.group("host").strip() for item in QUOTED_HOST.finditer(match.group("hosts"))]


def display_name(host):
    label = host.split(".", 1)[0].replace("-", " ").replace("_", " ")
    return label.title()


def clean_metadata_value(value, maximum_length=120):
    if not isinstance(value, str):
        return ""
    return value.strip()[:maximum_length]


def image_parts(image):
    image = clean_metadata_value(image)
    if "@sha256:" in image:
        return image.split("@", 1)[0], image.split("@", 1)[1]
    image_name, separator, version = image.rpartition(":")
    if separator and "/" not in version:
        return image_name, version
    return image, ""


def container_metadata(containers):
    metadata = {}
    for container in containers:
        labels = container.get("Labels") or {}
        router_names = {
            key.split(".")[3]
            for key in labels
            if key.startswith("traefik.http.routers.")
            and key.count(".") >= 3
        }
        image, version = image_parts(container.get("Image", ""))
        state = container.get("State")
        values = {
            "name": clean_metadata_value(labels.get(f"{LABEL_PREFIX}name")),
            "icon": clean_metadata_value(labels.get(f"{LABEL_PREFIX}icon"), 40),
            "description": clean_metadata_value(labels.get(f"{LABEL_PREFIX}description"), 240),
            "category": clean_metadata_value(labels.get(f"{LABEL_PREFIX}category"), 60) or DEFAULT_CATEGORY,
            "container": clean_metadata_value((container.get("Names") or [""])[0].lstrip("/")),
            "image": image,
            "version": version,
            "status": "up" if state == "running" else "down" if state else "unknown",
        }
        for router_name in router_names:
            metadata[router_name] = values
    return metadata


def normalize_routers(routers, metadata=None):
    metadata = metadata or {}
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
            router_name = name.removesuffix("@docker")
            details = metadata.get(router_name, {})
            services[host] = {
                "name": details.get("name") or display_name(host),
                "host": host,
                "url": f"https://{host}",
                "tls": router.get("TLS") is not None,
                "category": details.get("category") or DEFAULT_CATEGORY,
                "icon": details.get("icon", ""),
                "description": details.get("description", ""),
                "status": details.get("status", "unknown"),
                "container": details.get("container", ""),
                "image": details.get("image", ""),
                "version": details.get("version", ""),
            }
    return sorted(services.values(), key=lambda item: item["name"].lower())


def read_docker_containers(socket_path=DOCKER_SOCKET):
    request = b"GET /containers/json?all=1 HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        connection.connect(socket_path)
        connection.sendall(request)
        response = b""
        while chunk := connection.recv(65536):
            response += chunk
    finally:
        connection.close()
    _, body = response.split(b"\r\n\r\n", 1)
    return json.loads(body)


class DashboardState:
    def __init__(self, api_url, api_host, refresh_seconds, docker_socket=DOCKER_SOCKET):
        self.api_url = api_url
        self.api_host = api_host
        self.refresh_seconds = refresh_seconds
        self.docker_socket = docker_socket
        self.services = []
        self.lock = threading.Lock()

    def update(self):
        request = Request(self.api_url, headers={"Host": self.api_host})
        context = ssl._create_unverified_context()
        with urlopen(request, context=context, timeout=10) as response:
            payload = json.load(response)
        routers = payload if isinstance(payload, list) else []
        try:
            metadata = container_metadata(read_docker_containers(self.docker_socket))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Docker metadata refresh failed: {error}", flush=True)
            metadata = {}
        services = normalize_routers(routers, metadata)
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
        os.environ.get("DOCKER_SOCKET", DOCKER_SOCKET),
    )
    threading.Thread(target=refresh_loop, args=(state,), daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(state))
    server.serve_forever()


if __name__ == "__main__":
    main()