import tempfile
import unittest
from pathlib import Path

from scripts.docker_compose import add_host_rules, build_host_rule


class BuildHostRuleTests(unittest.TestCase):
    def test_renders_multiple_fully_qualified_hosts(self):
        self.assertEqual(
            build_host_rule("git.homelab.internal,forgejo.homelab.internal"),
            "Host(`git.homelab.internal`) || Host(`forgejo.homelab.internal`)",
        )

    def test_appends_domain_to_short_hosts_and_removes_duplicates(self):
        self.assertEqual(
            build_host_rule("git,git", "homelab.internal"),
            "Host(`git.homelab.internal`)",
        )

    def test_rejects_empty_or_invalid_hosts(self):
        for hosts in ("", "git,", "bad host.homelab.internal"):
            with self.subTest(hosts=hosts), self.assertRaises(ValueError):
                build_host_rule(hosts, "homelab.internal")

    def test_renders_an_unbounded_host_list(self):
        hosts = ",".join(f"service-{index}.homelab.internal" for index in range(50))
        rule = build_host_rule(hosts)
        self.assertEqual(rule.count("Host("), 50)

    def test_builds_rules_from_compose_env_files(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "HOMELAB_DOMAIN=homelab.internal\n"
                "HOSTS=git.homelab.internal,forgejo\n",
                encoding="utf-8",
            )
            environment = {}
            add_host_rules(["--env-file", str(env_file)], environment)

        self.assertEqual(
            environment["HOST_RULE"],
            "Host(`git.homelab.internal`) || Host(`forgejo.homelab.internal`)",
        )

    def test_uses_existing_single_hostname_settings(self):
        environment = {
            "ADGUARD_HOST": "adguard",
            "HOMELAB_DOMAIN": "homelab.internal",
        }
        add_host_rules([], environment)
        self.assertEqual(environment["HOST_RULE"], "Host(`adguard.homelab.internal`)")

    def test_generates_service_specific_rules(self):
        environment = {
            "PHP56_HOSTS": "php56,legacy-php.homelab.internal",
            "HOMELAB_DOMAIN": "homelab.internal",
        }
        add_host_rules([], environment)
        self.assertEqual(
            environment["PHP56_HOST_RULE"],
            "Host(`php56.homelab.internal`) || Host(`legacy-php.homelab.internal`)",
        )


if __name__ == "__main__":
    unittest.main()
