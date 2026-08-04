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
FIELD_ALIASES = {
    "name": {"name", "routername"},
}


def normalized_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def field_value(record, field, default=None):
    wanted = normalized_key(field)
    aliases = FIELD_ALIASES.get(wanted, {wanted})
    for key, value in record.items():
        if normalized_key(key) in aliases:
            return value
    return default


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
        labels = field_value(container, "labels", {}) or {}
        normalized_labels = {normalized_key(key): value for key, value in labels.items()}
        router_names = {
            key.split(".")[3]
            for key in labels
            if normalized_key(key).startswith("traefikhttprouters")
            and len(key.split(".")) >= 4
        }
        image, version = image_parts(field_value(container, "image", ""))
        state = field_value(container, "state")
        values = {
            "name": clean_metadata_value(normalized_labels.get(normalized_key(f"{LABEL_PREFIX}name"))),
            "icon": clean_metadata_value(normalized_labels.get(normalized_key(f"{LABEL_PREFIX}icon")), 40),
            "description": clean_metadata_value(normalized_labels.get(normalized_key(f"{LABEL_PREFIX}description")), 240),
            "category": clean_metadata_value(normalized_labels.get(normalized_key(f"{LABEL_PREFIX}category")), 60) or DEFAULT_CATEGORY,
            "container": clean_metadata_value((field_value(container, "names") or [""])[0].lstrip("/")),
            "image": image,
            "version": version,
            "status": "up" if state == "running" else "down" if state else "unknown",
        }
        for router_name in router_names:
            metadata[router_name] = values
    return metadata


def normalize_routers(routers, metadata=None, backend_statuses=None):
    metadata = metadata or {}
    backend_statuses = backend_statuses or {}
    services = {}
    for router in routers:
        provider = str(field_value(router, "provider", "")).lower()
        name = str(field_value(router, "name", ""))
        service = str(field_value(router, "service", ""))
        if provider != "docker" and not name.lower().endswith("@docker"):
            continue
        if service.lower() in {item.lower() for item in TECHNICAL_SERVICES}:
            continue
        for host in hostnames_from_rule(field_value(router, "rule", "")):
            if "*" in host or host in services:
                continue
            router_name = name.removesuffix("@docker")
            details = metadata.get(router_name, {})
            status = backend_statuses.get(service.lower(), details.get("status", "unknown"))
            services[host] = {
                "name": details.get("name") or display_name(host),
                "host": host,
                "url": f"https://{host}",
                "tls": field_value(router, "tls") is not None,
                "category": details.get("category") or DEFAULT_CATEGORY,
                "icon": details.get("icon", ""),
                "description": details.get("description", ""),
                "status": status,
                "container": details.get("container", ""),
                "image": details.get("image", ""),
                "version": details.get("version", ""),
            }
    return sorted(services.values(), key=lambda item: item["name"].lower())


def backend_statuses(services):
    statuses = {}
    for service in services:
        name = str(field_value(service, "name", "")).lower()
        status = str(field_value(service, "status", "")).lower()
        if status not in {"up", "down"}:
            server_status = field_value(service, "serverstatus", {}) or {}
            values = [str(value).lower() for value in server_status.values()]
            if values and all(value in {"up", "healthy", "running"} for value in values):
                status = "up"
            elif values and any(value in {"down", "unhealthy", "stopped"} for value in values):
                status = "down"
        if name and status in {"up", "down"}:
            statuses[name] = status
    return statuses


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
    header_bytes, body = response.split(b"\r\n\r\n", 1)
    headers = header_bytes.decode("iso-8859-1").lower()
    if "transfer-encoding: chunked" in headers:
        body = decode_chunked_body(body)
    return json.loads(body.decode("utf-8"))


def decode_chunked_body(body):
    decoded = bytearray()
    position = 0
    while True:
        line_end = body.find(b"\r\n", position)
        if line_end < 0:
            raise ValueError("Invalid chunked Docker response")
        size = int(body[position:line_end].split(b";", 1)[0], 16)
        position = line_end + 2
        if size == 0:
            return bytes(decoded)
        end = position + size
        if end + 2 > len(body) or body[end:end + 2] != b"\r\n":
            raise ValueError("Invalid chunked Docker response")
        decoded.extend(body[position:end])
        position = end + 2


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
        backend_state = {}
        services_url = self.api_url.rsplit("/", 1)[0] + "/services"
        try:
            with urlopen(Request(services_url, headers={"Host": self.api_host}), context=context, timeout=10) as response:
                service_payload = json.load(response)
            backend_state = backend_statuses(service_payload if isinstance(service_payload, list) else [])
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Traefik backend status refresh failed: {error}", flush=True)
        try:
            metadata = container_metadata(read_docker_containers(self.docker_socket))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Docker metadata refresh failed: {error}", flush=True)
            metadata = {}
        services = normalize_routers(routers, metadata, backend_state)
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