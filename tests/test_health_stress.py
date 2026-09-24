#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Stress Test Suite for Account Health Score Algorithm (HealthScorer)
Target: multi_account_hub/hub_engine.py -> HealthScorer
Created by: Challenger M1-2
"""

from datetime import datetime, timezone
import math
import random
import unittest
import sys
import os

HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HUB_ROOT not in sys.path:
    sys.path.insert(0, HUB_ROOT)

from hub_engine import HealthScorer


class TestHealthScorerStress(unittest.TestCase):
    """Stress tests with 1,000+ synthetic account configurations and boundary testing."""

    # =========================================================================
    # 1. API Contract Tests
    # =========================================================================
    def test_api_contract_calculate_alias(self):
        """Checks if HealthScorer provides .calculate() alias in addition to .calculate_score()."""
        has_calculate = hasattr(HealthScorer, "calculate")
        if not has_calculate:
            print("\n[FINDING: API Contract] HealthScorer has no 'calculate' method, only 'calculate_score'.")
        # Verify calculate_score is present
        self.assertTrue(hasattr(HealthScorer, "calculate_score"))

    # =========================================================================
    # 2. Extreme Boundary & Pathological Values
    # =========================================================================
    def test_extreme_all_zeros(self):
        """0 views, 0 posts, 0 clicks, 0 followers."""
        b = {
            "status": "activo",
            "cluster_canales": {},
            "metricas_resumen": {
                "videos_hoy": 0,
                "vistas_hoy": 0,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 0,
            },
            "historial_metricas": [],
        }
        res = HealthScorer.calculate_score(b)
        self.assertGreaterEqual(res["total_score"], 0.0)
        self.assertLessEqual(res["total_score"], 100.0)
        self.assertFalse(math.isnan(res["total_score"]))

    def test_extreme_enormous_billions(self):
        """Billions of views, millions of posts, large clicks."""
        b = {
            "status": "activo",
            "cluster_canales": {},
            "metricas_resumen": {
                "videos_hoy": 10**6,
                "vistas_hoy": 10**12,
                "clics_tienda_hoy": 10**10,  # 1.0% CTR >= 0.8% target
                "dias_sin_publicar": 0,
            },
            "historial_metricas": [
                {"vistas": 10**11, "videos_publicados": 10**5} for _ in range(7)
            ],
        }
        res = HealthScorer.calculate_score(b)
        self.assertGreaterEqual(res["total_score"], 0.0)
        self.assertLessEqual(res["total_score"], 100.0)
        # Consistency is maxed (35.0), recency maxed (25.0), conversion maxed (10.0)
        self.assertEqual(res["breakdown"]["consistency_score"], 35.0)
        self.assertEqual(res["breakdown"]["recency_score"], 25.0)
        self.assertEqual(res["breakdown"]["conversion_score"], 10.0)

    def test_extreme_negative_values_bypassed(self):
        """Negative metrics should not crash and must clamp properly."""
        b = {
            "status": "activo",
            "cluster_canales": {},
            "metricas_resumen": {
                "videos_hoy": -10,
                "vistas_hoy": -5000,
                "clics_tienda_hoy": -100,
                "dias_sin_publicar": -5,
            },
            "historial_metricas": [
                {"vistas": -100, "videos_publicados": -2} for _ in range(5)
            ],
        }
        res = HealthScorer.calculate_score(b)
        self.assertGreaterEqual(res["total_score"], 0.0)
        self.assertLessEqual(res["total_score"], 100.0)
        self.assertFalse(math.isnan(res["total_score"]))

    def test_pathological_none_values(self):
        """Ensure None values in sub-dictionaries do not trigger uncaught TypeError/AttributeError."""
        # Check None values handling
        none_keys = ["status", "cluster_canales", "metricas_resumen", "historial_metricas"]
        for key in none_keys:
            try:
                res = HealthScorer.calculate_score({key: None})
                print(f"[PATHOLOGICAL NONE] {key}=None handled safely -> score: {res['total_score']}")
            except Exception as e:
                print(f"[PATHOLOGICAL NONE FLAW] {key}=None raised uncaught {type(e).__name__}: {e}")

    # =========================================================================
    # 3. Zero-Division Hazards Across All Components
    # =========================================================================
    def test_zero_division_hazards(self):
        """Test zero-division protection across consistency, momentum, recency, conversion."""
        cases = [
            {"metricas_resumen": {"vistas_hoy": 0, "clics_tienda_hoy": 0}},
            {"metricas_resumen": {"vistas_hoy": 0, "clics_tienda_hoy": 50}},
            {"historial_metricas": [{"vistas": 0, "videos_publicados": 0} for _ in range(3)]},
            {"historial_metricas": [{"vistas": 0, "videos_publicados": 0} for _ in range(7)]},
            {"historial_metricas": [{"vistas": 0} for _ in range(7)] + [{"vistas": 100}, {"vistas": 200}, {"vistas": 300}]},
            {"historial_metricas": [{"vistas": 0}, {"vistas": 50}, {"vistas": 100}]},
            {"historial_metricas": [{"vistas": 0}, {"vistas": 0}, {"vistas": 0}]},
        ]
        for idx, tc in enumerate(cases):
            with self.subTest(case_idx=idx):
                res = HealthScorer.calculate_score(tc)
                score = res["total_score"]
                self.assertFalse(math.isnan(score), f"Score is NaN for case {idx}")
                self.assertFalse(math.isinf(score), f"Score is Inf for case {idx}")
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 100.0)

    # =========================================================================
    # 4. Calentamiento (Warm-up) Grace Score & Dormancy Invariants
    # =========================================================================
    def test_calentamiento_grace_score_and_no_dormancy_penalty(self):
        """
        Calentamiento accounts with 0 posts MUST receive:
        1. Exactly 35.0 consistency grace score.
        2. No dormancy penalty regardless of elapsed days (0, 1, 2, 3, 4, 10, 365).
        """
        days_list = [0, 1, 2, 3, 4, 10, 30, 365]
        for d in days_list:
            with self.subTest(days_inactive=d):
                b = {
                    "id": f"warm-test-{d}",
                    "status": "calentamiento",
                    "cluster_canales": {
                        "youtube_shorts": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
                        "instagram_reels": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
                        "facebook_reels": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
                        "tiktok": {"estado": "calentamiento", "videos_publicados": 0, "ultimo_post": None},
                    },
                    "metricas_resumen": {
                        "videos_hoy": 0,
                        "vistas_hoy": 0,
                        "clics_tienda_hoy": 0,
                        "dias_sin_publicar": d,
                    },
                    "historial_metricas": [],
                }
                res = HealthScorer.calculate_score(b)
                bd = res["breakdown"]

                # Invariant 1: Consistency score must be 35.0
                self.assertEqual(
                    bd["consistency_score"],
                    35.0,
                    f"Calentamiento account at d={d} did not receive 35.0 consistency score (got {bd['consistency_score']})",
                )

                # Invariant 2: No dormancy penalty applied
                dormancy_reasons = [r for r in bd["penalty_reasons"] if "Inactividad prolongada" in r]
                self.assertEqual(
                    len(dormancy_reasons),
                    0,
                    f"Calentamiento account at d={d} incorrectly received dormancy penalty: {dormancy_reasons}",
                )

                # Clamped total score
                self.assertGreaterEqual(res["total_score"], 0.0)
                self.assertLessEqual(res["total_score"], 100.0)

    # =========================================================================
    # 5. Dormant Accounts Invariant & Decay
    # =========================================================================
    def test_dormant_accounts_decay_and_penalties(self):
        """
        Dormant accounts (days_since_last_video = 1, 2, 3, 4, 10, 365 days):
        - Recency decay: 0->25, 1->22, 2->16, 3->10, 4->4, >=5->0
        - Dormancy penalty: <=3->0, 4->5, 5->10, 6->15, >=7->20
        - Monotonicity: score must be non-increasing with days inactive.
        """
        base_b = {
            "status": "activo",
            "cluster_canales": {
                "youtube_shorts": {"estado": "activo", "videos_publicados": 14},
                "instagram_reels": {"estado": "activo", "videos_publicados": 14},
                "facebook_reels": {"estado": "activo", "videos_publicados": 14},
            },
            "metricas_resumen": {
                "videos_hoy": 0,
                "vistas_hoy": 5000,
                "clics_tienda_hoy": 50,
                "tasa_conversion_bio_pct": 1.0,
            },
            "historial_metricas": [{"vistas": 5000, "videos_publicados": 2} for _ in range(7)],
        }

        test_days = [0, 1, 2, 3, 4, 5, 6, 7, 10, 365]
        expected_recency = {0: 25.0, 1: 22.0, 2: 16.0, 3: 10.0, 4: 4.0, 5: 0.0, 6: 0.0, 7: 0.0, 10: 0.0, 365: 0.0}
        expected_dormancy_pen = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 5.0, 5: 10.0, 6: 15.0, 7: 20.0, 10: 20.0, 365: 20.0}

        prev_score = 100.0
        for d in test_days:
            with self.subTest(days_inactive=d):
                b = dict(base_b)
                b["metricas_resumen"] = dict(base_b["metricas_resumen"])
                b["metricas_resumen"]["dias_sin_publicar"] = d

                res = HealthScorer.calculate_score(b)
                score = res["total_score"]
                bd = res["breakdown"]

                # 1. Monotonic non-increasing
                self.assertLessEqual(score, prev_score + 1e-9, f"Score increased at day {d}: {score} > {prev_score}")
                prev_score = score

                # 2. Recency score curve
                self.assertEqual(bd["recency_score"], expected_recency[d], f"Recency mismatch at day {d}")

                # 3. Dormancy penalty
                dormancy_reasons = [r for r in bd["penalty_reasons"] if "Inactividad prolongada" in r]
                exp_pen = expected_dormancy_pen[d]
                if exp_pen == 0.0:
                    self.assertEqual(len(dormancy_reasons), 0, f"Unexpected dormancy penalty at day {d}")
                else:
                    self.assertTrue(
                        any(f"-{exp_pen:.1f} pts" in r for r in dormancy_reasons),
                        f"Expected -{exp_pen:.1f} pts dormancy penalty at day {d}, got {dormancy_reasons}",
                    )

    # =========================================================================
    # 6. Shadowban Anomaly Detection (Crucial Challenge)
    # =========================================================================
    def test_shadowban_near_zero_views_triggers(self):
        """Near-zero views (<50) with active posts today must trigger RIESGO_SHADOWBAN."""
        b = {
            "status": "activo",
            "metricas_resumen": {
                "videos_hoy": 2,
                "vistas_hoy": 15,
                "clics_tienda_hoy": 0,
                "dias_sin_publicar": 0,
            },
        }
        res = HealthScorer.calculate_score(b)
        self.assertIn("RIESGO_SHADOWBAN", res["breakdown"]["flags"])
        self.assertGreaterEqual(res["breakdown"]["penalties_deducted"], 20.0)

    def test_shadowban_zero_views_with_posts_anomaly(self):
        """
        EMPIRICAL CHALLENGE:
        Accounts with posts but ZERO views (views_today = 0, videos_hoy = 2).
        Does line 952 'if views_today > 0 and views_today < 50:' bypass zero views?
        """
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

        has_flag_zero = "RIESGO_SHADOWBAN" in res_zero["breakdown"]["flags"]
        score_zero = res_zero["total_score"]
        score_fifteen = res_fifteen["total_score"]

        print(f"\n[EMPIRICAL SHADOWBAN TEST]")
        print(f"Posts=2, Views=0  -> Total Score: {score_zero:.1f}, Flags: {res_zero['breakdown']['flags']}, Penalty: {res_zero['breakdown']['penalties_deducted']}")
        print(f"Posts=2, Views=15 -> Total Score: {score_fifteen:.1f}, Flags: {res_fifteen['breakdown']['flags']}, Penalty: {res_fifteen['breakdown']['penalties_deducted']}")

        if not has_flag_zero:
            print("[BUG CONFIRMED] Line 952 'if views_today > 0 and views_today < 50' ignores views_today == 0!")
            print(f"[INVERTED MONOTONICITY] 0 views score ({score_zero}) > 15 views score ({score_fifteen})!")

        # Verify whether zero views triggers shadowban
        self.assertIn(
            "RIESGO_SHADOWBAN",
            res_zero["breakdown"]["flags"],
            "CRITICAL FLAW: Active account with posts but 0 views did NOT trigger RIESGO_SHADOWBAN because code requires 'views_today > 0'!",
        )

    # =========================================================================
    # 7. Monotonicity and Boundary Invariants (1,000+ Monte-Carlo Synthetic Cases)
    # =========================================================================
    def test_monte_carlo_1000_synthetic_configurations(self):
        """Runs 1,000+ randomized synthetic configurations to verify clamping and invariants."""
        statuses = ["activo", "calentamiento", "archivado", "pausado", "revision", "desconocido"]
        channel_states = ["activo", "pausado", "calentamiento", "error", None]

        violations = []
        for i in range(1000):
            status = random.choice(statuses)
            v_today = random.choice([0, 1, 2, 5, 20, random.randint(-5, 50)])
            views = random.choice([0, 10, 49, 50, 100, 10000, 10**6, 10**9, random.randint(-100, 50000)])
            clicks = random.choice([0, 1, 10, 50, random.randint(-10, 500)])
            d_last = random.choice([None, 0, 1, 2, 3, 4, 5, 10, 365, random.randint(-5, 100)])

            cluster = {}
            for ch in ["youtube_shorts", "instagram_reels", "facebook_reels", "tiktok"]:
                if random.random() > 0.2:
                    cluster[ch] = {
                        "estado": random.choice(channel_states),
                        "videos_publicados": random.randint(0, 50),
                        "reproducciones_totales": random.randint(0, 500000),
                        "ultimo_post": "2026-09-23T15:00:00Z" if random.random() > 0.3 else None,
                    }

            history = []
            for h in range(random.randint(0, 10)):
                history.append({
                    "fecha": f"2026-09-{h+1:02d}",
                    "vistas": random.randint(0, 50000),
                    "videos_publicados": random.randint(0, 5),
                    "clics_checkout": random.randint(0, 100),
                })

            synth_b = {
                "id": f"mc-{i}",
                "status": status,
                "cluster_canales": cluster,
                "metricas_resumen": {
                    "videos_hoy": v_today,
                    "vistas_hoy": views,
                    "clics_tienda_hoy": clicks,
                    "dias_sin_publicar": d_last,
                    "tasa_conversion_bio_pct": random.choice([None, 0.0, 0.5, 1.2, 5.0, -1.0]),
                },
                "historial_metricas": history,
            }

            try:
                res = HealthScorer.calculate_score(synth_b)
                score = res["total_score"]

                if not (0.0 <= score <= 100.0):
                    violations.append(f"Case {i}: score {score} out of [0, 100]")

                if math.isnan(score) or math.isinf(score):
                    violations.append(f"Case {i}: score is NaN or Inf: {score}")

                valid_tiers = ["optimo", "estable", "alerta", "critico"]
                if res["health_status"] not in valid_tiers:
                    violations.append(f"Case {i}: invalid health_status {res['health_status']}")

            except Exception as e:
                violations.append(f"Case {i}: Uncaught exception: {type(e).__name__}: {e}")

        self.assertEqual(len(violations), 0, f"Found {len(violations)} invariant violations in 1,000 cases: {violations[:5]}")


if __name__ == "__main__":
    unittest.main()
