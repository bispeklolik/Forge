# -*- coding: utf-8 -*-
"""Облики, чьи модели живут НЕ в игре и НЕ в W3EE (релиз 26.09).

Жетон такого облика есть в основном пакете кузницы, но модель — в другом
моде или в нашем дополнении с чужими моделями:
  - дополнения кузницы: dlcFRGTW2 (TW2 Gear), dlcFRGZmeya и dlcFRGVesemir
    (доспехи Каэр-Морхена) — выкладываются отдельно, с разрешения авторов;
  - чужие моды-DLC: Raven Armor, Frayed, Vagabond.
Скрипт кузницы предлагает такой жетон в лавке, только если карточка донора
есть в игре (мод стоит), — иначе выкованная вещь была бы без модели.

Один источник для build_blanks.py (жетоны «только облик») и build_lab.py
(ворота лавки).
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# чужие моды-DLC и перенесённый доспех Весемира (dlcFRGVesemir)
BASE = {"Frayed Armor", "Frayed Gloves", "Raven Armor", "Raven Pants",
        "Raven Gloves", "Raven Boots", "vagabondarmor", "Vesemir KM Armor"}

# списки пишут сборщики дополнений
_JSONS = [os.path.join(HERE, "tw2", "tw2_donors.json"),
          os.path.join(HERE, "zmeya_donors.json")]


def donor_names():
    """Все доноры-облики с моделью вне игры и W3EE."""
    out = set(BASE)
    for p in _JSONS:
        if os.path.exists(p):
            out |= {d["name"] for d in json.load(io.open(p, encoding="utf-8"))}
    return out
