# -*- coding: utf-8 -*-
"""Общая таблица чар для мода «Камни чар».

Живёт отдельным файлом, потому что её читают ОБА сборщика, а импортировать
build_core ради таблицы нельзя: он при импорте пишет .ws и правит mods.settings.

Коды 1..15 — те же, что у кузницы (forge/ui_data.EFFECTS): ярлык карточки,
значение перечисления эффекта, русское и английское имя.
"""

# (код, ярлык карточки, значение перечисления, ru, en)
CHARMS = [
    (1,  "SwordCritVigorEffect",        "EET_SwordCritVigor",        "Крит даёт энергию",   "Crit restores vigor"),
    (2,  "SwordRendBlastEffect",        "EET_SwordRendBlast",        "Взрывной размах",     "Rend blast"),
    (3,  "SwordInjuryHealEffect",       "EET_SwordInjuryHeal",       "Раны лечат",          "Injuries heal"),
    (4,  "SwordDancingEffect",          "EET_SwordDancing",          "Танцующий клинок",    "Dancing blade"),
    (5,  "SwordQuenEffect",             "EET_SwordQuen",             "Квен при ударе",      "Quen on strike"),
    (6,  "SwordWraithbaneEffect",       "EET_SwordWraithbane",       "Гроза призраков",     "Wraithbane"),
    (7,  "SwordBloodFrenzyEffect",      "EET_SwordBloodFrenzy",      "Кровавое безумие",    "Blood frenzy"),
    (8,  "SwordKillBuffEffect",         "EET_SwordKillBuff",         "Удар после убийства", "Kill momentum"),
    (9,  "SwordBeheadEffect",           "EET_SwordBehead",           "Обезглавливание",     "Beheading"),
    (10, "SwordGasEffect",              "EET_SwordGas",              "Взрывное облако",     "Gas cloud"),
    (11, "SwordSignDancerEffect",       "EET_SwordSignDancer",       "Танцор знаков",       "Sign dancer"),
    (12, "SwordReachoftheDamnedEffect", "EET_SwordReachoftheDamned", "Длань проклятых",     "Reach of the damned"),
    (13, "SwordDarkCurseEffect",        "EET_SwordDarkCurse",        "Тёмное проклятье",    "Dark curse"),
    (14, "SwordDesperateActEffect",     "EET_SwordDesperateAct",     "Отчаянный шаг",       "Desperate act"),
    (15, "SwordRedTearEffect",          "EET_SwordRedTear",          "Красная слеза",       "Red tear"),
]

# Имя карточки заряженного камня: код внутри имени, чтобы скрипт и сборщик
# предметов не расходились.
STONE = "CHT Charmstone %d"

EMPTY_NAME = "CHT Empty Charmstone"
CLEAN_NAME = "CHT Cleansing Charmstone"
