#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Empirical Challenge Test Suite: Dynamic Activation & Metric Isolation Stress
=============================================================================
Auditor: Challenger 2 (Metric Simulation & Dynamic Activation Challenger)
Target: multi_account_hub/hub_engine.py, data/negocios.json, scripts/centinela_refresh.py

Empirical Verifications:
1. Dynamic Activation: Does switching status to 'activo' automatically trigger
   metric refreshes without any engine code modification?
2. Metric Isolation: Do 100+ repeated calls to refresh_metrics() keep
   'en_preparacion' stores completely invariant at 75.0 pts and 'en_espera'?
3. CLI Invocation: Do 'refresh --all' and 'refresh --id steamfur-pro' exit with code 0?
4. Channel Purity: Are channels strictly limited to the Organic Triad with 0% TikTok?
5. Concurrency Resilience: Is atomic storage safe under concurrent refresh threads?
"""

import copy
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HUB_ROOT not in sys.path:
    sys.path.insert(0, HUB_ROOT)

from hub_engine import HubEngine, cli_main, INITIAL_BUSINESSES
from scripts import centinela_refresh


class TestChallengerActivationStress(unittest.TestCase):
    """Empirical challenge tests for dynamic activation, isolation, and CLI."""

    def setUp(self):
        """Creates an isolated temporary test database before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix="hub_challenger_test_")
        self.test_db_path = os.path.join(self.temp_dir, "negocios.json")

        # Load canonical seed businesses from data/negocios.json if available, else INITIAL_BUSINESSES
        canonical_path = os.path.join(HUB_ROOT, "data", "negocios.json")
        if os.path.exists(canonical_path):
            with open(canonical_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {
                "version": "1.0.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "total_businesses": len(INITIAL_BUSINESSES),
                "businesses": copy.deepcopy(INITIAL_BUSINESSES),
            }

        with open(self.test_db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.engine = HubEngine(data_path=self.test_db_path)

    def tearDown(self):
        """Cleans up temporary directory after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # Task 1: Dynamic Activation Simulation
    # =========================================================================
    def test_dynamic_activation_pickup_lifecycle(self):
        """
        Verify that changing a store from 'en_preparacion' to 'activo'
        is automatically picked up by refresh_metrics() without any code change.
        """
        # Step 1: Initial state - exactly 1 active business (steamfur-pro)
        initial_refreshed = self.engine.refresh_metrics()
        self.assertEqual(len(initial_refreshed), 1, "Initial refresh should only target 1 active business")
        self.assertEqual(initial_refreshed[0]["id"], "steamfur-pro")

        # Step 2: Switch 'prosmile-ultrasonic' to 'activo'
        updated_prosmile = self.engine.update_business(
            "prosmile-ultrasonic",
            {
                "status": "activo",
                "cluster_canales": {
                    "youtube_shorts": {"estado": "activo"},
                    "instagram_reels": {"estado": "activo"},
                    "facebook_reels": {"estado": "activo"},
                },
            },
        )
        self.assertEqual(updated_prosmile["status"], "activo")

        # Step 3: Call refresh_metrics() again
        second_refreshed = self.engine.refresh_metrics()
        refreshed_ids = {b["id"] for b in second_refreshed}
        self.assertEqual(
            len(second_refreshed),
            2,
            f"Expected exactly 2 active businesses after activation, got {len(second_refreshed)}",
        )
        self.assertEqual(refreshed_ids, {"steamfur-pro", "prosmile-ultrasonic"})

        # Verify that prosmile-ultrasonic received fresh refresh timestamps
        prosmile_refreshed = next(b for b in second_refreshed if b["id"] == "prosmile-ultrasonic")
        self.assertIsNotNone(prosmile_refreshed.get("refreshed_at"))
        self.assertIsNotNone(prosmile_refreshed.get("updated_at"))
        for ch_name in ["youtube_shorts", "instagram_reels", "facebook_reels"]:
            ch = prosmile_refreshed["cluster_canales"][ch_name]
            self.assertIn("ultimo_sondeo", ch)
            self.assertIsNotNone(ch["ultimo_sondeo"])

        # Step 4: Dynamically activate the remaining two stores
        self.engine.update_business("spinerelief-pro", {"status": "activo"})
        self.engine.update_business("aeroforce-x3", {"status": "activo"})

        all_refreshed = self.engine.refresh_metrics()
        self.assertEqual(len(all_refreshed), 4, "All 4 businesses should be refreshed when all are active")
        self.assertEqual(
            {b["id"] for b in all_refreshed},
            {"steamfur-pro", "prosmile-ultrasonic", "spinerelief-pro", "aeroforce-x3"},
        )

        # Step 5: Deactivate 'prosmile-ultrasonic' back to 'en_preparacion'
        self.engine.update_business("prosmile-ultrasonic", {"status": "en_preparacion"})
        reverted_refreshed = self.engine.refresh_metrics()
        self.assertEqual(len(reverted_refreshed), 3)
        self.assertNotIn("prosmile-ultrasonic", {b["id"] for b in reverted_refreshed})

    # =========================================================================
    # Task 2: Isolation Stress Test (En_preparacion Stores Protection)
    # =========================================================================
    def test_isolation_100_repeated_refreshes_en_preparacion_stores(self):
        """
        Confirm that 100 consecutive calls to refresh_metrics() do NOT modify
        or degrade 'en_preparacion' stores. Their health score must stay locked
        at 75.0 points and health_status at 'en_espera'.
        """
        # Read baseline state of all 'en_preparacion' stores
        initial_data = self.engine.storage.load()
        prep_ids = ["prosmile-ultrasonic", "spinerelief-pro", "aeroforce-x3"]

        prep_baselines = {}
        for b in initial_data["businesses"]:
            if b["id"] in prep_ids:
                prep_baselines[b["id"]] = copy.deepcopy(b)
                # Verify initial preconditions
                self.assertEqual(b["status"], "en_preparacion")
                self.assertEqual(b["metricas_resumen"]["account_health_score"], 75.0)
                self.assertEqual(b["metricas_resumen"]["health_status"], "en_espera")

        # Execute 100 repeated metric refreshes
        for cycle in range(100):
            res = self.engine.refresh_metrics()
            self.assertEqual(len(res), 1, f"Cycle {cycle}: Only active store should be returned")
            self.assertEqual(res[0]["id"], "steamfur-pro")

        # Reload from disk and verify isolation of en_preparacion stores
        final_data = self.engine.storage.load()
        for b in final_data["businesses"]:
            if b["id"] in prep_ids:
                baseline = prep_baselines[b["id"]]
                # 1. Health Score must be invariant
                self.assertEqual(
                    b["metricas_resumen"]["account_health_score"],
                    75.0,
                    f"Store {b['id']} health score degraded! Expected 75.0, got {b['metricas_resumen']['account_health_score']}",
                )
                # 2. Health Status must remain 'en_espera'
                self.assertEqual(
                    b["metricas_resumen"]["health_status"],
                    "en_espera",
                    f"Store {b['id']} health status altered! Expected 'en_espera', got {b['metricas_resumen']['health_status']}",
                )
                # 3. Status must remain 'en_preparacion'
                self.assertEqual(b["status"], "en_preparacion")
                # 4. Channels must remain paused
                for ch_name, ch_data in b["cluster_canales"].items():
                    self.assertEqual(ch_data["estado"], "pausado")
                    # ultimo_sondeo should NOT have been added or updated
                    self.assertEqual(ch_data.get("ultimo_sondeo"), baseline["cluster_canales"][ch_name].get("ultimo_sondeo"))
                # 5. Timestamps updated_at and refreshed_at must be untouched
                self.assertEqual(b.get("refreshed_at"), baseline.get("refreshed_at"))
                self.assertEqual(b.get("updated_at"), baseline.get("updated_at"))

    # =========================================================================
    # Task 3: CLI Command Invocations and Exit Code 0
    # =========================================================================
    def test_cli_refresh_all_exit_code_zero(self):
        """Test 'python hub_engine.py refresh --all' returns exit code 0."""
        code = cli_main(["--data-path", self.test_db_path, "refresh", "--all"])
        self.assertEqual(code, 0, f"CLI refresh --all returned non-zero code {code}")

    def test_cli_refresh_by_id_steamfur_exit_code_zero(self):
        """Test 'python hub_engine.py refresh --id steamfur-pro' returns exit code 0."""
        code = cli_main(["--data-path", self.test_db_path, "refresh", "--id", "steamfur-pro"])
        self.assertEqual(code, 0, f"CLI refresh --id steamfur-pro returned non-zero code {code}")

    def test_centinela_refresh_wrapper_exit_code_zero(self):
        """Test scripts/centinela_refresh.py wrapper execution."""
        orig_argv = sys.argv
        try:
            sys.argv = ["centinela_refresh.py", "--data-path", self.test_db_path]
            code = centinela_refresh.main()
            self.assertEqual(code, 0, f"centinela_refresh.main() returned {code}")
        finally:
            sys.argv = orig_argv

    def test_cli_live_subprocess_refresh_all(self):
        """
        Execute python hub_engine.py refresh --all via subprocess
        against the live production database to confirm real CLI behavior.
        """
        cmd = [sys.executable, "hub_engine.py", "refresh", "--all"]
        proc = subprocess.run(
            cmd,
            cwd=HUB_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"Command {cmd} failed with exit code {proc.returncode}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}",
        )
        self.assertIn("[OK] Refreshed metrics for 1 active business(es)", proc.stdout)
        self.assertIn("steamfur-pro", proc.stdout)

    def test_cli_live_subprocess_refresh_by_id(self):
        """
        Execute python hub_engine.py refresh --id steamfur-pro via subprocess
        against the live production database.
        """
        cmd = [sys.executable, "hub_engine.py", "refresh", "--id", "steamfur-pro"]
        proc = subprocess.run(
            cmd,
            cwd=HUB_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"Command {cmd} failed with exit code {proc.returncode}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}",
        )
        self.assertIn("[OK] Refreshed metrics for 'steamfur-pro'", proc.stdout)
        self.assertIn("YouTube Shorts", proc.stdout)
        self.assertIn("Instagram Reels", proc.stdout)
        self.assertIn("Facebook Reels", proc.stdout)

    # =========================================================================
    # Task 4: Organic Triad Channel Purity (Zero TikTok)
    # =========================================================================
    def test_triad_channel_purity_zero_tiktok(self):
        """
        Confirm that refreshed data structures adhere strictly to the 3 channels
        ('youtube_shorts', 'instagram_reels', 'facebook_reels') with zero TikTok.
        """
        # Refresh all
        refreshed = self.engine.refresh_metrics()
        for b in refreshed:
            channels = b.get("cluster_canales", {})
            # Must strictly have the 3 canonical keys
            self.assertEqual(
                set(channels.keys()),
                {"youtube_shorts", "instagram_reels", "facebook_reels"},
                f"Business {b['id']} channels mismatch: {channels.keys()}",
            )
            # Serialize business to string and ensure 'tiktok' is nowhere
            dumped = json.dumps(b).lower()
            self.assertNotIn("tiktok", dumped, f"Found 'tiktok' reference in business {b['id']}!")

    # =========================================================================
    # Task 5: Concurrency & Re-Entrancy Stress
    # =========================================================================
    def test_concurrent_refresh_threads(self):
        """Stress test 10 concurrent threads calling refresh_metrics()."""
        errors = []

        def worker():
            try:
                for _ in range(5):
                    self.engine.refresh_metrics()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent refresh encountered errors: {errors}")
        data = self.engine.storage.load()
        self.assertEqual(len(data["businesses"]), 4)


if __name__ == "__main__":
    unittest.main()
