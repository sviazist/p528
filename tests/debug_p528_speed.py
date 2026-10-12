"""
tests/itu/debug_p528_speed.py — Отладка P.528 с разложением по компонентам.

Проверяет три точки на горизонтальной поляризации (если CSV NTIA —
HORIZONTAL). Меняя POLARIZATION, можно сравнить V vs H.
"""

import os
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

sys.path.insert(0, _HERE)
from test_p528 import _parse_ntia_csv, P528_SRC_DIR, _list_csv_files

from p528 import p528, POLARIZATION__VERTICAL, POLARIZATION__HORIZONTAL


# ВАЖНО: если CSV NTIA сгенерирован для HORIZONTAL поляризации,
# поставьте POLARIZATION__HORIZONTAL. Проверяем гипотезу.
POL = POLARIZATION__HORIZONTAL


def detail(d_km, h1_m, h2_m, f_mhz, p, lb_ref):
    """Расчёт с полным разложением по компонентам."""
    import math as _m
    from p528.p528 import p528_ex
    from p528.types import (
        Result, Terminal, Path, LineOfSightParams, TroposcatterParams,
    )
    from p528.ray_optics import ray_optics
    from p528.los import (
        find_psi_at_distance, find_psi_at_delta_r,
    )
    from p528.long_term import long_term_variability
    from p528.nakagami_rice import (
        nakagami_rice, find_k_for_ypi_at_99,
    )
    from p528.math_utils import combine_distributions
    from p528.reflection import reflection_coefficients
    from p528.los import get_path_loss
    from p528.constants import PI as _PI

    result = Result()
    t1 = Terminal()
    t2 = Terminal()
    tropo = TroposcatterParams()
    path = Path()
    los = LineOfSightParams()

    p528_ex(d_km, h1_m, h2_m, f_mhz, POL, p,
            result, t1, t2, tropo, path, los)

    print(f"\n--- Детали d={d_km} h1={h1_m} h2={h2_m} f={f_mhz} p={p} POL={'H' if POL == 0 else 'V'} ---")
    print(f"  ref  A = {lb_ref:.3f} дБ")
    print(f"  ours A = {result.A__db:.3f} дБ  (err = {result.A__db - lb_ref:+.3f})")
    print(f"  mode   = {result.propagation_mode}")
    print(f"  A_fs   = {result.A_fs__db:.3f} дБ")
    print(f"  A_a    = {result.A_a__db:.3f} дБ")
    print(f"  theta_h1 = {result.theta_h1__rad:.6f} рад")
    print(f"  --- terminal_1 ---")
    print(f"    h_r={t1.h_r__km:.4f} h_e={t1.h_e__km:.4f} delta_h={t1.delta_h__km:.6f}")
    print(f"    d_r={t1.d_r__km:.4f} a={t1.a__km:.4f} theta={t1.theta__rad:.6f}")
    print(f"  --- terminal_2 ---")
    print(f"    h_r={t2.h_r__km:.4f} h_e={t2.h_e__km:.4f} delta_h={t2.delta_h__km:.6f}")
    print(f"    d_r={t2.d_r__km:.4f} a={t2.a__km:.4f} theta={t2.theta__rad:.6f}")
    print(f"  --- path ---")
    print(f"    d_ML={path.d_ML__km:.3f} d_0={path.d_0__km:.3f} d_d={path.d_d__km:.3f}")
    print(f"  --- LOS params ---")
    print(f"    r_0={los.r_0__km:.4f} r_12={los.r_12__km:.4f} delta_r={los.delta_r__km:.6f}")
    print(f"    A_LOS={los.A_LOS__db:.3f} d={los.d__km:.4f}")

    # --- variability ---
    lambda_km = 0.2997925 / f_mhz
    terminate_dbg = lambda_km / 1e6
    psi_limit_dbg = find_psi_at_delta_r(lambda_km / 2, path, t1, t2, terminate_dbg)

    th1 = los.theta_h1__rad
    if th1 <= 0.0:
        f_theta_h_dbg = 1.0
    elif th1 >= 1.0:
        f_theta_h_dbg = 0.0
    else:
        f_theta_h_dbg = max(
            0.5 - (1.0 / _PI) * _m.atan(20.0 * _m.log10(32.0 * th1)), 0.0)

    Y_e_dbg, A_Y_dbg = long_term_variability(
        t1.d_r__km, t2.d_r__km, d_km, f_mhz, p, f_theta_h_dbg, los.A_LOS__db)
    Y_e_50_dbg, _ = long_term_variability(
        t1.d_r__km, t2.d_r__km, d_km, f_mhz, 50, f_theta_h_dbg, los.A_LOS__db)

    los_for_R = LineOfSightParams()
    psi_R = find_psi_at_distance(d_km, path, t1, t2)
    ray_optics(t1, t2, psi_R, los_for_R)

    R_Tg_dbg = get_path_loss(
        psi_R, path, f_mhz, psi_limit_dbg, 0.0, 0.0, POL, los_for_R)

    R_g_dbg, phi_g_dbg = reflection_coefficients(psi_R, f_mhz, POL)
    F_r_dbg = min(los_for_R.r_0__km / los_for_R.r_12__km, 1.0) \
              if los_for_R.r_12__km != 0 else 1.0

    F_AY_dbg = 1.0 if A_Y_dbg <= 0 else (
        0.1 if A_Y_dbg >= 9.0
        else (1.1 + 0.9 * _m.cos((A_Y_dbg / 9.0) * _PI)) / 2.0)
    F_dr_dbg = 1.0 if los_for_R.delta_r__km >= lambda_km / 2 else 0.1

    R_s_dbg = R_Tg_dbg * F_dr_dbg * F_AY_dbg

    a_slant_dbg = los_for_R.r_0__km
    Y_pi_99_dbg = 10.0 * _m.log10(f_mhz * a_slant_dbg ** 3) - 84.26
    K_t_dbg = find_k_for_ypi_at_99(Y_pi_99_dbg)

    W_a_dbg = 10.0 ** (K_t_dbg / 10.0)
    W_R_dbg = R_s_dbg ** 2 + 0.01 ** 2
    W_dbg = W_R_dbg + W_a_dbg
    K_LOS_dbg = 10.0 * _m.log10(W_dbg) if W_dbg > 0 else -40.0
    if K_LOS_dbg < -40.0:
        K_LOS_dbg = -40.0

    Y_pi_dbg = nakagami_rice(K_LOS_dbg, p)
    Y_total_dbg = -combine_distributions(Y_e_50_dbg, Y_e_dbg, 0.0, Y_pi_dbg, p)

    print(f"  --- variability ---")
    print(f"    f_theta_h={f_theta_h_dbg:.6f} A_LOS={los.A_LOS__db:.6f}")
    print(f"    Y_e={Y_e_dbg:.6f} A_Y={A_Y_dbg:.6f} Y_e_50={Y_e_50_dbg:.6f}")
    print(f"    psi_R={psi_R:.6f}")
    print(f"    R_g={R_g_dbg:.6f} phi_g={phi_g_dbg:.6f} F_r={F_r_dbg:.6f}")
    print(f"    R_Tg={R_Tg_dbg:.6f}")
    print(f"    F_dr={F_dr_dbg:.6f} F_AY={F_AY_dbg:.6f} R_s={R_s_dbg:.6f}")
    print(f"    Y_pi_99={Y_pi_99_dbg:.6f} K_t={K_t_dbg:.6f}")
    print(f"    W_a={W_a_dbg:.6f} W_R={W_R_dbg:.6f} W={W_dbg:.6f}")
    print(f"    K_LOS={K_LOS_dbg:.6f}")
    print(f"    Y_pi={Y_pi_dbg:.6f}")
    print(f"    Y_total={Y_total_dbg:.6f}")


def main():
    files = _list_csv_files()
    if not files:
        print(f"Не найдено CSV в {P528_SRC_DIR}")
        return

    target_name = "600 MHz - Lb(0.95)"
    path = next(f for f in files if target_name in f)


    print(f"Файл: {os.path.basename(path)}")

    parsed = _parse_ntia_csv(path)
    if parsed is None:
        print("Не распарсилось")
        return

    f_mhz, p, cases = parsed
    print(f"f_mhz = {f_mhz}, p = {p}, точек: {len(cases)}")


    targets = [
        (140.0, 1.5, 1000.0),    # около d_ML
        (200.0, 1.5, 1000.0),    # diffraction
        (500.0, 1.5, 1000.0),    # diffraction/scattering
        (1000.0, 1.5, 1000.0),   # transhorizon
        (200.0, 1.5, 10000.0),   # transhorizon
        (1000.0, 1.5, 10000.0),  # transhorizon
    ]

    for (d_km, h1_m, h2_m) in targets:
        ref = None
        for (dd, hh1, hh2, lb) in cases:
            if abs(dd - d_km) < 1e-6 and abs(hh1 - h1_m) < 1e-3 \
                    and abs(hh2 - h2_m) < 1e-3:
                ref = lb
                break
        if ref is None:
            print(f"\nТочка {d_km},{h1_m},{h2_m} не найдена в CSV")
            continue
        detail(d_km, h1_m, h2_m, f_mhz, p, ref)


if __name__ == '__main__':
    main()
