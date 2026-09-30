#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adversarial Inmutability & Edge-Case Test Suite — Multi-Account Hub
==================================================================
Empirically verifies:
1. Inmutability Shield (§ 7) and diff gates.
2. Git staging safety (git add data/negocios.json exclusively, zero git add -A).
3. Zero-metric-change handling (git diff --staged --quiet).
4. Edge cases & data resilience (malformed JSON, 0-byte file, missing fields, atomic persistence).
5. TikTok eradication verification across workflows and scripts.

Created by: challenger_1 (Adversarial Inmutability & Edge-Case Challenger)
"""

import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure multi_account_hub is importable
HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HUB_ROOT not in sys.path:
    sys.path.insert(0, HUB_ROOT)

from hub_engine import (
    BusinessStorage,
    HealthScorer,
    HubEngine,
    cli_main,
)


class TestAdversarialInmutabilityWorkflow(unittest.TestCase):
    """Adversarial verification of .github/workflows/centinela_metricas.yml."""

    def setUp(self):
        self.workflow_path = os.path.join(HUB_ROOT, ".github", "workflows", "centinela_metricas.yml")
        self.assertTrue(os.path.exists(self.workflow_path), f"Workflow not found at {self.workflow_path}")
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            self.workflow_content = f.read()

    def test_workflow_schedule_and_dispatch(self):
        """Verify daily schedule at 12:00 UTC (06:00 AM CST) and workflow_dispatch."""
        self.assertIn("cron: '0 12 * * *'", self.workflow_content)
        self.assertIn("workflow_dispatch:", self.workflow_content)
        self.assertIn("contents: write", self.workflow_content)

    def test_workflow_step5_diff_gate_command(self):
        """Verify the exact diff gate command in step 5."""
        gate_pattern = r"if\s+!\s+git\s+diff\s+--quiet\s+index\.html\s+hub_engine\.py;\s*then"
        match = re.search(gate_pattern, self.workflow_content)
        self.assertIsNotNone(match, "Diff gate 'if ! git diff --quiet index.html hub_engine.py; then' missing from workflow")
        self.assertIn("exit 1", self.workflow_content)

    def test_workflow_step5_fatal_abort_no_continue_on_error(self):
        """Verify step 5 lacks continue-on-error, ensuring fatal workflow abort on violation."""
        # Find step 5 block
        step5_idx = self.workflow_content.find("Blindaje Constitucional de Inmutabilidad")
        self.assertGreater(step5_idx, -1)
        step6_idx = self.workflow_content.find("Post-run Test Check", step5_idx)
        step5_block = self.workflow_content[step5_idx:step6_idx] if step6_idx != -1 else self.workflow_content[step5_idx:]

        self.assertNotIn("continue-on-error: true", step5_block)
        self.assertNotIn("continue-on-error: 'true'", step5_block)

    def test_workflow_staging_strictly_negocios_json(self):
        """Verify that step 7 exclusively stages data/negocios.json."""
        self.assertIn("git add data/negocios.json", self.workflow_content)
        # Verify prohibited blanket staging commands are absent
        prohibited = [
            "git add -A",
            "git add .",
            "git add --all",
            "git commit -a",
            "git commit -am",
            "git add *",
        ]
        for bad_cmd in prohibited:
            self.assertNotIn(bad_cmd, self.workflow_content, f"Prohibited command '{bad_cmd}' found in workflow!")

    def test_workflow_zero_diff_quiet_guard(self):
        """Verify git diff --staged --quiet guard prevents empty commits."""
        self.assertIn("git diff --staged --quiet", self.workflow_content)
        guard_pattern = r"if\s+git\s+diff\s+--staged\s+--quiet;\s*then"
        match = re.search(guard_pattern, self.workflow_content)
        self.assertIsNotNone(match, "Zero-diff guard 'if git diff --staged --quiet; then' missing")

    def test_workflow_no_tiktok_presence(self):
        """Verify zero occurrences of 'tiktok' in workflow."""
        self.assertNotIn("tiktok", self.workflow_content.lower())


class TestEmpiricalGitDiffGatesAndStaging(unittest.TestCase):
    """Empirical git execution in temporary isolated git repositories."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="git_adv_test_")
        self._init_git_repo()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_git(self, args, check=True):
        res = subprocess.run(
            ["git"] + args,
            cwd=self.test_dir,
            capture_output=True,
            text=True,
        )
        if check and res.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(args)}\nStdout: {res.stdout}\nStderr: {res.stderr}")
        return res

    def _init_git_repo(self):
        """Initialize a mock repository mirroring multi_account_hub."""
        self._run_git(["init"])
        self._run_git(["config", "user.name", "Test Runner"])
        self._run_git(["config", "user.email", "test@example.com"])

        # Create data directory and baseline files
        os.makedirs(os.path.join(self.test_dir, "data"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "scripts"), exist_ok=True)

        with open(os.path.join(self.test_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body>ORIGINAL UI</body></html>")

        with open(os.path.join(self.test_dir, "hub_engine.py"), "w", encoding="utf-8") as f:
            f.write("# ORIGINAL HUB ENGINE\nSCHEMA_VERSION = '1.0.0'\n")

        with open(os.path.join(self.test_dir, "data", "negocios.json"), "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "businesses": []}, f)

        # Baseline commit
        self._run_git(["add", "index.html", "hub_engine.py", "data/negocios.json"])
        self._run_git(["commit", "-m", "chore: initial baseline commit"])

    def test_diff_gate_returns_zero_when_clean(self):
        """Empirical verification: diff gate returns 0 when index.html and hub_engine.py are untouched."""
        res = self._run_git(["diff", "--quiet", "index.html", "hub_engine.py"], check=False)
        self.assertEqual(res.returncode, 0, "Diff gate should return 0 on clean baseline")

    def test_diff_gate_fails_when_index_html_modified(self):
        """Empirical verification: diff gate returns 1 when index.html is modified."""
        with open(os.path.join(self.test_dir, "index.html"), "a", encoding="utf-8") as f:
            f.write("\n<!-- UNAUTHORIZED MODIFICATION -->")

        res = self._run_git(["diff", "--quiet", "index.html", "hub_engine.py"], check=False)
        self.assertEqual(res.returncode, 1, "Diff gate must return 1 when index.html is altered")

    def test_diff_gate_fails_when_hub_engine_modified(self):
        """Empirical verification: diff gate returns 1 when hub_engine.py is modified."""
        with open(os.path.join(self.test_dir, "hub_engine.py"), "a", encoding="utf-8") as f:
            f.write("\n# ROGUE CODE INJECTION")

        res = self._run_git(["diff", "--quiet", "index.html", "hub_engine.py"], check=False)
        self.assertEqual(res.returncode, 1, "Diff gate must return 1 when hub_engine.py is altered")

    def test_diff_gate_does_not_trip_on_data_negocios_modification(self):
        """Empirical verification: diff gate ignores intentional data/negocios.json updates."""
        with open(os.path.join(self.test_dir, "data", "negocios.json"), "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "businesses": [{"id": "steamfur-pro"}]}, f)

        res = self._run_git(["diff", "--quiet", "index.html", "hub_engine.py"], check=False)
        self.assertEqual(res.returncode, 0, "Diff gate must ignore data/negocios.json updates")

    def test_staging_isolation_strictly_negocios_json(self):
        """
        Empirical verification: git add data/negocios.json stages ONLY data/negocios.json,
        even when dirty untracked files and modified UI files exist in working tree.
        """
        # Modify index.html
        with open(os.path.join(self.test_dir, "index.html"), "a", encoding="utf-8") as f:
            f.write("\n<!-- DIRTY UI EDIT -->")

        # Create untracked rogue files
        with open(os.path.join(self.test_dir, "rogue_script.sh"), "w", encoding="utf-8") as f:
            f.write("echo 'rogue'")

        with open(os.path.join(self.test_dir, "scripts", "untracked_helper.py"), "w", encoding="utf-8") as f:
            f.write("# untracked")

        # Modify data/negocios.json
        with open(os.path.join(self.test_dir, "data", "negocios.json"), "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "businesses": [{"id": "steamfur-pro", "followers": 10}]}, f)

        # Execute Centinela staging command
        self._run_git(["add", "data/negocios.json"])

        # Check staged files
        res_staged = self._run_git(["diff", "--staged", "--name-only"])
        staged_files = res_staged.stdout.strip().splitlines()

        self.assertEqual(len(staged_files), 1, f"Expected exactly 1 staged file, got: {staged_files}")
        self.assertEqual(staged_files[0].replace("\\", "/"), "data/negocios.json")

        # Check unstaged files
        res_unstaged = self._run_git(["status", "--porcelain"])
        status_lines = res_unstaged.stdout.strip().splitlines()
        # index.html should be modified unstaged (" M index.html")
        has_unstaged_index = any(" M index.html" in line for line in status_lines)
        self.assertTrue(has_unstaged_index, "index.html must remain unstaged")

    def test_zero_diff_quiet_clean_handling(self):
        """
        Empirical verification: git diff --staged --quiet returns 0 when no metrics changed,
        preventing empty commit failure.
        """
        # Run git add data/negocios.json with identical content
        self._run_git(["add", "data/negocios.json"])

        res = self._run_git(["diff", "--staged", "--quiet"], check=False)
        self.assertEqual(res.returncode, 0, "git diff --staged --quiet must return 0 when nothing changed")

    def test_zero_diff_quiet_returns_one_when_changed(self):
        """
        Empirical verification: git diff --staged --quiet returns 1 when real metrics changed,
        properly routing to git commit.
        """
        with open(os.path.join(self.test_dir, "data", "negocios.json"), "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "businesses": [{"id": "steamfur-pro", "followers": 42}]}, f)

        self._run_git(["add", "data/negocios.json"])

        res = self._run_git(["diff", "--staged", "--quiet"], check=False)
        self.assertEqual(res.returncode, 1, "git diff --staged --quiet must return 1 when changes exist")


class TestDataResilienceAndPathologicalEdgeCases(unittest.TestCase):
    """Stress testing HubEngine and BusinessStorage under pathological corruptions."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="data_adv_test_")
        self.data_file = os.path.join(self.test_dir, "negocios.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_malformed_truncated_json_handling(self):
        """Test handling of truncated, invalid JSON syntax in storage file."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write('{"version": "1.0.0", "businesses": [ {"id": "steamfur')

        storage = BusinessStorage(self.data_file)
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("Corrupted or invalid JSON", str(ctx.exception))

        # FINDING: cli_main currently catches only KeyError at line 1620, leaking unhandled ValueError
        with self.assertRaises(ValueError):
            cli_main(["refresh", "--all", "--data-path", self.data_file])

    def test_zero_byte_empty_file_handling(self):
        """Test handling of completely empty (0 bytes) storage file."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("")

        storage = BusinessStorage(self.data_file)
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("Empty JSON file", str(ctx.exception))

        # FINDING: cli_main currently catches only KeyError at line 1620, leaking unhandled ValueError
        with self.assertRaises(ValueError):
            cli_main(["refresh", "--all", "--data-path", self.data_file])


    def test_non_dict_root_element_handling(self):
        """Test handling when root JSON element is an array instead of envelope dict."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([{"id": "steamfur-pro"}], f)

        storage = BusinessStorage(self.data_file)
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("Root JSON element must be an object envelope", str(ctx.exception))

    def test_missing_businesses_key_handling(self):
        """Test handling when JSON envelope lacks 'businesses' array."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "updated_at": "2026-09-29T12:00:00Z"}, f)

        storage = BusinessStorage(self.data_file)
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("missing required 'businesses' array", str(ctx.exception))

    def test_missing_cluster_canales_handled_gracefully(self):
        """Test that refresh_metrics safely handles a business record missing cluster_canales."""
        bare_envelope = {
            "version": "1.0.0",
            "businesses": [
                {
                    "id": "steamfur-pro",
                    "nombre": "SteamFur Pro™",
                    "nicho": "Mascotas",
                    "status": "activo",
                    # No cluster_canales, no metricas_resumen, no historial
                }
            ]
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(bare_envelope, f)

        engine = HubEngine(data_path=self.data_file)
        refreshed = engine.refresh_metrics("steamfur-pro")

        self.assertIn("cluster_canales", refreshed)
        self.assertIn("youtube_shorts", refreshed["cluster_canales"])
        self.assertIn("instagram_reels", refreshed["cluster_canales"])
        self.assertIn("facebook_reels", refreshed["cluster_canales"])
        self.assertNotIn("tiktok", refreshed["cluster_canales"])

    def test_atomic_persistence_preserves_original_on_failure(self):
        """
        Verify that atomic write (tempfile + os.replace) leaves the original
        file completely intact if an exception is raised prior to commit.
        """
        valid_envelope = {
            "version": "1.0.0",
            "businesses": [{"id": "original-store", "nombre": "Original Store", "status": "activo"}]
        }
        storage = BusinessStorage(self.data_file)
        storage.save(valid_envelope)

        with open(self.data_file, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Attempt to save invalid data that fails validation
        with self.assertRaises(ValueError):
            storage.save({"invalid_key": 123})

        with open(self.data_file, "r", encoding="utf-8") as f:
            current_content = f.read()
        self.assertEqual(original_content, current_content, "Original file must not be modified when save fails")


class TestCentinelaScriptAndTikTokEradication(unittest.TestCase):
    """Verify scripts/centinela_refresh.py and TikTok eradication."""

    def test_centinela_refresh_script_exists_and_clean(self):
        """Verify scripts/centinela_refresh.py exists and defaults to refresh --all."""
        script_path = os.path.join(HUB_ROOT, "scripts", "centinela_refresh.py")
        self.assertTrue(os.path.exists(script_path), f"Script not found at {script_path}")
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("from hub_engine import cli_main", content)
        self.assertIn('["refresh", "--all"]', content)
        self.assertNotIn("tiktok", content.lower())

    def test_active_stores_dynamic_refresh_skips_preparation(self):
        """
        Verify that refresh_metrics(None) skips stores with status == 'en_preparacion'
        and preserves their score without degradation.
        """
        test_dir = tempfile.mkdtemp(prefix="refresh_prep_test_")
        data_file = os.path.join(test_dir, "negocios.json")
        try:
            envelope = {
                "version": "1.0.0",
                "businesses": [
                    {
                        "id": "steamfur-pro",
                        "nombre": "SteamFur Pro™",
                        "status": "activo",
                        "metricas_resumen": {"account_health_score": 95.0, "health_status": "optimo"},
                    },
                    {
                        "id": "prosmile-ultrasonic",
                        "nombre": "ProSmile Ultrasonic™",
                        "status": "en_preparacion",
                        "metricas_resumen": {"account_health_score": 75.0, "health_status": "en_espera"},
                    },
                ]
            }
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(envelope, f)

            engine = HubEngine(data_path=data_file)
            refreshed = engine.refresh_metrics(None)

            # Only active businesses should be returned in refreshed list
            self.assertEqual(len(refreshed), 1)
            self.assertEqual(refreshed[0]["id"], "steamfur-pro")

            # Check persistent storage
            stored_data = engine.storage.load()
            prosmile = next(b for b in stored_data["businesses"] if b["id"] == "prosmile-ultrasonic")
            self.assertEqual(prosmile["status"], "en_preparacion")
            self.assertEqual(prosmile["metricas_resumen"]["account_health_score"], 75.0)
            self.assertNotIn("refreshed_at", prosmile)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
