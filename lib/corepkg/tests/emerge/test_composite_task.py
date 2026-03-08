# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from _emerge.CompositeTask import CompositeTask
from corepkg.tests import TestCase
from corepkg.util._eventloop.global_event_loop import global_event_loop


class _FakeBuilddirLock:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.unlock_calls = 0
        self.unlock_future = scheduler.create_future()

    def async_unlock(self):
        self.unlock_calls += 1
        return self.unlock_future


class _FakeCompositeTask(CompositeTask):
    __slots__ = ("_build_dir",)

    def _async_unlock_builddir(self, returncode=None):
        self._start_builddir_unlock("_build_dir", returncode=returncode)


class CompositeTaskTestCase(TestCase):
    def testStartBuilddirUnlockClearsLockAndGuardsReentry(self):
        scheduler = global_event_loop()
        builddir_lock = _FakeBuilddirLock(scheduler)
        task = _FakeCompositeTask(scheduler=scheduler, _build_dir=builddir_lock)

        task._async_unlock_builddir(returncode=17)

        self.assertIsNone(task._build_dir)
        self.assertIsNotNone(task._builddir_unlock_task)
        self.assertEqual(builddir_lock.unlock_calls, 1)
        self.assertRaises(AssertionError, task._async_unlock_builddir, 18)

        builddir_lock.unlock_future.set_result(None)
        scheduler.run_until_complete(task._current_task.async_wait())

        self.assertEqual(task.returncode, 17)
        self.assertIsNone(task._builddir_unlock_task)
