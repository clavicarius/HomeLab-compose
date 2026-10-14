#!/usr/bin/env python3
import os
import re
import subprocess
import sys


_HOST_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)


def build_host_rule(hosts, domain=""):
    entries = hosts.split(",")
    if not entries or any(not host.strip() for host in entries):
        raise ValueError("Host lists must not contain empty hostnames")

    normalized = []
    for entry in entries:
        hostname = entry.strip()
        if "." not in hostname and domain:
            hostname = f"{hostname}.{domain}"
        if not _HOST_PATTERN.fullmatch(hostname):
            raise ValueError(f"Invalid hostname: {entry.strip()}")
        if hostname not in normalized:
            normalized.append(hostname)

    return " || ".join(f"Host(`{hostname}`)" for hostname in normalized)


def read_env_file(path):
    values = {}
    try:
        with open(path, encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, separator, value = line.partition("=")
                if not separator:
                    continue
                key = key.strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                    continue
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key] = value
    except FileNotFoundError:
        pass
    return values


def env_file_arguments(arguments):
    paths = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--env-file" and index + 1 < len(arguments):
            paths.append(arguments[index + 1])
            index += 2
        elif argument.startswith("--env-file="):
            paths.append(argument.partition("=")[2])
            index += 1
        else:
            index += 1
    return paths


def add_host_rules(arguments, environment):
    config = {}
    for path in env_file_arguments(arguments):
        config.update(read_env_file(path))
    config.update(environment)

    domain = config.get("HOMELAB_DOMAIN", "")
    legacy_hosts = {
        "HOSTS": (
            "ADGUARD_HOST",
            "DASHBOARD_HOST",
            "FORGEJO_HOST",
            "GITEA_HOST",
            "PAPERLESS_HOST",
            "PORTAINER_HOST",
        ),
        "TRAEFIK_HOSTS": ("TRAEFIK_HOST",),
    }
    for name, candidates in legacy_hosts.items():
        if name in config:
            continue
        for candidate in candidates:
            if config.get(candidate):
                config[name] = config[candidate]
                break
    if "HOSTS" not in config and "DASHBOARD_IP" in config:
        config["HOSTS"] = "dashboard"
    if any(name.startswith("POLYPHP") and name.endswith("_IP") for name in config):
        for name, hostname in (
            ("PHP56_HOSTS", "php56"),
            ("PHP74_HOSTS", "php74"),
            ("PHP85_HOSTS", "php85"),
            ("PHPMYADMIN_HOSTS", "phpmyadmin"),
        ):
            config.setdefault(name, hostname)

    host_lists = {
        name: value for name, value in config.items()
        if name == "HOSTS" or name.endswith("_HOSTS")
    }
    for name, hosts in host_lists.items():
        if not hosts:
            raise ValueError(f"{name} must contain at least one hostname")
        rule_name = "HOST_RULE" if name == "HOSTS" else f"{name[:-6]}_HOST_RULE"
        environment[rule_name] = build_host_rule(hosts, domain)
    if "CERT_RESOLVER" not in config:
        environment.setdefault("CERT_RESOLVER", "stepca")
    if "STEP_CA_ACME_URL" not in config:
        environment.setdefault("STEP_CA_ACME_URL", "https://step-ca:9000/acme/acme/directory")


def main():
    arguments = sys.argv[1:]
    environment = os.environ.copy()
    try:
        add_host_rules(arguments, environment)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    return subprocess.run(["docker", "compose", *arguments], env=environment).returncode


if __name__ == "__main__":
    raise SystemExit(main())
