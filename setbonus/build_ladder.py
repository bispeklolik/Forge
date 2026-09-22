# -*- coding: utf-8 -*-
"""
ЛЕСЕНКА ОПЫТНЫХ ПРЕДМЕТОВ — ищем, чем наша карточка отличается от рабочей.

Установлено делом: броня «Бродяги» переживает загрузку, наш камень — нет.
Значит и дополнение, и игра, и W3EE ни при чём: дело в полях КАРТОЧКИ.

Вместо перебора догадок делаем лесенку: шесть предметов, каждый на один шаг
ближе к нашему камню. Один заход в игру — и видно, на какой ступеньке ломается.

    T1  точная копия брони «Бродяги» (сменено только имя)
    T2  T1, но категория upgrade вместо armor
    T3  T2, но без снаряжательных полей (шаблон, слоты, прочность, варианты)
    T4  T3, но наши ярлыки
    T5  T4, но наш значок и наши подписи
    T6  наш настоящий камень (для сверки)

Все шесть кладутся в наше дополнение рядом с камнями. Опытные предметы
безобидны: это отдельные записи, ничего не переопределяют.
"""
import os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
T = "\t"
P = T * 4

# Свойство-копия «Бродяги», объявляется у нас же — чтобы лесенка не зависела
# от того, установлен ли сам «Бродяга».
LADDER_ABILITY = "SBT Ladder _Stats"
LADDER_ABILITY_XML = (
    T * 3 + '<ability name="' + LADDER_ABILITY + '">\n'
    + T * 4 + "<tags></tags>\n"
    + T * 4 + '<armor type="base" always_random="false" min="80" max="80"/>\n'
    + T * 4 + '<quality type="add" min="4" max="4"/>\n'
    + T * 4 + '<weight type="base" min="12" />\n'
    + T * 3 + "</ability>\n"
)

VAG_ICON = "icons/vagabicon.dds"
OUR_ICON = "icons/inventory/ingredients/runes/rune_stribog_greater_64x64.png"
VAG_KEY = "modva_item_name_vagabond_armor"
VAG_DESC = "modva_item_desc_vagabond_armor"


def item(name, category, gear, tags, icon, key, desc, extra_ability=True):
    """gear — снаряжательные поля, которые есть у брони и которых нет у камня."""
    s = T * 3 + '<item name="' + name + '"\n'
    s += P + 'category="' + category + '"\n'
    s += P + 'stackable="1"\n'
    if gear:
        s += P + 'enhancement_slots="3"\n'
        s += P + 'equip_template="t_01_vagabond"\n'
        s += P + 'ability_mode="OnMount"\n'
    s += P + 'grid_size="2"\n' if gear else P + 'grid_size="1"\n'
    s += P + 'icon_path="' + icon + '"\n'
    s += P + 'localisation_key_name="' + key + '"\n'
    s += P + 'localisation_key_description="' + desc + '"\n'
    s += P + 'price="300"\n'
    if gear:
        s += P + 'initial_durability="100"\n'
        s += P + 'max_durability="100"\n'
    s = s.rstrip("\n") + " >\n"
    s += P + "<tags>" + tags + "</tags>\n"
    if gear:
        s += P + "<bound_items>\n" + P + "</bound_items>\n"
    s += P + "<base_abilities>\n"
    s += P + T + "<a>" + LADDER_ABILITY + "</a>\n"
    if extra_ability:
        s += P + T + "<a>Default armor _Stats</a>\n"
    s += P + "</base_abilities>\n"
    if gear:
        s += P + "<variants>\n"
        s += P + T + '<variant equip_template="t_01a_vagabond" category="gloves"></variant>\n'
        s += P + "</variants>\n"
    s += T * 3 + "</item>\n"
    return s


VAG_TAGS = "Armor,MediumArmor, mod_armor"
OUR_TAGS = "mod_upgrade, mod_dye, SBT_Stone, SBT_Gryphon"

LADDER = (
    # T1: точная копия брони, сменено только имя
    item("SBT T1 copy", "armor", True, VAG_TAGS, VAG_ICON, VAG_KEY, VAG_DESC)
    # T2: категория как у камня
    + item("SBT T2 upgrade", "upgrade", True, VAG_TAGS, VAG_ICON, VAG_KEY, VAG_DESC)
    # T3: убраны снаряжательные поля
    + item("SBT T3 plain", "upgrade", False, VAG_TAGS, VAG_ICON, VAG_KEY, VAG_DESC)
    # T4: наши ярлыки
    + item("SBT T4 tags", "upgrade", False, OUR_TAGS, VAG_ICON, VAG_KEY, VAG_DESC)
    # T5: наш значок и наши подписи
    + item("SBT T5 ours", "upgrade", False, OUR_TAGS, OUR_ICON,
           "sbt_st_griffin", "sbt_st_desc", extra_ability=False)
)

if __name__ == "__main__":
    # Вклеиваем лесенку в собранные карточки и пересобираем дополнение.
    src = Path(os.environ["TEMP"]) / "sbt_raw" / "gameplay" / "items" / "sbt_items.xml"
    if not src.exists():
        print("нет собранных карточек — сначала build_item.py")
        sys.exit(1)

    print("=" * 66)
    print("  Лесенка опытных предметов")
    print("=" * 66)

    for branch in ("items", "items_plus"):
        p = Path(os.environ["TEMP"]) / "sbt_raw" / "gameplay" / branch / "sbt_items.xml"
        t = p.read_bytes().decode("utf-16")
        if "SBT T1 copy" in t:
            print("   [--] лесенка уже вклеена в %s" % branch)
            continue
        # свойство — в раздел свойств, предметы — в раздел предметов
        t = t.replace("\t\t</abilities>", LADDER_ABILITY_XML.replace("\n", "\r\n") + "\t\t</abilities>")
        t = t.replace("\t\t<items>\r\n", "\t\t<items>\r\n" + LADDER.replace("\n", "\r\n"))
        p.write_bytes(t.encode("utf-16"))
        print("   [ok] вклеено в %s" % branch)

    print()
    r = subprocess.run([sys.executable, str(HERE / "build_dlc.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (r.stdout or "").splitlines():
        if any(k in line for k in ("[ok]", "[!!]", "[--]", "ГОТОВО")):
            print("   " + line.strip())

    print()
    print("   В ИГРЕ — взять все шесть и проверить полным кругом:")
    for n in ("SBT T1 copy", "SBT T2 upgrade", "SBT T3 plain",
              "SBT T4 tags", "SBT T5 ours", "SBT Runestone Griffin"):
        print("     additem('%s')" % n)
    print()
    print("   Сохраниться, ВЫЙТИ В МЕНЮ, загрузиться и сказать,")
    print("   какие остались, а какие пропали — по номерам.")
