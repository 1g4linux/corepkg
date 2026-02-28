# Copyright 2013-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import multiprocessing

import corepkg
from corepkg import os
from corepkg.tests import TestCase
from corepkg.tests.resolver.ResolverPlayground import ResolverPlayground
from corepkg.package.ebuild._ipc.QueryCommand import QueryCommand
from corepkg.util._async.ForkProcess import ForkProcess
from corepkg.util._async.TaskScheduler import TaskScheduler
from _emerge.Package import Package
from _emerge.PipeReader import PipeReader


class DoebuildFdPipesTestCase(TestCase):
    output_fd = 200

    def _run_single_phase(self, ebuilds, cpv, phase):
        dev_null = open(os.devnull, "wb")
        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            QueryCommand._db = playground.trees
            root_config = playground.trees[playground.eroot]["root_config"]
            portdb = root_config.trees["porttree"].dbapi
            settings = corepkg.config(clone=playground.settings)
            settings.features.add("noauto")
            settings["PORTAGE_PYTHON"] = corepkg._python_interpreter
            settings["PORTAGE_QUIET"] = "1"

            metadata = dict(
                zip(Package.metadata_keys, portdb.aux_get(cpv, Package.metadata_keys))
            )
            pkg = Package(
                built=False,
                cpv=cpv,
                installed=False,
                metadata=metadata,
                root_config=root_config,
                type_name="ebuild",
            )
            settings.setcpv(pkg)

            ebuildpath = portdb.findname(cpv)
            self.assertNotEqual(ebuildpath, None)

            pr, pw = multiprocessing.Pipe(duplex=False)
            producer = ForkProcess(
                target=self._doebuild,
                fd_pipes={
                    1: dev_null.fileno(),
                },
                args=(QueryCommand._db, pw, ebuildpath, phase),
                kwargs={
                    "settings": settings,
                    "mydbapi": root_config.trees["porttree"].dbapi,
                    "tree": "porttree",
                    "vartree": root_config.trees["vartree"],
                    "prev_mtimes": {},
                },
            )
            consumer = PipeReader(input_files={"producer": pr})
            task_scheduler = TaskScheduler(iter([producer, consumer]), max_jobs=2)
            try:
                task_scheduler.start()
            finally:
                # PipeReader closes pr
                pw.close()

            task_scheduler.wait()
            output = corepkg._unicode_decode(consumer.getvalue()).rstrip("\n")
            return task_scheduler.returncode, output
        finally:
            dev_null.close()
            playground.cleanup()
            QueryCommand._db = None

    def testDefaultPhaseResolutionEapi8(self):
        """
        Verify default phase wiring under EAPI=8 for src_prepare and
        src_configure.
        """

        output_fd = self.output_fd
        ebuild_body = "\n".join(
            (
                "S=${WORKDIR}",
                f'src_prepare() {{ default; echo "${{EBUILD_PHASE_FUNC}}:${{EBUILD_PHASE}}" 1>&{output_fd}; }}',
                f'src_configure() {{ default; echo "${{EBUILD_PHASE_FUNC}}:${{EBUILD_PHASE}}" 1>&{output_fd}; }}',
                "",
            )
        )

        ebuilds = {
            "app-misct/default-phases-1": {
                "EAPI": "8",
                "MISC_CONTENT": ebuild_body,
            }
        }

        dev_null = open(os.devnull, "wb")
        playground = ResolverPlayground(ebuilds=ebuilds)
        try:
            QueryCommand._db = playground.trees
            root_config = playground.trees[playground.eroot]["root_config"]
            portdb = root_config.trees["porttree"].dbapi
            settings = corepkg.config(clone=playground.settings)
            settings.features.add("noauto")
            settings["PORTAGE_PYTHON"] = corepkg._python_interpreter
            settings["PORTAGE_QUIET"] = "1"

            cpv = "app-misct/default-phases-1"
            metadata = dict(
                zip(Package.metadata_keys, portdb.aux_get(cpv, Package.metadata_keys))
            )

            pkg = Package(
                built=False,
                cpv=cpv,
                installed=False,
                metadata=metadata,
                root_config=root_config,
                type_name="ebuild",
            )
            settings.setcpv(pkg)

            source_ebuildpath = portdb.findname(cpv)
            self.assertNotEqual(source_ebuildpath, None)

            expected_output = {
                "unpack": "",
                "prepare": "src_prepare:prepare",
                "configure": "src_configure:configure",
            }
            for phase in ("unpack", "prepare", "configure"):
                pr, pw = multiprocessing.Pipe(duplex=False)

                producer = ForkProcess(
                    target=self._doebuild,
                    fd_pipes={
                        1: dev_null.fileno(),
                    },
                    args=(QueryCommand._db, pw, source_ebuildpath, phase),
                    kwargs={
                        "settings": settings,
                        "mydbapi": root_config.trees["porttree"].dbapi,
                        "tree": "porttree",
                        "vartree": root_config.trees["vartree"],
                        "prev_mtimes": {},
                    },
                )

                consumer = PipeReader(input_files={"producer": pr})
                task_scheduler = TaskScheduler(iter([producer, consumer]), max_jobs=2)

                try:
                    task_scheduler.start()
                finally:
                    # PipeReader closes pr
                    pw.close()

                task_scheduler.wait()
                output = corepkg._unicode_decode(consumer.getvalue()).rstrip("\n")

                if task_scheduler.returncode != os.EX_OK:
                    corepkg.writemsg(output, noiselevel=-1)

                self.assertEqual(task_scheduler.returncode, os.EX_OK)
                self.assertEqual(output, expected_output[phase])
        finally:
            dev_null.close()
            playground.cleanup()
            QueryCommand._db = None

    def testEapi8ExpectedHelperUsexIsAvailable(self):
        output_fd = self.output_fd
        ebuilds = {
            "app-misct/helpers-1": {
                "EAPI": "8",
                "IUSE": "+foo",
                "MISC_CONTENT": "\n".join(
                    (
                        "S=${WORKDIR}",
                        f'pkg_setup() {{ echo "$(usex foo yes no)" 1>&{output_fd}; }}',
                        "",
                    )
                ),
            }
        }

        returncode, output = self._run_single_phase(
            ebuilds=ebuilds, cpv="app-misct/helpers-1", phase="setup"
        )
        self.assertEqual(returncode, os.EX_OK)
        self.assertEqual(output, "yes")

    def testEapi8BannedHelperHasqFails(self):
        ebuilds = {
            "app-misct/helpers-1": {
                "EAPI": "8",
                "MISC_CONTENT": "\n".join(
                    (
                        "S=${WORKDIR}",
                        "pkg_setup() { hasq foo foo; }",
                        "",
                    )
                ),
            }
        }

        returncode, _output = self._run_single_phase(
            ebuilds=ebuilds, cpv="app-misct/helpers-1", phase="setup"
        )
        self.assertNotEqual(returncode, os.EX_OK)

    def testEapi8EnvironmentExportSemantics(self):
        output_fd = self.output_fd
        ebuilds = {
            "app-misct/env-export-1": {
                "EAPI": "8",
                "MISC_CONTENT": "\n".join(
                    (
                        "S=${WORKDIR}",
                        "pkg_setup() {",
                        "  local var",
                        "  local missing=()",
                        "  local legacy_exported=()",
                        "  for var in EAPI EPREFIX EROOT BROOT; do",
                        "    declare -xp \"${var}\" >/dev/null 2>&1 || missing+=(\"${var}\")",
                        "  done",
                        "  for var in PORTDIR ECLASSDIR; do",
                        "    declare -xp \"${var}\" >/dev/null 2>&1 && legacy_exported+=(\"${var}\")",
                        "  done",
                        f"  echo \"missing=${{missing[*]}} legacy=${{legacy_exported[*]}}\" 1>&{output_fd}",
                        "  [[ ${#missing[@]} -eq 0 && ${#legacy_exported[@]} -eq 0 ]] || return 1",
                        "}",
                        "",
                    )
                ),
            }
        }

        returncode, output = self._run_single_phase(
            ebuilds=ebuilds, cpv="app-misct/env-export-1", phase="setup"
        )
        self.assertEqual(returncode, os.EX_OK)
        self.assertEqual(output, "missing= legacy=")

    def testDoebuild(self):
        """
        Invoke corepkg.doebuild() with the fd_pipes parameter, and
        check that the expected output appears in the pipe. This
        functionality is not used by corepkg internally, but it is
        supported for API consumers (see bug #475812).
        """

        output_fd = self.output_fd
        ebuild_body = ["S=${WORKDIR}"]
        for phase_func, default in (
            ("pkg_info", False),
            ("pkg_nofetch", False),
            ("pkg_pretend", False),
            ("pkg_setup", False),
            ("pkg_config", False),
            ("src_unpack", False),
            ("src_prepare", True),
            ("src_configure", False),
            ("src_compile", False),
            ("src_test", False),
            ("src_install", False),
        ):
            ebuild_body.append(
                ("%s() { %secho ${EBUILD_PHASE}" " 1>&%s; }")
                % (phase_func, "default; " if default else "", output_fd)
            )

        ebuild_body.append("")
        ebuild_body = "\n".join(ebuild_body)

        ebuilds = {
            "app-misct/foo-1": {
                "EAPI": "8",
                "IUSE": "+foo +bar",
                "REQUIRED_USE": "|| ( foo bar )",
                "MISC_CONTENT": ebuild_body,
            }
        }

        # Populate configdict["pkg"]["USE"] with something arbitrary in order
        # to try and trigger bug 675748 in doebuild _validate_deps.
        arbitrary_package_use = "baz"

        user_config = {
            # In order to trigger bug 675748, package.env must be non-empty,
            # but the referenced env file can be empty.
            "package.env": (f"app-misct/foo {os.devnull}",),
            "package.use": (f"app-misct/foo {arbitrary_package_use}",),
        }

        # Override things that may be unavailable, or may have portability
        # issues when running tests in exotic environments.
        #   prepstrip - bug #447810 (bash read builtin EINTR problem)
        true_symlinks = ("find", "prepstrip", "sed", "scanelf")
        true_binary = corepkg.process.find_binary("true")
        self.assertEqual(true_binary is None, False, "true command not found")

        dev_null = open(os.devnull, "wb")
        playground = ResolverPlayground(ebuilds=ebuilds, user_config=user_config)
        try:
            QueryCommand._db = playground.trees
            root_config = playground.trees[playground.eroot]["root_config"]
            portdb = root_config.trees["porttree"].dbapi
            settings = corepkg.config(clone=playground.settings)
            if "__PORTAGE_TEST_HARDLINK_LOCKS" in os.environ:
                settings["__PORTAGE_TEST_HARDLINK_LOCKS"] = os.environ[
                    "__PORTAGE_TEST_HARDLINK_LOCKS"
                ]
                settings.backup_changes("__PORTAGE_TEST_HARDLINK_LOCKS")

            settings.features.add("noauto")
            settings.features.add("test")
            settings["PORTAGE_PYTHON"] = corepkg._python_interpreter
            settings["PORTAGE_QUIET"] = "1"
            settings["PYTHONDONTWRITEBYTECODE"] = os.environ.get(
                "PYTHONDONTWRITEBYTECODE", ""
            )

            fake_bin = os.path.join(settings["EPREFIX"], "bin")
            corepkg.util.ensure_dirs(fake_bin)
            for x in true_symlinks:
                os.symlink(true_binary, os.path.join(fake_bin, x))

            settings["__PORTAGE_TEST_PATH_OVERRIDE"] = fake_bin
            settings.backup_changes("__PORTAGE_TEST_PATH_OVERRIDE")

            cpv = "app-misct/foo-1"
            metadata = dict(
                zip(Package.metadata_keys, portdb.aux_get(cpv, Package.metadata_keys))
            )

            pkg = Package(
                built=False,
                cpv=cpv,
                installed=False,
                metadata=metadata,
                root_config=root_config,
                type_name="ebuild",
            )
            settings.setcpv(pkg)

            # Demonstrate that settings.configdict["pkg"]["USE"] contains our arbitrary
            # package.use setting in order to trigger bug 675748.
            self.assertEqual(settings.configdict["pkg"]["USE"], arbitrary_package_use)

            # Try to trigger the config.environ() split_LC_ALL assertion for bug 925863.
            settings["LC_ALL"] = "C"

            source_ebuildpath = portdb.findname(cpv)
            self.assertNotEqual(source_ebuildpath, None)

            for phase, tree, ebuildpath in (
                ("info", "porttree", source_ebuildpath),
                ("nofetch", "porttree", source_ebuildpath),
                ("pretend", "porttree", source_ebuildpath),
                ("setup", "porttree", source_ebuildpath),
                ("unpack", "porttree", source_ebuildpath),
                ("prepare", "porttree", source_ebuildpath),
                ("configure", "porttree", source_ebuildpath),
                ("compile", "porttree", source_ebuildpath),
                ("test", "porttree", source_ebuildpath),
                ("install", "porttree", source_ebuildpath),
                ("qmerge", "porttree", source_ebuildpath),
                ("clean", "porttree", source_ebuildpath),
                ("merge", "porttree", source_ebuildpath),
                ("clean", "porttree", source_ebuildpath),
                ("config", "vartree", root_config.trees["vartree"].dbapi.findname(cpv)),
            ):
                if ebuildpath is not source_ebuildpath:
                    self.assertNotEqual(ebuildpath, None)

                pr, pw = multiprocessing.Pipe(duplex=False)

                producer = ForkProcess(
                    target=self._doebuild,
                    fd_pipes={
                        1: dev_null.fileno(),
                    },
                    args=(QueryCommand._db, pw, ebuildpath, phase),
                    kwargs={
                        "settings": settings,
                        "mydbapi": root_config.trees[tree].dbapi,
                        "tree": tree,
                        "vartree": root_config.trees["vartree"],
                        "prev_mtimes": {},
                    },
                )

                consumer = PipeReader(input_files={"producer": pr})

                task_scheduler = TaskScheduler(iter([producer, consumer]), max_jobs=2)

                try:
                    task_scheduler.start()
                finally:
                    # PipeReader closes pr
                    pw.close()

                task_scheduler.wait()
                output = corepkg._unicode_decode(consumer.getvalue()).rstrip("\n")

                if task_scheduler.returncode != os.EX_OK:
                    corepkg.writemsg(output, noiselevel=-1)

                self.assertEqual(task_scheduler.returncode, os.EX_OK)

                if phase not in ("clean", "merge", "qmerge"):
                    self.assertEqual(phase, output)

        finally:
            dev_null.close()
            playground.cleanup()
            QueryCommand._db = None

    @staticmethod
    def _doebuild(db, pw, *args, **kwargs):
        QueryCommand._db = db
        kwargs["fd_pipes"] = {
            DoebuildFdPipesTestCase.output_fd: pw.fileno(),
        }
        return corepkg.doebuild(*args, **kwargs)
