# p528

Python-реализация **ITU-R P.528-5** — «A propagation prediction method
for aeronautical mobile and radionavigation services using the VHF,
UHF and SHF bands».

Порт эталонной C++ реализации NTIA `NTIA/p528`.

## Установка

```bash
pip install -e ../p835
pip install -e ../p676
pip install -e .
```

## Использование

```python
from p528 import p528

r = p528(d__km=100.0, h_1__meter=30.0, h_2__meter=3000.0,
         f__mhz=300.0, T_pol=1, p=50.0)
print(r.A__db, r.propagation_mode)
```

## Тесты

```bash
pytest tests/ -v
```

## Attribution

ATTRIBUTION AND SOURCES
========================

This software (PyP528) is a Python implementation of the mathematical
model described in:

    ITU-R P.528-5 — "A propagation prediction method for aeronautical mobile and radionavigation services using the VHF, UHF and SHF bands"
    International Telecommunication Union, Radiocommunication Sector (ITU-R)
    Geneva, Switzerland

The ITU-R Recommendations are publicly available at:
    https://www.itu.int/rec/R-REC-P.528-5/en

The original reference implementation in C++ was published by the
U.S. National Telecommunications and Information Administration (NTIA)
and is available at:
    https://github.com/NTIA/p528-5

The Python port was created by:
    Evgeny Gennadievich Prutkov <sviazist.pr@gmail.com>, 2026

This software is provided under the MIT License (see LICENSE).

The author of this port is not affiliated with ITU or NTIA. All
formulas and algorithms are taken from the publicly available
ITU-R Recommendations.
