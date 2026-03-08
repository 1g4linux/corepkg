# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from corepkg import os
from corepkg.emaint.modules.move.move import MoveHandler
from corepkg.tests import TestCase


class MoveHandlerTestCase(TestCase):
    def testGrabGlobalUpdatesAccumulatesParseErrors(self):
        with tempfile.TemporaryDirectory() as tempdir:
            repo_paths = {}
            for repo_name in ("main", "overlay"):
                repo_path = f"{tempdir}/{repo_name}"
                repo_paths[repo_name] = repo_path
                updates_dir = f"{repo_path}/profiles/updates"

                os.makedirs(updates_dir)

            portdb = SimpleNamespace(
                getRepositories=lambda: ("main", "overlay"),
                getRepositoryPath=repo_paths.__getitem__,
                repositories=SimpleNamespace(
                    mainRepo=lambda: SimpleNamespace(name="main")
                ),
            )
            porttree = SimpleNamespace(dbapi=portdb)
            handler = MoveHandler(SimpleNamespace(), porttree)

            update_data = {
                f"{repo_paths['main']}/profiles/updates": (
                    ("2024-01", None, "main-1"),
                    ("2024-02", None, "main-2"),
                ),
                f"{repo_paths['overlay']}/profiles/updates": (
                    ("2024-03", None, "overlay-1"),
                ),
            }
            parsed_updates = {
                "main-1": ([("move", "dev-libs/a", "dev-libs/b")], ["main error 1"]),
                "main-2": (
                    [("slotmove", "dev-libs/c", "0", "1")],
                    ["main error 2"],
                ),
                "overlay-1": (
                    [("move", "dev-libs/d", "dev-libs/e")],
                    ["overlay error 1"],
                ),
            }

            with patch(
                "corepkg.update.grab_updates",
                side_effect=lambda path: update_data[path],
            ), patch(
                "corepkg.update.parse_updates",
                side_effect=lambda content: parsed_updates[content],
            ):
                updates, errors = handler._grab_global_updates()

        self.assertEqual(
            updates["main"],
            [
                ("move", "dev-libs/a", "dev-libs/b"),
                ("slotmove", "dev-libs/c", "0", "1"),
            ],
        )
        self.assertEqual(
            updates["overlay"], [("move", "dev-libs/d", "dev-libs/e")]
        )
        self.assertEqual(updates["DEFAULT"], updates["main"])
        self.assertEqual(
            errors, ["main error 1", "main error 2", "overlay error 1"]
        )
