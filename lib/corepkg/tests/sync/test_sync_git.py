# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from corepkg import os
from corepkg.sync.modules.git.git import (
    _get_oneg4_gitlab_sync_auth,
    _inject_oneg4_gitlab_sync_auth,
)
from corepkg.tests import TestCase


class SyncGitAuthTestCase(TestCase):
    def test_get_oneg4_gitlab_sync_auth(self):
        old_token = os.environ.get("ONEG4_GITLAB_TOKEN")
        old_owner_url = os.environ.get("ONEG4_GITLAB_OWNER_URL")
        try:
            os.environ["ONEG4_GITLAB_TOKEN"] = "token123"
            os.environ.pop("ONEG4_GITLAB_OWNER_URL", None)

            self.assertEqual(
                _get_oneg4_gitlab_sync_auth(
                    "https://gitlab.example.com/group/private-overlay.git"
                ),
                (
                    "http.https://gitlab.example.com/.extraHeader",
                    "Authorization: Bearer token123",
                ),
            )
            self.assertEqual(
                _get_oneg4_gitlab_sync_auth(
                    "https://gitlab.example.com:8443/group/private-overlay.git"
                ),
                (
                    "http.https://gitlab.example.com:8443/.extraHeader",
                    "Authorization: Bearer token123",
                ),
            )
            self.assertIsNone(
                _get_oneg4_gitlab_sync_auth(
                    "ssh://git@gitlab.example.com/group/private-overlay.git"
                )
            )
            self.assertIsNone(
                _get_oneg4_gitlab_sync_auth(
                    "https://example.com/group/private-overlay.git"
                )
            )

            settings = {"ONEG4_GITLAB_OWNER_URL": "https://gitlab.example.com/group"}
            self.assertEqual(
                _get_oneg4_gitlab_sync_auth(
                    "https://gitlab.example.com/group/private-overlay.git",
                    settings=settings,
                ),
                (
                    "http.https://gitlab.example.com/.extraHeader",
                    "Authorization: Bearer token123",
                ),
            )
            self.assertIsNone(
                _get_oneg4_gitlab_sync_auth(
                    "https://gitlab.example.com/other/private-overlay.git",
                    settings=settings,
                )
            )
        finally:
            if old_token is None:
                os.environ.pop("ONEG4_GITLAB_TOKEN", None)
            else:
                os.environ["ONEG4_GITLAB_TOKEN"] = old_token
            if old_owner_url is None:
                os.environ.pop("ONEG4_GITLAB_OWNER_URL", None)
            else:
                os.environ["ONEG4_GITLAB_OWNER_URL"] = old_owner_url

    def test_inject_oneg4_gitlab_sync_auth(self):
        old_token = os.environ.get("ONEG4_GITLAB_TOKEN")
        old_owner_url = os.environ.get("ONEG4_GITLAB_OWNER_URL")
        try:
            os.environ["ONEG4_GITLAB_TOKEN"] = "token123"
            os.environ.pop("ONEG4_GITLAB_OWNER_URL", None)
            uri = "https://gitlab.example.com/group/private-overlay.git"

            env = {}
            self.assertTrue(_inject_oneg4_gitlab_sync_auth(env, uri))
            self.assertEqual(env["GIT_CONFIG_COUNT"], "1")
            self.assertEqual(
                env["GIT_CONFIG_KEY_0"], "http.https://gitlab.example.com/.extraHeader"
            )
            self.assertEqual(
                env["GIT_CONFIG_VALUE_0"], "Authorization: Bearer token123"
            )

            # Idempotent with existing identical entry.
            self.assertTrue(_inject_oneg4_gitlab_sync_auth(env, uri))
            self.assertEqual(env["GIT_CONFIG_COUNT"], "1")

            # Appends after existing git config entries.
            env = {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.sslVerify",
                "GIT_CONFIG_VALUE_0": "true",
            }
            self.assertTrue(_inject_oneg4_gitlab_sync_auth(env, uri))
            self.assertEqual(env["GIT_CONFIG_COUNT"], "2")
            self.assertEqual(
                env["GIT_CONFIG_KEY_1"], "http.https://gitlab.example.com/.extraHeader"
            )
            self.assertEqual(
                env["GIT_CONFIG_VALUE_1"], "Authorization: Bearer token123"
            )

            # Ignore malformed existing GIT_CONFIG_COUNT.
            env = {"GIT_CONFIG_COUNT": "not-a-number"}
            self.assertFalse(_inject_oneg4_gitlab_sync_auth(env, uri))
            self.assertEqual(env, {"GIT_CONFIG_COUNT": "not-a-number"})

            # Respect owner URL restriction.
            settings = {
                "ONEG4_GITLAB_OWNER_URL": "https://gitlab.example.com/group"
            }
            env = {}
            self.assertTrue(
                _inject_oneg4_gitlab_sync_auth(
                    env, "https://gitlab.example.com/group/private-overlay.git", settings
                )
            )
            env = {}
            self.assertFalse(
                _inject_oneg4_gitlab_sync_auth(
                    env, "https://gitlab.example.com/other/private-overlay.git", settings
                )
            )
        finally:
            if old_token is None:
                os.environ.pop("ONEG4_GITLAB_TOKEN", None)
            else:
                os.environ["ONEG4_GITLAB_TOKEN"] = old_token
            if old_owner_url is None:
                os.environ.pop("ONEG4_GITLAB_OWNER_URL", None)
            else:
                os.environ["ONEG4_GITLAB_OWNER_URL"] = old_owner_url

    def test_inject_oneg4_gitlab_sync_auth_without_token(self):
        old_token = os.environ.get("ONEG4_GITLAB_TOKEN")
        try:
            os.environ.pop("ONEG4_GITLAB_TOKEN", None)

            env = {}
            self.assertFalse(
                _inject_oneg4_gitlab_sync_auth(
                    env, "https://gitlab.example.com/group/private-overlay.git"
                )
            )
            self.assertEqual(env, {})
        finally:
            if old_token is None:
                os.environ.pop("ONEG4_GITLAB_TOKEN", None)
            else:
                os.environ["ONEG4_GITLAB_TOKEN"] = old_token
