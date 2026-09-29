#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Test Suite for Multi-Account Hub Engine
============================================
Comprehensive test suite verifying 100% of data layer operations,
atomic persistence, mathematical health scoring, seed data parity,
and CLI interface commands.

Runner compatibility:
- Standard library: python -m unittest discover -s tests -p "test_*.py"
- Direct execution: python tests/test_hub.py
"""

from datetime import datetime, timedelta, timezone
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

# Ensure multi_account_hub is importable
HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HUB_ROOT not in sys.path:
    sys.path.insert(0, HUB_ROOT)

from hub_engine import (
    INITIAL_BUSINESSES,
    SCHEMA_VERSION,
    BusinessStorage,
    HealthScorer,
    HubEngine,
    cli_main,
    parse_iso_datetime,
)


class BaseHubTestCase(unittest.TestCase):
    """Base test case providing an isolated temporary directory for each test."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="hub_test_")
        self.data_file = os.path.join(self.test_dir, "negocios.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_business(self, b_id="test-product", name="Test Product™", niche="Test Niche", status="activo"):
        """Helper to create a well-formed test business dict."""
        return {
            "id": b_id,
            "nombre": name,
            "nicho": niche,
            "status": status,
            "score_hunter": 95.0,
            "enlace_tienda": f"https://{b_id}.com",
            "cluster_canales": {
                "youtube_shorts": {
                    "handle": f"@{b_id}_yt",
                    "canal_url": f"https://youtube.com/@{b_id}",
                    "estado": "activo",
                    "seguidores": 1000,
                    "reproducciones_totales": 50000,
                    "videos_publicados": 14,
                    "ultimo_post": "2026-09-23T15:00:00Z",
                },
                "instagram_reels": {
                    "handle": f"@{b_id}_ig",
                    "canal_url": f"https://instagram.com/{b_id}",
                    "estado": "activo",
                    "seguidores": 800,
                    "reproducciones_totales": 35000,
                    "videos_publicados": 14,
                    "ultimo_post": "2026-09-23T23:00:00Z",
                },
                "facebook_reels": {
                    "handle": f"{name} Official",
                    "canal_url": f"https://facebook.com/{b_id}",
                    "estado": "activo",
                    "seguidores": 500,
                    "reproducciones_totales": 15000,
                    "videos_publicados": 10,
                    "ultimo_post": "2026-09-23T23:00:00Z",
                },
            },
            "metricas_resumen": {
                "videos_hoy": 2,
                "vistas_hoy": 10000,
                "clics_tienda_hoy": 80,
                "vistas_ultimos_7_dias": 70000,
                "tasa_conversion_bio_pct": 1.15,
                "dias_sin_publicar": 0,
                "account_health_score": 95.0,
                "health_status": "optimo",
            },
            "historial_metricas": [
                {
                    "fecha": "2026-09-21",
                    "videos_publicados": 2,
                    "vistas": 9500,
                    "clics_checkout": 70,
                    "health_score": 93.0,
                },
                {
                    "fecha": "2026-09-22",
                    "videos_publicados": 2,
                    "vistas": 9800,
                    "clics_checkout": 75,
                    "health_score": 94.0,
                },
                {
                    "fecha": "2026-09-23",
                    "videos_publicados": 2,
                    "vistas": 10000,
                    "clics_checkout": 80,
                    "health_score": 95.0,
                },
            ],
        }


# ==============================================================================
# 1. Storage & Atomic Persistence Tests
# ==============================================================================
class TestHubStorage(BaseHubTestCase):
    """Verifies atomic file persistence, error handling, and file initialization."""

    def test_init_creates_missing_file(self):
        storage = BusinessStorage(self.data_file)
        self.assertTrue(os.path.exists(self.data_file))
        data = storage.load()
        self.assertEqual(data["version"], SCHEMA_VERSION)
        self.assertEqual(data["total_businesses"], 0)
        self.assertEqual(data["businesses"], [])

    def test_atomic_write_integrity(self):
        storage = BusinessStorage(self.data_file)
        payload = {
            "version": "1.0.0",
            "businesses": [{"id": "unit-test", "nombre": "Unit Test"}],
        }
        storage.save(payload)
        reloaded = storage.load()
        self.assertEqual(reloaded["total_businesses"], 1)
        self.assertEqual(reloaded["businesses"][0]["id"], "unit-test")

    def test_load_corrupted_json_raises_value_error(self):
        storage = BusinessStorage(self.data_file)
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON DATA CORRUPTED ]")
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("Corrupted or invalid JSON", str(ctx.exception))

    def test_load_invalid_root_type_raises_value_error(self):
        storage = BusinessStorage(self.data_file)
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("[\"array\", \"not\", \"object\"]")
        with self.assertRaises(ValueError) as ctx:
            storage.load()
        self.assertIn("Root JSON element must be an object", str(ctx.exception))

    def test_save_invalid_envelope_raises_value_error(self):
        storage = BusinessStorage(self.data_file)
        with self.assertRaises(ValueError):
            storage.save(["not a dict"])
        with self.assertRaises(ValueError):
            storage.save({"missing": "businesses"})

    def test_storage_reload(self):
        storage = BusinessStorage(self.data_file)
        data = storage.load()
        self.assertEqual(data["total_businesses"], 0)
        data["businesses"].append({"id": "sample-1", "nombre": "Sample"})
        storage.save(data)
        reloaded = storage.reload()
        self.assertEqual(reloaded["total_businesses"], 1)


# ==============================================================================
# 2. Business CRUD Lifecycle Tests
# ==============================================================================
class TestBusinessCRUD(BaseHubTestCase):
    """Verifies all CRUD operations, validations, and ID uniqueness."""

    def setUp(self):
        super().setUp()
        self.engine = HubEngine(data_path=self.data_file)

    def test_add_business_success(self):
        mock_b = self.create_mock_business(b_id="test-item", name="Item Test")
        res = self.engine.add_business(mock_b)
        self.assertEqual(res["id"], "test-item")
        self.assertEqual(res["nombre"], "Item Test")
        self.assertIn("account_health_score", res["metricas_resumen"])
        retrieved = self.engine.get_business("test-item")
        self.assertEqual(retrieved["id"], "test-item")

    def test_add_business_duplicate_id_raises_value_error(self):
        mock_b1 = self.create_mock_business(b_id="duplicate-id", name="Dup 1")
        self.engine.add_business(mock_b1)
        mock_b2 = self.create_mock_business(b_id="duplicate-id", name="Dup 2")
        with self.assertRaises(ValueError) as ctx:
            self.engine.add_business(mock_b2)
        self.assertIn("already exists", str(ctx.exception))

    def test_add_business_missing_required_fields(self):
        with self.assertRaises(ValueError):
            self.engine.add_business({"nombre": "No ID", "nicho": "Tech"})
        with self.assertRaises(ValueError):
            self.engine.add_business({"id": "no-name", "nicho": "Tech"})
        with self.assertRaises(ValueError):
            self.engine.add_business({"id": "no-niche", "nombre": "No Niche"})

    def test_add_business_initializes_default_channels(self):
        minimal_b = {
            "id": "minimal-product",
            "nombre": "Minimal Product",
            "nicho": "General",
        }
        res = self.engine.add_business(minimal_b)
        channels = res.get("cluster_canales", {})
        self.assertIn("youtube_shorts", channels)
        self.assertIn("instagram_reels", channels)
        self.assertIn("facebook_reels", channels)
        self.assertNotIn("tiktok", channels)
        self.assertEqual(len(channels), 3)

    def test_get_business_success(self):
        mock_b = self.create_mock_business(b_id="fetch-me")
        self.engine.add_business(mock_b)
        found = self.engine.get_business("fetch-me")
        self.assertEqual(found["id"], "fetch-me")

    def test_get_business_not_found_raises_key_error(self):
        with self.assertRaises(KeyError) as ctx:
            self.engine.get_business("ghost-business")
        self.assertIn("ghost-business", str(ctx.exception))

    def test_update_business_success(self):
        mock_b = self.create_mock_business(b_id="update-target")
        self.engine.add_business(mock_b)
        updated = self.engine.update_business("update-target", {"nombre": "New Name", "nicho": "New Niche"})
        self.assertEqual(updated["nombre"], "New Name")
        self.assertEqual(updated["nicho"], "New Niche")
        retrieved = self.engine.get_business("update-target")
        self.assertEqual(retrieved["nombre"], "New Name")

    def test_update_business_preserves_id_and_created_at(self):
        mock_b = self.create_mock_business(b_id="immutable-check")
        created = self.engine.add_business(mock_b)
        original_created_at = created["created_at"]
        updated = self.engine.update_business(
            "immutable-check",
            {"id": "hacked-id", "created_at": "1999-01-01T00:00:00Z", "nombre": "Updated"},
        )
        self.assertEqual(updated["id"], "immutable-check")
        self.assertEqual(updated["created_at"], original_created_at)

    def test_update_business_not_found_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.update_business("non-existent", {"nombre": "Fail"})

    def test_archive_business_soft_delete(self):
        mock_b = self.create_mock_business(b_id="to-archive")
        self.engine.add_business(mock_b)
        archived = self.engine.archive_business("to-archive")
        self.assertEqual(archived["status"], "archivado")
        self.assertIn("archived_at", archived)
        # All channels must be paused
        for ch in archived["cluster_canales"].values():
            self.assertEqual(ch["estado"], "pausado")

    def test_archive_business_not_found_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.archive_business("non-existent")

    def test_unarchive_business_restores_active(self):
        mock_b = self.create_mock_business(b_id="to-restore")
        self.engine.add_business(mock_b)
        self.engine.archive_business("to-restore")
        restored = self.engine.unarchive_business("to-restore")
        self.assertEqual(restored["status"], "activo")
        self.assertNotIn("archived_at", restored)
        self.assertEqual(restored["cluster_canales"]["youtube_shorts"]["estado"], "activo")

    def test_unarchive_business_not_found_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.unarchive_business("non-existent")


# ==============================================================================
# 3. Listing & Multi-Criteria Filtering Tests
# ==============================================================================
class TestListingAndFiltering(BaseHubTestCase):
    """Verifies listing and multi-criteria filters across niches, status, and scores."""

    def setUp(self):
        super().setUp()
        self.engine = HubEngine(data_path=self.data_file)
        self.b1 = self.create_mock_business(b_id="b-pets", name="Pet Item", niche="Mascotas & Hogar", status="activo")
        self.b2 = self.create_mock_business(b_id="b-dental", name="Dental Item", niche="Salud Dental", status="activo")
        self.b3 = self.create_mock_business(b_id="b-tactical", name="Jet Fan", niche="Automotriz & Táctico", status="calentamiento")
        self.b4 = self.create_mock_business(b_id="b-old", name="Old Item", niche="Hogar", status="archivado")

        self.engine.add_business(self.b1)
        self.engine.add_business(self.b2)
        self.engine.add_business(self.b3)
        self.engine.add_business(self.b4)

    def test_list_businesses_excludes_archived_by_default(self):
        listed = self.engine.list_businesses(include_archived=False)
        ids = [b["id"] for b in listed]
        self.assertIn("b-pets", ids)
        self.assertIn("b-dental", ids)
        self.assertIn("b-tactical", ids)
        self.assertNotIn("b-old", ids)
        self.assertEqual(len(listed), 3)

    def test_list_businesses_includes_archived_when_flagged(self):
        listed = self.engine.list_businesses(include_archived=True)
        self.assertEqual(len(listed), 4)

    def test_filter_by_niche_case_insensitive(self):
        res1 = self.engine.filter_businesses(niche="mascotas")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["id"], "b-pets")

        res2 = self.engine.filter_businesses(niche="DENTAL")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["id"], "b-dental")

    def test_filter_by_status(self):
        actives = self.engine.filter_businesses(status="activo")
        self.assertEqual(len(actives), 2)
        warming = self.engine.filter_businesses(status="calentamiento")
        self.assertEqual(len(warming), 1)
        self.assertEqual(warming[0]["id"], "b-tactical")
        archived = self.engine.filter_businesses(status="archivado")
        self.assertEqual(len(archived), 1)

    def test_filter_by_platform(self):
        yt_businesses = self.engine.filter_businesses(platform="youtube")
        self.assertGreaterEqual(len(yt_businesses), 2)

    def test_filter_by_min_health_score(self):
        # Update b-dental with dormant metrics and paused channels to lower its genuine score
        self.engine.update_business("b-dental", {
            "metricas_resumen": {"dias_sin_publicar": 8, "videos_hoy": 0, "vistas_hoy": 0},
            "cluster_canales": {
                "youtube_shorts": {"estado": "pausado"},
                "instagram_reels": {"estado": "pausado"},
                "facebook_reels": {"estado": "pausado"},
            },
            "historial_metricas": [],
        })
        high_scores = self.engine.filter_businesses(min_health_score=80.0)
        ids = [b["id"] for b in high_scores]
        self.assertIn("b-pets", ids)
        self.assertNotIn("b-dental", ids)

    def test_filter_combined_criteria(self):
        res = self.engine.filter_businesses(niche="Mascotas", status="activo", min_health_score=50.0)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "b-pets")

    def test_filter_no_results(self):
        res = self.engine.filter_businesses(niche="Astronomy")
        self.assertEqual(res, [])


# ==============================================================================
# 4. Metrics Logging & Counter Updates
# ==============================================================================
class TestMetricsLogging(BaseHubTestCase):
    """Verifies metrics recording, rolling counters, and channel tracking."""

    def setUp(self):
        super().setUp()
        self.engine = HubEngine(data_path=self.data_file)
        self.mock_b = self.create_mock_business(b_id="metrics-biz")
        self.engine.add_business(self.mock_b)

    def test_log_metrics_appends_history(self):
        entry = {
            "fecha": "2026-09-24",
            "videos_publicados": 2,
            "vistas": 12000,
            "clics_checkout": 90,
            "pedidos": 8,
        }
        res = self.engine.log_metrics("metrics-biz", entry)
        history = res["historial_metricas"]
        self.assertEqual(history[-1]["vistas"], 12000)
        self.assertIn("health_score", history[-1])

    def test_log_metrics_updates_summary_counters(self):
        entry = {
            "fecha": "2026-09-24",
            "videos_publicados": 3,
            "vistas": 15000,
            "clics_checkout": 120,
        }
        res = self.engine.log_metrics("metrics-biz", entry)
        summary = res["metricas_resumen"]
        self.assertEqual(summary["videos_hoy"], 3)
        self.assertEqual(summary["vistas_hoy"], 15000)
        self.assertEqual(summary["clics_tienda_hoy"], 120)
        self.assertEqual(summary["dias_sin_publicar"], 0)
        self.assertAlmostEqual(summary["tasa_conversion_bio_pct"], 0.8, places=2)

    def test_log_metrics_channel_specific_tracking(self):
        initial_ch = self.engine.get_business("metrics-biz")["cluster_canales"]["youtube_shorts"]
        init_views = initial_ch["reproducciones_totales"]
        init_posts = initial_ch["videos_publicados"]

        entry = {
            "fecha": "2026-09-24",
            "videos_publicados": 1,
            "vistas": 5000,
            "clics_checkout": 40,
        }
        res = self.engine.log_metrics("metrics-biz", entry, channel="youtube_shorts")
        updated_ch = res["cluster_canales"]["youtube_shorts"]
        self.assertEqual(updated_ch["reproducciones_totales"], init_views + 5000)
        self.assertEqual(updated_ch["videos_publicados"], init_posts + 1)
        self.assertIsNotNone(updated_ch["ultimo_post"])

    def test_log_metrics_triggers_health_recalculation(self):
        entry = {
            "fecha": "2026-09-24",
            "videos_publicados": 2,
            "vistas": 18000,
            "clics_checkout": 150,
        }
        res = self.engine.log_metrics("metrics-biz", entry)
        score = res["metricas_resumen"]["account_health_score"]
        self.assertGreaterEqual(score, 80.0)

    def test_log_metrics_invalid_business_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.log_metrics("non-existent-biz", {"vistas": 100})

    def test_log_metrics_invalid_payload_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.engine.log_metrics("metrics-biz", "not a dict")

    def test_log_metrics_zero_views_resets_conversion(self):
        entry = {"fecha": "2026-09-24", "videos_publicados": 0, "vistas": 0, "clics_checkout": 0}
        res = self.engine.log_metrics("metrics-biz", entry)
        summary = res["metricas_resumen"]
        self.assertEqual(summary["vistas_hoy"], 0)


# ==============================================================================
# 5. Account Health Score Algorithm Mathematical Rigor
# ==============================================================================
class TestHealthScoreAlgorithm(BaseHubTestCase):
    """Verifies Account Health Score mathematical formula, bounds, and edge cases."""

    def test_health_score_perfect_active_account(self):
        b_data = self.create_mock_business()
        score_res = HealthScorer.calculate_score(b_data)
        self.assertGreaterEqual(score_res["total_score"], 90.0)
        self.assertEqual(score_res["health_status"], "optimo")
        bd = score_res["breakdown"]
        self.assertGreaterEqual(bd["consistency_score"], 25.0)
        self.assertGreaterEqual(bd["momentum_score"], 20.0)
        self.assertGreaterEqual(bd["recency_score"], 22.0)
        self.assertEqual(bd["penalties_deducted"], 0.0)

    def test_health_score_warming_account_no_penalty(self):
        # A warming account with 0 posts must get full consistency and recency marks
        b_data = {
            "id": "warm-biz",
            "status": "calentamiento",
            "cluster_canales": {
                "youtube_shorts": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
                "instagram_reels": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
            },
            "metricas_resumen": {
                "videos_hoy": 0,
                "vistas_hoy": 50,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 0,
            },
            "historial_metricas": [],
        }
        score_res = HealthScorer.calculate_score(b_data)
        self.assertGreaterEqual(score_res["total_score"], 85.0)
        bd = score_res["breakdown"]
        self.assertEqual(bd["consistency_score"], 35.0)
        self.assertEqual(bd["recency_score"], 25.0)
        self.assertEqual(bd["penalties_deducted"], 0.0)

    def test_health_score_decay_with_inactivity(self):
        b_data = self.create_mock_business()
        scores = []
        for days in [0, 1, 2, 3, 4, 6]:
            b_data["metricas_resumen"]["dias_sin_publicar"] = days
            score = HealthScorer.calculate_score(b_data)["total_score"]
            scores.append(score)

        # Monotonically non-increasing
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])

        # At 6 days of inactivity, dormancy penalty kicks in
        b_data["metricas_resumen"]["dias_sin_publicar"] = 6
        dormant_res = HealthScorer.calculate_score(b_data)
        self.assertGreater(dormant_res["breakdown"]["penalties_deducted"], 0.0)

    def test_health_score_shadowban_penalty_applied(self):
        # Active account published today but got only 15 views
        b_data = self.create_mock_business()
        b_data["metricas_resumen"]["videos_hoy"] = 2
        b_data["metricas_resumen"]["vistas_hoy"] = 15
        b_data["metricas_resumen"]["dias_sin_publicar"] = 0
        score_res = HealthScorer.calculate_score(b_data)
        self.assertIn("RIESGO_SHADOWBAN", score_res["breakdown"]["flags"])
        self.assertGreaterEqual(score_res["breakdown"]["penalties_deducted"], 20.0)

    def test_health_score_triad_channel_pause_penalty(self):
        b_data = self.create_mock_business()
        # Pause 1 triad channel
        b_data["cluster_canales"]["youtube_shorts"]["estado"] = "pausado"
        score_res = HealthScorer.calculate_score(b_data)
        self.assertGreaterEqual(score_res["breakdown"]["penalties_deducted"], 8.0)

    def test_health_score_zero_division_safety(self):
        # Absolutely empty / zeroed business
        empty_b = {
            "id": "zero-biz",
            "status": "activo",
            "cluster_canales": {},
            "metricas_resumen": {
                "videos_hoy": 0,
                "vistas_hoy": 0,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 10,
            },
            "historial_metricas": [],
        }
        score_res = HealthScorer.calculate_score(empty_b)
        self.assertGreaterEqual(score_res["total_score"], 0.0)
        self.assertLessEqual(score_res["total_score"], 100.0)
        self.assertEqual(score_res["health_status"], "critico")

    def test_health_score_deterministic_date_injection(self):
        b_data = self.create_mock_business()
        fixed_date = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
        score1 = HealthScorer.calculate_score(b_data, as_of_date=fixed_date)
        score2 = HealthScorer.calculate_score(b_data, as_of_date=fixed_date)
        self.assertEqual(score1["total_score"], score2["total_score"])

    def test_health_score_momentum_growth_bonus(self):
        # 3-day view velocity >= +20%
        b_data = self.create_mock_business()
        b_data["historial_metricas"] = [
            {"vistas": 1000, "videos_publicados": 2},
            {"vistas": 1000, "videos_publicados": 2},
            {"vistas": 1000, "videos_publicados": 2},
            {"vistas": 2000, "videos_publicados": 2},
            {"vistas": 2500, "videos_publicados": 2},
            {"vistas": 3000, "videos_publicados": 2},
        ]
        score_res = HealthScorer.calculate_score(b_data)
        self.assertEqual(score_res["breakdown"]["momentum_score"], 30.0)

    def test_health_score_momentum_decline_penalty(self):
        # Severe drop in views
        b_data = self.create_mock_business()
        b_data["historial_metricas"] = [
            {"vistas": 5000, "videos_publicados": 2},
            {"vistas": 5000, "videos_publicados": 2},
            {"vistas": 5000, "videos_publicados": 2},
            {"vistas": 500, "videos_publicados": 2},
            {"vistas": 400, "videos_publicados": 2},
            {"vistas": 300, "videos_publicados": 2},
        ]
        score_res = HealthScorer.calculate_score(b_data)
        self.assertLess(score_res["breakdown"]["momentum_score"], 15.0)

    def test_health_score_conversion_tiers(self):
        b_data = self.create_mock_business()
        b_data["metricas_resumen"]["vistas_hoy"] = 1000
        # CTR 1.0% -> 10 pts
        b_data["metricas_resumen"]["tasa_conversion_bio_pct"] = 1.0
        score_res = HealthScorer.calculate_score(b_data)
        self.assertEqual(score_res["breakdown"]["conversion_score"], 10.0)

        # CTR 0.5% -> 7.5 pts
        b_data["metricas_resumen"]["tasa_conversion_bio_pct"] = 0.5
        score_res = HealthScorer.calculate_score(b_data)
        self.assertEqual(score_res["breakdown"]["conversion_score"], 7.5)


# ==============================================================================
# 6. Seed Data & Upstream Parity Tests
# ==============================================================================
class TestSeedDataParity(BaseHubTestCase):
    """Verifies parity with Dropshipping Hunter winners and initial businesses."""

    def setUp(self):
        super().setUp()
        self.engine = HubEngine(data_path=self.data_file)

    def test_seed_contains_exact_4_winners(self):
        seeded = self.engine.seed_initial_businesses(overwrite=True)
        self.assertEqual(len(seeded), 4)
        ids = [b["id"] for b in seeded]
        self.assertIn("steamfur-pro", ids)
        self.assertIn("prosmile-ultrasonic", ids)
        self.assertIn("spinerelief-pro", ids)
        self.assertIn("aeroforce-x3", ids)

    def test_seed_matches_dropshipping_hunter_scores(self):
        seeded = self.engine.seed_initial_businesses(overwrite=True)
        scores_by_id = {b["id"]: b["score_hunter"] for b in seeded}
        self.assertEqual(scores_by_id["steamfur-pro"], 100.0)
        self.assertEqual(scores_by_id["prosmile-ultrasonic"], 100.0)
        self.assertEqual(scores_by_id["spinerelief-pro"], 97.0)
        self.assertEqual(scores_by_id["aeroforce-x3"], 97.0)

    def test_seed_includes_conversion_hooks(self):
        seeded = self.engine.seed_initial_businesses(overwrite=True)
        for b in seeded:
            hooks = b.get("ganchos_conversion", {})
            self.assertIn("gancho_1_curiosidad", hooks)
            self.assertIn("gancho_2_agitacion", hooks)
            self.assertIn("gancho_3_contrariano", hooks)
            self.assertIn("gancho_4_transformacion", hooks)
            for h in hooks.values():
                self.assertTrue(len(h.get("voz_cliente", "")) > 10)
                self.assertTrue(len(h.get("voz_creador", "")) > 10)
                self.assertIn("texto_3d", h)

    def test_seed_idempotency_without_overwrite(self):
        self.engine.seed_initial_businesses(overwrite=True)
        # Modify a business
        self.engine.update_business("steamfur-pro", {"nombre": "Modified SteamFur"})
        # Re-seed without overwrite should not destroy changes
        seeded = self.engine.seed_initial_businesses(overwrite=False)
        self.assertEqual(seeded[0]["nombre"], "Modified SteamFur")

    def test_seed_forces_reset_with_overwrite(self):
        self.engine.seed_initial_businesses(overwrite=True)
        self.engine.update_business("steamfur-pro", {"nombre": "Modified SteamFur"})
        # Re-seed with overwrite should reset
        seeded = self.engine.seed_initial_businesses(overwrite=True)
        self.assertEqual(seeded[0]["nombre"], "SteamFur Pro™")


# ==============================================================================
# 7. Command Line Interface (CLI) Execution Tests
# ==============================================================================
class TestCommandLineInterface(BaseHubTestCase):
    """Verifies CLI argument parsing and terminal commands execution."""

    def setUp(self):
        super().setUp()
        self.engine = HubEngine(data_path=self.data_file)
        self.engine.seed_initial_businesses(overwrite=True)

    def run_cli(self, args):
        """Runs cli_main with injected arguments and captured stdout/stderr."""
        full_args = ["--data-path", self.data_file] + args
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
            code = cli_main(full_args)
        return code, stdout_buf.getvalue(), stderr_buf.getvalue()

    def test_cli_list_command(self):
        code, out, err = self.run_cli(["--list"])
        self.assertEqual(code, 0)
        self.assertIn("SteamFur Pro", out)
        self.assertIn("ProSmile Ultrasonic", out)
        self.assertIn("SpineRelief Pro", out)
        self.assertIn("AeroForce X3", out)

    def test_cli_health_command(self):
        code, out, err = self.run_cli(["--health", "steamfur-pro"])
        self.assertEqual(code, 0)
        self.assertIn("ACCOUNT HEALTH SCORE BREAKDOWN", out)
        self.assertIn("steamfur-pro", out)
        self.assertIn("Consistency", out)
        self.assertIn("Momentum", out)

    def test_cli_health_command_non_existent(self):
        code, out, err = self.run_cli(["--health", "phantom-id"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_cli_info_command(self):
        code, out, err = self.run_cli(["--info", "prosmile-ultrasonic"])
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], "prosmile-ultrasonic")
        self.assertEqual(parsed["score_hunter"], 100.0)

    def test_cli_seed_command(self):
        code, out, err = self.run_cli(["--seed"])
        self.assertEqual(code, 0)
        self.assertIn("Seeded 4 initial winning businesses", out)

    def test_cli_archive_and_unarchive_command(self):
        # Archive
        code, out, err = self.run_cli(["--archive", "aeroforce-x3"])
        self.assertEqual(code, 0)
        self.assertIn("archived successfully", out)

        # Confirm list excludes it
        code, out, err = self.run_cli(["--list"])
        self.assertNotIn("aeroforce-x3", out)

        # Unarchive
        code, out, err = self.run_cli(["--unarchive", "aeroforce-x3"])
        self.assertEqual(code, 0)
        self.assertIn("restored to active status", out)

    def test_cli_log_metric_command(self):
        code, out, err = self.run_cli([
            "--log-metric", "steamfur-pro",
            "--views", "20000",
            "--clicks", "150",
            "--posts", "2",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Logged metrics for 'steamfur-pro'", out)

    def test_cli_filter_command(self):
        code, out, err = self.run_cli(["--filter", "--niche", "Mascotas"])
        self.assertEqual(code, 0)
        self.assertIn("SteamFur Pro", out)
        self.assertNotIn("ProSmile Ultrasonic", out)

    def test_cli_add_command(self):
        new_payload = {
            "id": "new-cli-product",
            "nombre": "CLI Product",
            "nicho": "Testing Niche",
        }
        json_file = os.path.join(self.test_dir, "new_prod.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(new_payload, f)

        code, out, err = self.run_cli(["--add", json_file])
        self.assertEqual(code, 0)
        self.assertIn("Added business 'new-cli-product'", out)

    def test_cli_invalid_args_handling(self):
        # Empty args defaults to list
        code, out, err = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertIn("MULTI-ACCOUNT HUB", out)


# ==============================================================================
# 8. Date Parsing Utility Tests
# ==============================================================================
class TestDateParsing(unittest.TestCase):
    """Verifies parse_iso_datetime robustness across formats."""

    def test_parse_iso_with_z(self):
        dt = parse_iso_datetime("2026-09-24T12:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 9)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_parse_iso_with_offset(self):
        dt = parse_iso_datetime("2026-09-24T12:00:00+00:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.hour, 12)

    def test_parse_simple_date(self):
        dt = parse_iso_datetime("2026-09-24")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.day, 24)

    def test_parse_invalid_string(self):
        self.assertIsNone(parse_iso_datetime("not-a-date"))
        self.assertIsNone(parse_iso_datetime(None))
        self.assertIsNone(parse_iso_datetime(""))


# ==============================================================================
# 9. Concurrency, Storage Resilience & HealthScorer Remediation Tests
# ==============================================================================
class TestRemediationRegression(BaseHubTestCase):
    """
    Regression tests verifying the remediation of:
    - Concurrency race conditions in HubEngine read-modify-write mutations
    - Windows NTFS file contention exponential backoff retry in BusinessStorage.save
    - Shadowban anomaly detection on 0 views with active posts
    - Complete None-safety across all HealthScorer attributes
    - HealthScorer.calculate public API alias contract
    """

    def test_concurrent_add_business_zero_lost_updates(self):
        """Spawns 20 concurrent threads adding businesses to ensure 0 lost updates."""
        engine = HubEngine(self.data_file)
        errors = []
        num_threads = 20

        def worker(thread_idx):
            b_data = {
                "id": f"concur-prod-{thread_idx}",
                "nombre": f"Concurrent Product {thread_idx}",
                "nicho": "Concur Niche",
            }
            try:
                engine.add_business(b_data)
            except Exception as e:
                errors.append((thread_idx, e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent add_business produced errors: {errors}")
        all_b = engine.list_businesses(include_archived=True)
        persisted_ids = {b["id"] for b in all_b}
        for i in range(num_threads):
            expected_id = f"concur-prod-{i}"
            self.assertIn(expected_id, persisted_ids, f"Lost update: {expected_id} not persisted")
        self.assertEqual(len(all_b), num_threads)

    def test_concurrent_log_metrics_zero_lost_updates(self):
        """Spawns 10 threads concurrently logging 20 metric entries each (total 200) with zero loss."""
        engine = HubEngine(self.data_file)
        biz = engine.add_business({
            "id": "concur-metric-target",
            "nombre": "Metrics Target",
            "nicho": "Niche",
        })

        num_threads = 10
        entries_per_thread = 20
        errors = []

        def worker(thread_idx):
            for j in range(entries_per_thread):
                entry = {
                    "fecha": f"2026-09-{(j % 28) + 1:02d}",
                    "vistas": 100 + thread_idx * 10 + j,
                    "videos_publicados": 1,
                    "clics_checkout": 5,
                    "pedidos": 1,
                }
                try:
                    engine.log_metrics("concur-metric-target", entry)
                except Exception as e:
                    errors.append((thread_idx, j, e))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent log_metrics produced errors: {errors}")
        updated_biz = engine.get_business("concur-metric-target")
        total_logged = len(updated_biz.get("historial_metricas", []))
        expected_total = num_threads * entries_per_thread
        self.assertEqual(
            total_logged,
            expected_total,
            f"Lost metric logs under concurrency! Expected {expected_total}, got {total_logged}"
        )

    @patch("time.sleep", return_value=None)
    def test_save_retry_on_windows_file_contention_succeeds(self, mock_sleep):
        """Verifies that BusinessStorage.save retries on PermissionError and succeeds."""
        storage = BusinessStorage(self.data_file)
        envelope = storage.load()
        envelope["test_marker"] = "retry_success"

        original_replace = os.replace
        calls = {"count": 0}

        def mock_replace(src, dst):
            calls["count"] += 1
            if calls["count"] < 3:
                raise PermissionError(13, "Access is denied (WinError 5)")
            return original_replace(src, dst)

        with patch("os.replace", side_effect=mock_replace):
            storage.save(envelope)

        self.assertEqual(calls["count"], 3)
        self.assertEqual(mock_sleep.call_count, 2)
        reloaded = storage.load()
        self.assertEqual(reloaded.get("test_marker"), "retry_success")

    @patch("time.sleep", return_value=None)
    def test_save_retry_exhausted_raises_ioerror(self, mock_sleep):
        """Verifies that exhausting all 10 retry attempts raises IOError."""
        storage = BusinessStorage(self.data_file)
        envelope = storage.load()

        with patch("os.replace", side_effect=PermissionError(13, "WinError 5")):
            with self.assertRaises(IOError) as ctx:
                storage.save(envelope)
            self.assertIn("Atomic persistence failure", str(ctx.exception))
            self.assertEqual(mock_sleep.call_count, 9)

    def test_shadowban_penalty_on_zero_views_with_posts(self):
        """Verifies that 0 views after publishing videos triggers RIESGO_SHADOWBAN and 20 pt penalty."""
        b_zero = {
            "status": "activo",
            "metricas_resumen": {
                "videos_hoy": 2,
                "vistas_hoy": 0,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 0,
            },
        }
        b_fifteen = {
            "status": "activo",
            "metricas_resumen": {
                "videos_hoy": 2,
                "vistas_hoy": 15,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 0,
            },
        }

        res_zero = HealthScorer.calculate_score(b_zero)
        res_fifteen = HealthScorer.calculate_score(b_fifteen)

        self.assertIn("RIESGO_SHADOWBAN", res_zero["breakdown"]["flags"])
        self.assertGreaterEqual(res_zero["breakdown"]["penalties_deducted"], 20.0)
        self.assertIn("RIESGO_SHADOWBAN", res_fifteen["breakdown"]["flags"])
        self.assertGreaterEqual(res_fifteen["breakdown"]["penalties_deducted"], 20.0)

        # Monotonicity: 0 views must NOT score higher than 15 views
        self.assertLessEqual(res_zero["total_score"], res_fifteen["total_score"])

    def test_health_scorer_none_safety(self):
        """Verifies HealthScorer handles None values gracefully across all fields without crashing."""
        pathological_cases = [
            # All top-level fields None
            {
                "status": None,
                "cluster_canales": None,
                "metricas_resumen": None,
                "historial_metricas": None,
            },
            # Non-dict / None root
            None,
            {},
            # Inner None fields
            {
                "status": "activo",
                "cluster_canales": {"youtube_shorts": None, "instagram_reels": {}},
                "metricas_resumen": {
                    "videos_hoy": None,
                    "vistas_hoy": None,
                    "clics_tienda_hoy": None,
                    "dias_sin_publicar": None,
                    "tasa_conversion_bio_pct": None,
                },
                "historial_metricas": [None, {}, {"vistas": None, "videos_publicados": None}],
            },
        ]

        for idx, case in enumerate(pathological_cases):
            res = HealthScorer.calculate_score(case)
            self.assertIsInstance(res, dict, f"Case {idx} did not return dict")
            self.assertIn("total_score", res, f"Case {idx} missing total_score")
            self.assertGreaterEqual(res["total_score"], 0.0)
            self.assertLessEqual(res["total_score"], 100.0)
            self.assertIn(res["health_status"], ["optimo", "estable", "alerta", "critico"])

    def test_health_scorer_calculate_alias(self):
        """Verifies that HealthScorer.calculate is exposed and behaves identically to calculate_score."""
        self.assertTrue(hasattr(HealthScorer, "calculate"))
        b = self.create_mock_business()
        score_direct = HealthScorer.calculate_score(b)
        score_alias = HealthScorer.calculate(b)
        self.assertEqual(score_direct, score_alias)

        # Also via engine instance
        engine = HubEngine(self.data_file)
        self.assertTrue(hasattr(engine.scorer, "calculate"))
        self.assertEqual(engine.scorer.calculate(b), score_direct)

    def test_storage_lock_and_transaction(self):
        """Verifies storage.lock property and transaction context manager."""
        storage = BusinessStorage(self.data_file)
        self.assertTrue(hasattr(storage, "lock"))
        self.assertIsInstance(storage.lock, type(threading.RLock()))

        # Test transaction context manager
        with storage.transaction() as data:
            data["transaction_test"] = True

        reloaded = storage.load()
        self.assertTrue(reloaded.get("transaction_test"))


if __name__ == "__main__":
    unittest.main()
