"""Tests for ai_sys_buddy.telemetry."""

from __future__ import annotations

import unittest

from ai_sys_buddy import telemetry


class TelemetryTests(unittest.TestCase):
    def test_gather_hardware_keys(self) -> None:
        hardware = telemetry.gather_hardware()
        for key in ("os", "machine", "cpu", "cores", "ram_gb", "gpu", "python", "app"):
            self.assertIn(key, hardware)
        self.assertTrue(hardware["os"])
        self.assertIsInstance(hardware["gpu"], str)

    def test_build_record_computes_speed(self) -> None:
        metrics = {
            "eval_count": 100,
            "eval_duration": 1_000_000_000,
            "load_duration": 2_000_000_000,
        }
        hardware = {"os": "Linux", "cpu": "x", "cores": "4", "ram_gb": "16", "app": "0.1.3"}
        record = telemetry.build_record("mymodel", metrics, hardware)
        self.assertEqual(record["model"], "mymodel")
        self.assertEqual(record["tokens_per_second"], 100.0)
        self.assertEqual(record["load_duration_s"], 2.0)

    def test_build_record_without_metrics(self) -> None:
        record = telemetry.build_record("m", None, {"os": "Linux"})
        self.assertEqual(record["model"], "m")
        self.assertNotIn("tokens_per_second", record)

    def test_render_report_contains_model_and_speed(self) -> None:
        report = telemetry.render_report(
            "mymodel",
            telemetry.gather_hardware(),
            {"eval_count": 5, "eval_duration": 1_000_000_000},
        )
        self.assertIn("mymodel", report)
        self.assertIn("tok/s", report)


if __name__ == "__main__":
    unittest.main()
