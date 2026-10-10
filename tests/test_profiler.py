"""Tests for ai_sys_buddy.profiler."""

from __future__ import annotations

import unittest

from ai_sys_buddy import profiler


class ProfilerTests(unittest.TestCase):
    def test_tokens_per_second(self) -> None:
        metrics = {"eval_count": 100, "eval_duration": 1_000_000_000}
        self.assertAlmostEqual(profiler.tokens_per_second(metrics), 100.0)

    def test_tokens_per_second_missing(self) -> None:
        self.assertIsNone(profiler.tokens_per_second(None))
        self.assertIsNone(profiler.tokens_per_second({"eval_count": 5}))

    def test_format_without_metrics(self) -> None:
        self.assertIn("no metrics", profiler.format_metrics(None).lower())

    def test_format_with_metrics(self) -> None:
        metrics = {
            "load_duration": 2_000_000_000,
            "eval_count": 50,
            "eval_duration": 500_000_000,
            "total_duration": 3_000_000_000,
        }
        report = profiler.format_metrics(metrics)
        self.assertIn("Load duration : 2.000 s", report)
        self.assertIn("Speed         : 100.00 tok/s", report)


if __name__ == "__main__":
    unittest.main()
