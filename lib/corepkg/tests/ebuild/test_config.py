# Copyright 2010-2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import tempfile

import corepkg
from corepkg import os, shutil, _encodings
from corepkg.const import USER_CONFIG_PATH
from corepkg.dep import Atom
from corepkg.package.ebuild.config import config
from corepkg.package.ebuild._config.LicenseManager import LicenseManager
from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import (
    ResolverPlayground,
    ResolverPlaygroundTestCase,
)
from corepkg.util import normalize_path


class ConfigTestCase(TestCase):
    def testFetchCommandEnvFilter(self):
        """
        Ensure fetch command overrides are not exported to phase environments.
        """
        tempdir = tempfile.mkdtemp()
        try:
            test_repo = os.path.join(tempdir, "var", "repositories", "test_repo")
            os.makedirs(os.path.join(test_repo, "profiles"))
            with open(os.path.join(test_repo, "profiles", "repo_name"), "w") as f:
                f.write("test_repo")

            env = {
                "PORTAGE_REPOSITORIES": "[DEFAULT]\nmain-repo = test_repo\n"
                "[test_repo]\nlocation = %s" % test_repo
            }

            # Tests may override corepkg.const.EPREFIX in order to
            # simulate a prefix installation.
            eprefix_orig = corepkg.const.EPREFIX
            corepkg.const.EPREFIX = tempdir
            try:
                settings = config(config_profile_path="", env=env, eprefix=tempdir)
            finally:
                corepkg.const.EPREFIX = eprefix_orig

            settings["FETCHCOMMAND_HTTPS_GITLAB_EXAMPLE_COM"] = "fetch-secret"
            settings["RESUMECOMMAND_HTTPS_GITLAB_EXAMPLE_COM"] = "resume-secret"
            settings["PORTAGE_FETCH_HTTP_HEADER_HTTPS_GITLAB_EXAMPLE_COM"] = (
                "Authorization: Bearer token"
            )
            settings["ONEG4_GITLAB_TOKEN"] = "token"
            settings["ONEG4_GITLAB_OWNER_URL"] = "https://gitlab.example.com/mygroup"

            env = settings.environ()
            self.assertNotIn("FETCHCOMMAND_HTTPS_GITLAB_EXAMPLE_COM", env)
            self.assertNotIn("RESUMECOMMAND_HTTPS_GITLAB_EXAMPLE_COM", env)
            self.assertNotIn("PORTAGE_FETCH_HTTP_HEADER_HTTPS_GITLAB_EXAMPLE_COM", env)
            self.assertNotIn("ONEG4_GITLAB_TOKEN", env)
            self.assertNotIn("ONEG4_GITLAB_OWNER_URL", env)
        finally:
            shutil.rmtree(tempdir)

    def testGitLabTokenGitConfig(self):
        """
        Ensure ONEG4_GITLAB_TOKEN triggers automatic GIT_CONFIG_* injection
        with Basic Auth and is itself filtered from the environment.
        """
        tempdir = tempfile.mkdtemp()
        try:
            test_repo = os.path.join(tempdir, "var", "repositories", "test_repo")
            os.makedirs(os.path.join(test_repo, "profiles"))
            with open(os.path.join(test_repo, "profiles", "repo_name"), "w") as f:
                f.write("test_repo")

            env = {
                "PORTAGE_REPOSITORIES": "[DEFAULT]\nmain-repo = test_repo\n"
                "[test_repo]\nlocation = %s" % test_repo
            }

            eprefix_orig = corepkg.const.EPREFIX
            corepkg.const.EPREFIX = tempdir
            try:
                settings = config(config_profile_path="", env=env, eprefix=tempdir)
            finally:
                corepkg.const.EPREFIX = eprefix_orig

            token = "my-secret-token"
            settings["ONEG4_GITLAB_TOKEN"] = token

            # Case 1: Default gitlab.com
            env = settings.environ()
            self.assertEqual(env.get("GIT_CONFIG_COUNT"), "1")
            self.assertEqual(
                env.get("GIT_CONFIG_KEY_0"), "http.https://gitlab.com/.extraHeader"
            )
            self.assertEqual(env.get("GIT_CONFIG_VALUE_0"), f"Authorization: Bearer {token}")
            # Ensure it's filtered from the shell environment
            self.assertNotIn("ONEG4_GITLAB_TOKEN", env)

            # Case 2: Custom owner URL
            settings["ONEG4_GITLAB_OWNER_URL"] = "https://git.example.com/group"
            env = settings.environ()
            self.assertEqual(env.get("GIT_CONFIG_COUNT"), "1")
            self.assertEqual(
                env.get("GIT_CONFIG_KEY_0"), "http.https://git.example.com/.extraHeader"
            )
            self.assertEqual(env.get("GIT_CONFIG_VALUE_0"), f"Authorization: Bearer {token}")
            self.assertNotIn("ONEG4_GITLAB_OWNER_URL", env)

            # Case 3: Preserving existing GIT_CONFIG_*
            settings["GIT_CONFIG_COUNT"] = "1"
            settings["GIT_CONFIG_KEY_0"] = "user.name"
            settings["GIT_CONFIG_VALUE_0"] = "Test User"
            env = settings.environ()
            self.assertEqual(env.get("GIT_CONFIG_COUNT"), "2")
            self.assertEqual(env.get("GIT_CONFIG_KEY_0"), "user.name")
            self.assertEqual(env.get("GIT_CONFIG_VALUE_0"), "Test User")
            self.assertEqual(
                env.get("GIT_CONFIG_KEY_1"), "http.https://git.example.com/.extraHeader"
            )
            self.assertEqual(env.get("GIT_CONFIG_VALUE_1"), f"Authorization: Bearer {token}")

        finally:
            shutil.rmtree(tempdir)

    def testMainRepoMissingDirectoryAllowed(self):
        """
        Ensure first-sync works when the configured main repo directory
        does not exist yet.
        """
        tempdir = tempfile.mkdtemp()
        try:
            bp_repo = os.path.join(tempdir, "var", "db", "repos", "bp")
            env = {
                "PORTAGE_REPOSITORIES": "[DEFAULT]\nmain-repo = bp\n"
                "[bp]\nlocation = %s\nsync-type = git\n"
                "sync-uri = https://github.com/1g4linux/bp.git"
                % bp_repo
            }

            # Tests may override corepkg.const.EPREFIX in order to
            # simulate a prefix installation.
            eprefix_orig = corepkg.const.EPREFIX
            corepkg.const.EPREFIX = tempdir
            try:
                settings = config(config_profile_path="", env=env, eprefix=tempdir)
            finally:
                corepkg.const.EPREFIX = eprefix_orig

            main_repo = settings.repositories.mainRepo()
            self.assertIsNotNone(main_repo)
            self.assertEqual(main_repo.name, "bp")
            self.assertEqual(main_repo.location, bp_repo)
        finally:
            shutil.rmtree(tempdir)

    def testMainRepoSyncUriOverrideFromMakeConf(self):
        """
        Ensure PORTAGE_MAIN_REPO_SYNC_URI in make.conf overrides repos.conf.
        """
        tempdir = tempfile.mkdtemp()
        try:
            etc_dir = os.path.join(tempdir, "etc")
            os.makedirs(etc_dir)

            sync_uri = "https://gitlab.example.com/group/private-overlay.git"
            with open(os.path.join(etc_dir, "make.conf"), "w") as f:
                f.write(f'PORTAGE_MAIN_REPO_SYNC_URI="{sync_uri}"\n')

            bp_repo = os.path.join(tempdir, "var", "db", "repos", "bp")
            env = {
                "PORTAGE_REPOSITORIES": "[DEFAULT]\nmain-repo = bp\n"
                "[bp]\nlocation = %s\nsync-type = git\n"
                "sync-uri = https://github.com/1g4linux/bp.git"
                % bp_repo
            }

            eprefix_orig = corepkg.const.EPREFIX
            corepkg.const.EPREFIX = tempdir
            try:
                settings = config(
                    config_profile_path="",
                    config_root=tempdir,
                    env=env,
                    eprefix=tempdir,
                )
            finally:
                corepkg.const.EPREFIX = eprefix_orig

            main_repo = settings.repositories.mainRepo()
            self.assertIsNotNone(main_repo)
            self.assertEqual(main_repo.sync_uri, sync_uri)
            self.assertNotIn("PORTAGE_MAIN_REPO_SYNC_URI", settings.environ())
        finally:
            shutil.rmtree(tempdir)

    def testPrivateOverlaySyncUriAutoOverlayFromMakeConf(self):
        """
        Ensure PORTAGE_PRIVATE_OVERLAY_SYNC_URI creates/updates private-overlay
        as an overlay of the configured main repo.
        """
        tempdir = tempfile.mkdtemp()
        try:
            etc_dir = os.path.join(tempdir, "etc")
            os.makedirs(etc_dir)

            sync_uri = "https://gitlab.example.com/group/private-overlay.git"
            with open(os.path.join(etc_dir, "make.conf"), "w") as f:
                f.write(f'PORTAGE_PRIVATE_OVERLAY_SYNC_URI="{sync_uri}"\n')

            public_repo = os.path.join(tempdir, "var", "db", "repos", "public")
            env = {
                "PORTAGE_REPOSITORIES": "[DEFAULT]\nmain-repo = public\n"
                "[public]\nlocation = %s\nsync-type = git\n"
                "sync-uri = https://github.com/example/public-overlay.git"
                % public_repo
            }

            eprefix_orig = corepkg.const.EPREFIX
            corepkg.const.EPREFIX = tempdir
            try:
                settings = config(
                    config_profile_path="",
                    config_root=tempdir,
                    env=env,
                    eprefix=tempdir,
                )
            finally:
                corepkg.const.EPREFIX = eprefix_orig

            private_repo = settings.repositories["private-overlay"]
            self.assertEqual(private_repo.sync_type, "git")
            self.assertEqual(private_repo.sync_uri, sync_uri)
            self.assertEqual(
                private_repo.location,
                os.path.join(tempdir, "var", "db", "repos", "private-overlay"),
            )
            self.assertEqual(
                tuple(master.name for master in private_repo.masters), ("public",)
            )
            self.assertNotIn("PORTAGE_PRIVATE_OVERLAY_SYNC_URI", settings.environ())
        finally:
            shutil.rmtree(tempdir)

    def testClone(self):
        """
        Test the clone via constructor.
        """

        ebuilds = {
            "dev-libs/A-1": {},
        }

        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            settings = config(clone=playground.settings)
            result = playground.run(["=dev-libs/A-1"])
            pkg, existing_node = result.depgraph._select_package(
                playground.eroot, Atom("=dev-libs/A-1")
            )
            settings.setcpv(pkg)

            # clone after setcpv tests deepcopy of LazyItemsDict
            settings2 = config(clone=settings)
        finally:
            playground.cleanup()

    def testFeaturesMutation(self):
        """
        Test whether mutation of config.features updates the FEATURES
        variable and persists through config.regenerate() calls. Also
        verify that features_set._prune_overrides() works correctly.
        """
        playground = ResolverPlayground()
        try:
            settings = config(clone=playground.settings)

            settings.features.add("noclean")
            self.assertEqual("noclean" in settings["FEATURES"].split(), True)
            settings.regenerate()
            self.assertEqual("noclean" in settings["FEATURES"].split(), True)

            settings.features.discard("noclean")
            self.assertEqual("noclean" in settings["FEATURES"].split(), False)
            settings.regenerate()
            self.assertEqual("noclean" in settings["FEATURES"].split(), False)

            settings.features.add("noclean")
            self.assertEqual("noclean" in settings["FEATURES"].split(), True)
            settings.regenerate()
            self.assertEqual("noclean" in settings["FEATURES"].split(), True)

            # before: ['noclean', '-noclean', 'noclean']
            settings.features._prune_overrides()
            #  after: ['noclean']
            self.assertEqual(settings._features_overrides.count("noclean"), 1)
            self.assertEqual(settings._features_overrides.count("-noclean"), 0)

            settings.features.remove("noclean")

            # before: ['noclean', '-noclean']
            settings.features._prune_overrides()
            #  after: ['-noclean']
            self.assertEqual(settings._features_overrides.count("noclean"), 0)
            self.assertEqual(settings._features_overrides.count("-noclean"), 1)
        finally:
            playground.cleanup()

    _testLicenseManagerPackageLicense = (
        "dev-libs/* TEST",
        "dev-libs/A -TEST2",
        "=dev-libs/A-2 TEST3 @TEST",
        "*/* @EULA TEST2",
        "=dev-libs/C-1 *",
        "=dev-libs/C-2 -*",
    )

    def _testLicenseManager(self, lic_man):
        self.assertEqual(lic_man._accept_license_str, None)
        self.assertEqual(lic_man._accept_license, None)
        self.assertEqual(lic_man._license_groups, {"EULA": frozenset(["TEST"])})
        self.assertEqual(lic_man._undef_lic_groups, {"TEST"})

        self.assertEqual(lic_man.extract_global_changes(), "TEST TEST2")
        self.assertEqual(lic_man.extract_global_changes(), "")

        lic_man.set_accept_license_str("TEST TEST2")
        self.assertEqual(
            lic_man._getPkgAcceptLicense("dev-libs/B-1", "0", None),
            ["TEST", "TEST2", "TEST"],
        )
        self.assertEqual(
            lic_man._getPkgAcceptLicense("dev-libs/A-1", "0", None),
            ["TEST", "TEST2", "TEST", "-TEST2"],
        )
        self.assertEqual(
            lic_man._getPkgAcceptLicense("dev-libs/A-2", "0", None),
            ["TEST", "TEST2", "TEST", "-TEST2", "TEST3", "@TEST"],
        )

        self.assertEqual(
            lic_man.get_pruned_accept_license("dev-libs/B-1", [], "TEST", "0", None),
            "TEST",
        )
        self.assertEqual(
            lic_man.get_pruned_accept_license("dev-libs/A-1", [], "-TEST2", "0", None),
            "",
        )
        self.assertEqual(
            lic_man.get_pruned_accept_license(
                "dev-libs/A-2", [], "|| ( TEST TEST2 )", "0", None
            ),
            "TEST",
        )
        self.assertEqual(
            lic_man.get_pruned_accept_license("dev-libs/C-1", [], "TEST5", "0", None),
            "TEST5",
        )
        self.assertEqual(
            lic_man.get_pruned_accept_license("dev-libs/C-2", [], "TEST2", "0", None),
            "",
        )

        self.assertEqual(
            lic_man.getMissingLicenses("dev-libs/B-1", [], "TEST", "0", None), []
        )
        self.assertEqual(
            lic_man.getMissingLicenses("dev-libs/A-1", [], "-TEST2", "0", None),
            ["-TEST2"],
        )
        self.assertEqual(
            lic_man.getMissingLicenses(
                "dev-libs/A-2", [], "|| ( TEST TEST2 )", "0", None
            ),
            [],
        )
        self.assertEqual(
            lic_man.getMissingLicenses(
                "dev-libs/A-3", [], "|| ( TEST2 || ( TEST3 TEST4 ) )", "0", None
            ),
            ["TEST2", "TEST3", "TEST4"],
        )
        self.assertEqual(
            lic_man.getMissingLicenses("dev-libs/C-1", [], "TEST5", "0", None), []
        )
        self.assertEqual(
            lic_man.getMissingLicenses("dev-libs/C-2", [], "TEST2", "0", None),
            ["TEST2"],
        )
        self.assertEqual(
            lic_man.getMissingLicenses("dev-libs/D-1", [], "", "0", None), []
        )

    def testLicenseManager(self):
        user_config = {
            "package.license": self._testLicenseManagerPackageLicense,
        }

        playground = ResolverPlayground(user_config=user_config)
        settings = config(clone=playground.settings)
        try:
            corepkg.util.noiselimit = -2

            lic_man = LicenseManager(settings._locations_manager)
            self._testLicenseManager(lic_man)

        finally:
            corepkg.util.noiselimit = 0
            playground.cleanup()

    def testLicenseManagerProfile(self):
        repo_configs = {
            "test_repo": {
                "layout.conf": ("profile-formats = profile-license",),
            }
        }
        profile_configs = {
            "package.license": self._testLicenseManagerPackageLicense,
        }

        playground = ResolverPlayground(
            repo_configs=repo_configs, profile=profile_configs
        )
        settings = config(clone=playground.settings)
        try:
            corepkg.util.noiselimit = -2

            lic_man = LicenseManager(settings._locations_manager)
            self._testLicenseManager(lic_man)

        finally:
            corepkg.util.noiselimit = 0
            playground.cleanup()

    def testLicenseManagerMixed(self):
        profile_configs = {
            "package.license": self._testLicenseManagerPackageLicense[:4],
        }
        user_configs = {
            "package.license": self._testLicenseManagerPackageLicense[4:],
        }
        repo_configs = {
            "test_repo": {
                "layout.conf": ("profile-formats = profile-license",),
            }
        }

        playground = ResolverPlayground(
            user_config=user_configs, repo_configs=repo_configs, profile=profile_configs
        )
        settings = config(clone=playground.settings)
        try:
            corepkg.util.noiselimit = -2

            lic_man = LicenseManager(settings._locations_manager)
            self._testLicenseManager(lic_man)

        finally:
            corepkg.util.noiselimit = 0
            playground.cleanup()

    def testPackageMaskOrder(self):
        ebuilds = {
            "dev-libs/A-1": {},
            "dev-libs/B-1": {},
            "dev-libs/C-1": {},
            "dev-libs/D-1": {},
            "dev-libs/E-1": {},
        }

        repo_configs = {
            "test_repo": {
                "package.mask": (
                    "dev-libs/A",
                    "dev-libs/C",
                ),
            }
        }

        profile = {
            "package.mask": (
                "-dev-libs/A",
                "dev-libs/B",
                "-dev-libs/B",
                "dev-libs/D",
            ),
        }

        user_config = {
            "package.mask": (
                "-dev-libs/C",
                "-dev-libs/D",
                "dev-libs/E",
            ),
        }

        test_cases = (
            ResolverPlaygroundTestCase(
                ["dev-libs/A"], options={"--autounmask": "n"}, success=False
            ),
            ResolverPlaygroundTestCase(
                ["dev-libs/B"], success=True, mergelist=["dev-libs/B-1"]
            ),
            ResolverPlaygroundTestCase(
                ["dev-libs/C"], success=True, mergelist=["dev-libs/C-1"]
            ),
            ResolverPlaygroundTestCase(
                ["dev-libs/D"], success=True, mergelist=["dev-libs/D-1"]
            ),
            ResolverPlaygroundTestCase(
                ["dev-libs/E"], options={"--autounmask": "n"}, success=False
            ),
        )

        playground = ResolverPlayground(
            ebuilds=ebuilds,
            repo_configs=repo_configs,
            profile=profile,
            user_config=user_config,
        )
        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def testManifest(self):
        distfiles = {
            "B-2.tar.bz2": b"binary\0content",
            "C-2.zip": b"binary\0content",
            "C-2.tar.bz2": b"binary\0content",
        }

        ebuilds = {
            "dev-libs/A-1::old_repo": {},
            "dev-libs/A-2::new_repo": {},
            "dev-libs/B-2::new_repo": {"SRC_URI": "B-2.tar.bz2"},
            "dev-libs/C-2::new_repo": {"SRC_URI": "C-2.zip C-2.tar.bz2"},
        }

        repo_configs = {
            "new_repo": {
                "layout.conf": (
                    "profile-formats = pms",
                    "thin-manifests = true",
                    "manifest-hashes = SHA256 SHA512",
                    "manifest-required-hashes = SHA512",
                    "# use implicit masters",
                ),
            }
        }

        test_cases = (
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-1"], mergelist=["dev-libs/A-1"], success=True
            ),
            ResolverPlaygroundTestCase(
                ["=dev-libs/A-2"], mergelist=["dev-libs/A-2"], success=True
            ),
        )

        playground = ResolverPlayground(
            ebuilds=ebuilds, repo_configs=repo_configs, distfiles=distfiles
        )
        settings = playground.settings

        new_repo_config = settings.repositories["new_repo"]
        old_repo_config = settings.repositories["old_repo"]
        self.assertTrue(
            len(new_repo_config.masters) > 0, "new_repo has no default master"
        )
        self.assertEqual(
            new_repo_config.masters[0].location,
            playground.settings.repositories["test_repo"].location,
            "new_repo default master is not test_repo",
        )
        self.assertEqual(
            new_repo_config.thin_manifest, True, "new_repo_config.thin_manifest != True"
        )

        new_manifest_file = os.path.join(
            new_repo_config.location, "dev-libs", "A", "Manifest"
        )
        self.assertNotExists(new_manifest_file)

        new_manifest_file = os.path.join(
            new_repo_config.location, "dev-libs", "B", "Manifest"
        )
        f = open(new_manifest_file)
        self.assertEqual(len(list(f)), 1)
        f.close()

        new_manifest_file = os.path.join(
            new_repo_config.location, "dev-libs", "C", "Manifest"
        )
        f = open(new_manifest_file)
        self.assertEqual(len(list(f)), 2)
        f.close()

        old_manifest_file = os.path.join(
            old_repo_config.location, "dev-libs", "A", "Manifest"
        )
        f = open(old_manifest_file)
        self.assertEqual(len(list(f)), 1)
        f.close()

        try:
            for test_case in test_cases:
                playground.run_TestCase(test_case)
                self.assertEqual(test_case.test_success, True, test_case.fail_msg)
        finally:
            playground.cleanup()

    def testSetCpv(self):
        """
        Test the clone via constructor.
        """

        ebuilds = {
            "dev-libs/A-1": {"IUSE": "static-libs"},
            "dev-libs/B-1": {"IUSE": "static-libs"},
        }

        env_files = {"A": ('USE="static-libs"',)}

        package_env = ("dev-libs/A A",)

        eprefix = normalize_path(tempfile.mkdtemp())
        playground = None
        try:
            user_config_dir = os.path.join(eprefix, USER_CONFIG_PATH)
            os.makedirs(user_config_dir)

            with open(
                os.path.join(user_config_dir, "package.env"),
                mode="w",
                encoding=_encodings["content"],
            ) as f:
                for line in package_env:
                    f.write(line + "\n")

            env_dir = os.path.join(user_config_dir, "env")
            os.makedirs(env_dir)
            for k, v in env_files.items():
                with open(
                    os.path.join(env_dir, k), mode="w", encoding=_encodings["content"]
                ) as f:
                    for line in v:
                        f.write(line + "\n")

            playground = ResolverPlayground(eprefix=eprefix, ebuilds=ebuilds)
            settings = config(clone=playground.settings)

            result = playground.run(["=dev-libs/A-1"])
            pkg, existing_node = result.depgraph._select_package(
                playground.eroot, Atom("=dev-libs/A-1")
            )
            settings.setcpv(pkg)
            self.assertTrue("static-libs" in settings["PORTAGE_USE"].split())

            # Test bug #522362, where a USE=static-libs package.env
            # setting leaked from one setcpv call to the next.
            pkg, existing_node = result.depgraph._select_package(
                playground.eroot, Atom("=dev-libs/B-1")
            )
            settings.setcpv(pkg)
            self.assertTrue("static-libs" not in settings["PORTAGE_USE"].split())

        finally:
            if playground is None:
                shutil.rmtree(eprefix)
            else:
                playground.cleanup()
