import unittest

from dashboard.server import container_metadata, display_name, hostnames_from_rule, normalize_routers


class DashboardNormalizerTests(unittest.TestCase):
    def test_extracts_hosts_from_host_rule(self):
        self.assertEqual(hostnames_from_rule("Host(`git.home.arpa`)") , ["git.home.arpa"])
        self.assertEqual(hostnames_from_rule("Host(`one.home.arpa`,`two.home.arpa`)") , ["one.home.arpa", "two.home.arpa"])

    def test_display_name_uses_host_label(self):
        self.assertEqual(display_name("php-my.home.arpa"), "Php My")

    def test_normalizes_only_docker_http_hosts_and_deduplicates(self):
        routers = [
            {"Name": "gitea@docker", "Provider": "docker", "Rule": "Host(`gitea.home.arpa`)", "Service": "gitea@docker", "TLS": {}},
            {"Name": "internal@file", "Provider": "file", "Rule": "Host(`traefik.home.arpa`)", "Service": "api@internal"},
            {"Name": "wildcard@docker", "Provider": "docker", "Rule": "HostRegexp(`{host:.+}.home.arpa`)", "Service": "wildcard@docker"},
            {"Name": "duplicate@docker", "Provider": "docker", "Rule": "Host(`gitea.home.arpa`)", "Service": "duplicate@docker"},
        ]
        self.assertEqual(normalize_routers(routers), [{"name": "Gitea", "host": "gitea.home.arpa", "url": "https://gitea.home.arpa", "tls": True, "category": "Other", "icon": "", "description": ""}])

    def test_container_metadata_reads_and_limits_homelab_labels(self):
        metadata = container_metadata([{
            "Labels": {
                "traefik.http.routers.gitea.rule": "Host(`gitea.home.arpa`)",
                "homelab.name": " Git ",
                "homelab.icon": "git",
                "homelab.description": "Source hosting",
                "homelab.category": "Development",
            }
        }])
        self.assertEqual(metadata["gitea"], {
            "name": "Git",
            "icon": "git",
            "description": "Source hosting",
            "category": "Development",
        })

    def test_normalizer_uses_metadata_without_changing_routing(self):
        routers = [{"Name": "gitea@docker", "Provider": "docker", "Rule": "Host(`gitea.home.arpa`)", "Service": "gitea@docker", "TLS": {}}]
        metadata = {"gitea": {"name": "Git", "icon": "git", "description": "Source hosting", "category": "Development"}}
        self.assertEqual(normalize_routers(routers, metadata)[0]["url"], "https://gitea.home.arpa")
        self.assertEqual(normalize_routers(routers, metadata)[0]["name"], "Git")


if __name__ == "__main__":
    unittest.main()