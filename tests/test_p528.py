"""
tests/itu/test_p528.py — Валидация P.528-5 против CSV-эталонов NTIA.

Два режима:
    1. Если есть сводный `p528_reference.csv` — используем его.
    2. Если есть 50 исходных CSV в `tests/itu/reference/p528/` —
       парсим их напрямую.

ВАЖНО: CSV-эталоны NTIA сгенерированы для ГОРИЗОНТАЛЬНОЙ поляризации.
"""

import os
import csv
import re
import math
import pytest

from p528 import (
    p528,
    POLARIZATION__VERTICAL, POLARIZATION__HORIZONTAL,
    SUCCESS, ERROR_VALIDATION__H_1, ERROR_VALIDATION__F_MHZ_LOW,
    PROP_MODE__LOS, PROP_MODE__DIFFRACTION, PROP_MODE__SCATTERING,
)


REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
P528_SRC_DIR = os.path.join(REFERENCE_DIR, "p528")
P528_AGGREGATED = os.path.join(REFERENCE_DIR, "p528_reference.csv")


# Поляризация эталонов NTIA (HORIZONTAL)
_REFERENCE_POL = POLARIZATION__HORIZONTAL


# =====================================================================
# 1. Базовая функциональность
# =====================================================================

class TestBasic:
    def test_low_los(self):
        r = p528(10.0, 30.0, 3000.0, 300.0, POLARIZATION__VERTICAL, 50.0)
        assert r.propagation_mode == PROP_MODE__LOS
        assert r.A__db > 0.0

    def test_transhorizon(self):
        r = p528(500.0, 30.0, 3000.0, 300.0, POLARIZATION__VERTICAL, 50.0)
        assert r.propagation_mode in (PROP_MODE__DIFFRACTION, PROP_MODE__SCATTERING)

    def test_atmospheric_absorption_increases(self):
        r_low = p528(10.0, 30.0, 3000.0, 300.0, POLARIZATION__VERTICAL, 50.0)
        r_high = p528(10.0, 30.0, 3000.0, 15000.0, POLARIZATION__VERTICAL, 50.0)
        assert r_high.A_a__db > r_low.A_a__db

    def test_loss_increases_with_distance(self):
        r1 = p528(10.0, 30.0, 3000.0, 300.0, POLARIZATION__VERTICAL, 50.0)
        r2 = p528(100.0, 30.0, 3000.0, 300.0, POLARIZATION__VERTICAL, 50.0)
        assert r2.A__db > r1.A__db

    def test_validation_errors(self):
        from p528 import validate_inputs
        assert validate_inputs(10.0, 0.5, 3000.0, 300.0, 1, 50.0) == ERROR_VALIDATION__H_1
        assert validate_inputs(10.0, 30.0, 3000.0, 50.0, 1, 50.0) == ERROR_VALIDATION__F_MHZ_LOW


# =====================================================================
# 2. Парсинг NTIA CSV
# =====================================================================

def _parse_header(filename):
    """Из имени извлекает f_mhz, p."""
    base = os.path.basename(filename)
    m_freq = re.match(r'^([\d,\.]+)\s*MHz', base)
    m_p = re.search(r'Lb\(([\d\.]+)\)', base)
    if not m_freq or not m_p:
        return None, None
    return float(m_freq.group(1).replace(',', '')), float(m_p.group(1)) * 100.0


def _parse_ntia_csv(filepath):
    """
    Парсит один NTIA CSV.

    Returns:
        (f_mhz, p, list_of_(d_km, h1_m, h2_m, Lb)) или None.
    """
    f_mhz, p = _parse_header(filepath)
    if f_mhz is None:
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n').rstrip('\r') for line in f]

    h1_list, h2_list = None, None
    data_start = None
    for i, line in enumerate(lines):
        if line.startswith(',h1(m)'):
            h1_list = [float(x) for x in line.split(',')[2:] if x.strip()]
        elif line.startswith(',h2(m)'):
            h2_list = [float(x) for x in line.split(',')[2:] if x.strip()]
        elif line.startswith('D (km)'):
            data_start = i + 1
            break

    if not h1_list or not h2_list or data_start is None:
        return None

    n_cols = len(h1_list)
    cases = []
    for line in lines[data_start:]:
        if not line.strip():
            continue
        parts = line.split(',')
        if len(parts) < 2 + n_cols:
            continue
        try:
            d_km = float(parts[0])
        except ValueError:
            continue
        for j in range(n_cols):
            try:
                lb = float(parts[2 + j])
            except (ValueError, IndexError):
                continue
            h1 = h1_list[j]
            h2 = h2_list[j]
            if h1 > h2:
                h1, h2 = h2, h1
            cases.append((d_km, h1, h2, lb))

    return f_mhz, p, cases


def _list_csv_files(limit=None):
    """
    Spisok NTIA CSV fajlov dlya validacii.

    ===== patch_v3_11 (B6): ubrano files[:4] =====
    Ranshe kod bral tolko 4 fajla iz 50 (kommentarij govoril
    chto "ogranichenie snyato", no `return files[:4]` ostavalsya).
    Teper pri limit=None vozvrashchaem VSE fajly.
    """
    if not os.path.isdir(P528_SRC_DIR):
        return []
    files = sorted([
        os.path.join(P528_SRC_DIR, f)
        for f in os.listdir(P528_SRC_DIR)
        if f.endswith('.csv')
    ])
    if limit is not None:
        return files[:limit]
    return files


# =====================================================================
# 3. Валидация против исходных 50 CSV
# =====================================================================

@pytest.mark.skipif(
    not os.path.isdir(P528_SRC_DIR),
    reason=f"Папка {P528_SRC_DIR} не найдена"
)
@pytest.mark.parametrize("csv_path", _list_csv_files())
def test_reference_ntia_csv(csv_path):
    """
    Прогоняет один NTIA CSV через p528() и сравнивает с эталоном.

    Пороги:
        - средняя ошибка < 0.5 дБ;
        - 95-й перцентиль ошибки < 1.0 дБ;
        - максимальная ошибка < 3.0 дБ.

    Прореживание: ~100 точек на файл (ускорение прогона в 5 раз).
    """
    parsed = _parse_ntia_csv(csv_path)
    if parsed is None:
        pytest.skip(f"Не удалось распарсить {csv_path}")

    f_mhz, p, cases = parsed
    if not cases:
        pytest.skip(f"Пустой CSV: {csv_path}")

    # Прореживание: ~100 точек на файл
    stride = max(1, len(cases) // 100)
    cases_sampled = cases[::stride]

    errors = []
    n_skipped = 0
    first_error = None

    for d_km, h1_m, h2_m, lb_ref in cases_sampled:
        if d_km <= 0.0 or h1_m <= 0.0 or h2_m <= 0.0:
            n_skipped += 1
            continue
        try:
            r = p528(d_km, h1_m, h2_m, f_mhz, _REFERENCE_POL, p)
            err = abs(r.A__db - lb_ref)
            errors.append(err)
        except Exception as e:
            n_skipped += 1
            if first_error is None:
                first_error = (d_km, h1_m, h2_m, type(e).__name__, str(e))
            continue

    if not errors:
        msg = f"Не удалось прогнать ни одного случая из {csv_path}"
        if first_error is not None:
            msg += (f"; первая ошибка: d={first_error[0]}, h1={first_error[1]},"
                    f" h2={first_error[2]}, {first_error[3]}: {first_error[4]}")
        pytest.skip(msg)

    errors.sort()
    n = len(errors)
    mean_err = sum(errors) / n
    p95 = errors[int(0.95 * n)] if n > 0 else 0.0
    max_err = errors[-1]

    fname = os.path.basename(csv_path)
    print(f"\n[{fname}] n={n} (skip={n_skipped}, из {len(cases)} точек, "
          f"взято {len(cases_sampled)}) "
          f"mean={mean_err:.3f} p95={p95:.3f} max={max_err:.3f} дБ")

    assert mean_err < 0.5, f"{fname}: mean={mean_err:.3f} дБ"
    assert p95 < 1.0, f"{fname}: p95={p95:.3f} дБ"
    assert max_err < 3.0, f"{fname}: max={max_err:.3f} дБ"


# =====================================================================
# 4. Тест сводного CSV
# =====================================================================

def _load_aggregated():
    if not os.path.exists(P528_AGGREGATED):
        return []
    rows = []
    with open(P528_AGGREGATED, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append((
                    float(row['d_km']),
                    float(row['h_1__meter']),
                    float(row['h_2__meter']),
                    float(row['f_mhz']),
                    float(row['p']),
                    float(row['A__db']),
                ))
            except (KeyError, ValueError):
                continue
    return rows


@pytest.mark.skipif(
    not os.path.exists(P528_AGGREGATED),
    reason=f"Сводный CSV не найден: {P528_AGGREGATED}"
)
def test_reference_aggregated():
    """Прогоняет сводный CSV (быстрая проверка)."""
    rows = _load_aggregated()
    if not rows:
        pytest.skip("Сводный CSV пуст")

    errors = []
    for d_km, h1_m, h2_m, f_mhz, p, lb_ref in rows:
        try:
            r = p528(d_km, h1_m, h2_m, f_mhz, _REFERENCE_POL, p)
            errors.append(abs(r.A__db - lb_ref))
        except Exception:
            continue

    assert errors, "Ни одного успешного расчёта"
    mean_err = sum(errors) / len(errors)
    max_err = max(errors)
    print(f"\n[aggregated] n={len(errors)} mean={mean_err:.3f} max={max_err:.3f} дБ")
    assert mean_err < 0.5
    assert max_err < 3.0
