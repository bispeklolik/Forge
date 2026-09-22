# -*- coding: utf-8 -*-
u"""ОБЛИК «ДОСПЕХ ВЕСЕМИРА ИЗ КАЭР-МОРХЕНА» — своим предметом, по образцу Ворона.

Заказ ГД 15.09: «я просил просто оставить все доспехи ванильные как есть, но
просто взять облики из этих модов». Моды modVesemirArmourKaerMo* кладут свои
меши ПОВЕРХ ванильных путей armor__viper — пока они стоят, ванильного вида
Змеи в сборке не существует вообще.

Мод «Raven Armor Set» показывает, как надо: свои папки, свои .w2ent, свои
меши, ваниль не тронута. Делаем так же.

УСТРОЙСТВО ОБЛИКА БРОНИ (проверено по файлам):
    карточка предмета .equip_template
        -> КАРТОЧНЫЙ слой  items\\bodyparts\\...\\t_01_mg__viper_lvl3.w2ent
           (краски: appearances dye_*, coloringEntries)
        -> МЕШЕВЫЙ слой    characters\\...\\armor__viper\\t_01_mg__viper_lvl3_meshes.w2ent
        -> собственно меши .w2mesh (+ парный .1.buffer с геометрией)

Приём: оба слоя копируются, а пути внутри них подменяются на СВОЙ каталог
ТОЙ ЖЕ ДЛИНЫ — armor__viper -> armor__vsmkm, viper -> vsmkm (по 5 букв).
Равная длина не двигает ни одного смещения в файле, поэтому ничего не рушится.
Сами .w2mesh своего пути внутри не содержат — кладутся байт-в-байт.

⛔ Ничего не писать в папку игры, пока игра запущена: сборка идёт в TEMP,
   перенос — отдельным шагом `python build_vesemir.py --install`.
"""
import os, re, shutil, subprocess, sys, zlib
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.path.insert(0, r"D:\Apps\w3ee-tweaks\setbonus")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from medallion import bundles as B
import passport

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
WCC = GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe"

# зеркало wcc_lite вне папки игры: он пишет свой wcc.log рядом с собой, а в
# папку игры при запущенной игре лезть нельзя
MIRROR_HINT = (r"C:\Users\New\AppData\Local\Temp\claude"
               r"\D------------------code\cf8f9b66-aa9a-41aa-b846-b23c4f60306c"
               r"\scratchpad\me\wcc")

WORK = Path(os.environ["TEMP"]) / "frgves"
RAW = WORK / "raw"
OUT = WORK / "content"
DLC = GAME / "dlc" / "dlcFRGVesemir"

MOUNT = "frgvesemir"
DLC_ID = "frg_vesemir"
ITEMS = "frgvesemir_items.xml"
SHOP = "frgvesemir_shop.xml"
EXTS = "frgvesemir_item_extensions.xml"

# свой каталог мешей: ровно 12 букв, как armor__viper — иначе не подменить
# путь байт-в-байт. Подстрока vsmkm во всей сборке не встречается (проверено).
OLD_DIR, NEW_DIR = "armor__viper", "armor__vsmkm"
OLD_TAG, NEW_TAG = "viper", "vsmkm"

ITEM_NAME = "Vesemir KM Armor"
EQUIP_TPL = "t_01_mg__vsmkm_lvl3"

EMPTY_XML = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items>\r\n\t\t</items>\r\n\t</definitions>\r\n</redxml>\r\n')


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 70); say("  " + s); say("=" * 70)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


# ---- чтение бандлов -----------------------------------------------------------
def grab(bundle, want, size=None):
    """Достаёт запись бандла по имени. Имена в оглавлении с обратными слэшами."""
    want_l = want.lower().replace("/", "\\")
    idx = B.read_index(bundle)
    for e in idx:
        n = str(getattr(e, "name", "")).lower().replace("/", "\\")
        if n == want_l:
            data = B.extract(bundle, e)
            if data is None:
                raise SystemExit("[!!] не распаковалось: %s" % want)
            if size is not None and len(data) != size:
                say("   [!] %s: ожидалось %d Б, получено %d" % (want, size, len(data)))
            return data
    raise SystemExit("[!!] нет записи %s в %s" % (want, bundle))


def find_bundle_with(root, want):
    """Первый бандл под root, в котором есть такая запись."""
    want_l = want.lower().replace("/", "\\")
    for f in sorted(Path(root).rglob("*.bundle")):
        try:
            idx = B.read_index(f)
        except Exception:
            continue
        for e in idx:
            if str(getattr(e, "name", "")).lower().replace("/", "\\") == want_l:
                return f
    return None


# ---- подмена путей ------------------------------------------------------------
def swap(buf, old, new, tag, count):
    """Замена РАВНОЙ ДЛИНЫ: ни одно смещение в файле не едет."""
    o, n = old.encode("latin-1"), new.encode("latin-1")
    assert len(o) == len(n), (tag, "разная длина", len(o), len(n))
    got = buf.count(o)
    assert got == count, (tag, "вхождений %d, ждали %d" % (got, count))
    return buf.replace(o, n)


def main():
    head("ОБЛИК ВЕСЕМИРА — сборка")
    if WORK.exists():
        shutil.rmtree(WORK)
    RAW.mkdir(parents=True)

    P = "characters\\models\\geralt\\armor\\"
    VAN_MESHES = P + OLD_DIR + "\\t_01_mg__viper_lvl3_meshes.w2ent"
    VAN_CARD = "items\\bodyparts\\geralt_items\\trunk\\witcher_viper\\t_01_mg__viper_lvl3.w2ent"
    MOD_TORSO = P + OLD_DIR + "\\t_01_mg__viper.w2mesh"
    MOD_BELT = P + OLD_DIR + "\\i_01_mg__viper.w2mesh"

    say("   Ищу ванильные слои облика Змеи...")
    b_card = find_bundle_with(GAME / "content", VAN_CARD)
    b_mesh = find_bundle_with(GAME / "content", VAN_MESHES)
    if not b_card or not b_mesh:
        raise SystemExit("[!!] ванильные .w2ent не найдены: card=%s meshes=%s"
                         % (b_card, b_mesh))
    say("   [ok] %s" % b_card.name)

    A = grab(b_card, VAN_CARD, 15229)          # слой красок
    C2 = grab(b_mesh, VAN_MESHES, 10272)       # слой мешей

    say("   Беру меши модов Весемира...")
    m_torso = GAME / "mods" / "modVesemirArmourKaerMoV2" / "content"
    m_belt = GAME / "mods" / "modVesemirArmourKaerMoBeltsV3" / "content"
    torso = grab(m_torso / "blob0.bundle", MOD_TORSO, 12405)
    torso_buf = grab(m_torso / "buffers0.bundle", MOD_TORSO + ".1.buffer", 420342)
    belt = grab(m_belt / "blob0.bundle", MOD_BELT, 5166)
    belt_buf = grab(m_belt / "buffers0.bundle", MOD_BELT + ".1.buffer", 132546)
    say("   [ok] торс %d Б (+буфер %d), пояс %d Б (+буфер %d)"
        % (len(torso), len(torso_buf), len(belt), len(belt_buf)))

    # --- слой мешей: две ссылки на свои меши; остальные четыре (подвеска,
    #     крюк, ткань, w3dyng) остаются ванильными и копировать их не надо
    n0 = len(C2)
    C2 = swap(C2, P + OLD_DIR + "\\t_01_mg__viper.w2mesh",
              P + NEW_DIR + "\\t_01_mg__vsmkm.w2mesh", "meshes/torso", 2)
    C2 = swap(C2, P + OLD_DIR + "\\i_01_mg__viper.w2mesh",
              P + NEW_DIR + "\\i_01_mg__vsmkm.w2mesh", "meshes/belt", 2)
    assert len(C2) == n0, "слой мешей: размер поехал"

    # --- слой красок: одна ссылка, на слой мешей. Короткие куски не трогать:
    #     "t_01_mg__viper" встречается ещё и как componentName в coloringEntries
    n0 = len(A)
    A = swap(A, VAN_MESHES, P + NEW_DIR + "\\t_01_mg__vsmkm_lvl3_meshes.w2ent",
             "card/meshes-ref", 1)
    assert len(A) == n0, "слой красок: размер поехал"
    assert A.count(b"componentName") >= 1, "слой красок: componentName потерян"
    say("   [ok] пути подменены, размеры файлов не изменились")

    # --- карточка предмета: поля списываем с живой ванильной карточки Змеи
    card = build_card()

    # --- раскладка --------------------------------------------------------------
    mesh_dir = RAW / "characters" / "models" / "geralt" / "armor" / NEW_DIR
    mesh_dir.mkdir(parents=True)
    (mesh_dir / "t_01_mg__vsmkm_lvl3_meshes.w2ent").write_bytes(C2)
    (mesh_dir / "t_01_mg__vsmkm.w2mesh").write_bytes(torso)
    (mesh_dir / "t_01_mg__vsmkm.w2mesh.1.buffer").write_bytes(torso_buf)
    (mesh_dir / "i_01_mg__vsmkm.w2mesh").write_bytes(belt)
    (mesh_dir / "i_01_mg__vsmkm.w2mesh.1.buffer").write_bytes(belt_buf)

    base = RAW / "dlc" / MOUNT
    (base / "data" / "items").mkdir(parents=True)
    (base / "data" / "items" / (EQUIP_TPL + ".w2ent")).write_bytes(A)
    for branch in ("items", "items_plus"):
        d = base / "data" / "gameplay" / branch
        d.mkdir(parents=True)
        (d / ITEMS).write_bytes(card.encode("utf-16"))
        (d / SHOP).write_bytes(EMPTY_XML.encode("utf-16"))
        (d / EXTS).write_bytes(EMPTY_XML.encode("utf-16"))
    (base / (MOUNT + ".reddlc")).write_bytes(
        passport.build(mount=MOUNT, name_key=DLC_ID, desc_key=DLC_ID + "_desc",
                       items_xml=ITEMS, shop_xml=SHOP, exts_xml=EXTS,
                       templates_dir="data/items/"))
    (RAW / "strings.list").write_bytes(b'{\n    "files": []\n}')
    say("   [ok] сырьё разложено: %d файлов"
        % sum(1 for _ in RAW.rglob("*") if _.is_file()))

    # --- упаковка ---------------------------------------------------------------
    OUT.mkdir(parents=True)
    wcc, cwd = wcc_pair()
    r = subprocess.run([str(wcc), "pack", "-dir=" + str(RAW), "-outdir=" + str(OUT)],
                       capture_output=True, text=True, timeout=600, cwd=str(cwd))
    if not (OUT / "blob0.bundle").exists():
        say("   [!!] pack не собрал (код %d)" % r.returncode)
        for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-10:]:
            say("      " + line.strip()[:120])
        sys.exit(1)
    r = subprocess.run([str(wcc), "metadatastore", "-path=" + str(OUT)],
                       capture_output=True, text=True, timeout=600, cwd=str(cwd))
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines():
        if "buffer" in line.lower() or "numresources" in line.lower():
            say("      " + line.strip()[:120])
    say("   [ok] blob0 %d Б, buffers0 %d Б"
        % ((OUT / "blob0.bundle").stat().st_size,
           (OUT / "buffers0.bundle").stat().st_size
           if (OUT / "buffers0.bundle").exists() else 0))

    verify()
    head("СОБРАНО")
    say("   Готово в: %s" % OUT)
    say("   Перенести в игру (ТОЛЬКО при закрытой игре):")
    say("       python build_vesemir.py --install")


def build_card():
    """Карточка нового предмета: поля — с живой ванильной карточки Змеи той же
    ступени, чтобы ничего не выдумывать; меняются имя, облик и подпись."""
    # в игровых xml между именем поля и "=" стоят табы — искать только regex
    want = re.compile(r'equip_template\s*=\s*"t_01_mg__viper_lvl3"')
    src = None
    for f in sorted((GAME / "content").rglob("*.bundle")):
        try:
            idx = B.read_index(f)
        except Exception:
            continue
        for e in idx:
            n = str(getattr(e, "name", "")).lower()
            if not n.endswith(".xml") or "items_plus" in n or not B.can_extract(e):
                continue
            try:
                raw = B.extract(f, e)
            except Exception:
                continue
            if not raw:
                continue
            for enc in ("utf-16", "utf-8"):
                try:
                    t = raw.decode(enc)
                    break
                except Exception:
                    t = None
            m = want.search(t) if t else None
            if not m:
                continue
            i = m.start()
            s = t.rfind("<item", 0, i)
            j = t.find(">", i)
            if s >= 0 and j > 0:
                src = t[s:j + 1]
                break
        if src:
            break
    if not src:
        raise SystemExit("[!!] не нашёл ванильную карточку Змеи 3-й ступени")

    icon = re.search(r'icon_path\s*=\s*"([^"]*)"', src)
    icon = icon.group(1) if icon else "icons/inventory/quests/ico_recipe.png"
    say("   [ok] поля списаны с ванильной карточки Змеи (иконка %s)" % icon)

    T = "\t"
    attrs = [("name", ITEM_NAME), ("category", "armor"), ("price", "88"),
             ("initial_durability", "100"), ("max_durability", "100"),
             ("enhancement_slots", "0"), ("stackable", "1"), ("grid_size", "2"),
             ("ability_mode", "OnMount"), ("equip_template", EQUIP_TPL),
             ("localisation_key_name", "frgv_vesemir"),
             ("localisation_key_description", "item_category_medium_armor_description"),
             ("icon_path", icon)]
    body = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n'
            + T + "<definitions>\r\n" + T * 2 + "<items>\r\n"
            + T * 3 + "<item\r\n"
            + "".join(T * 4 + '%-32s="%s"\r\n' % (k, v) for k, v in attrs)
            + T * 3 + ">\r\n"
            + T * 4 + "<tags>Armor, MediumArmor, mod_armor, NoShow</tags>\r\n"
            + T * 4 + "<base_abilities></base_abilities>\r\n"
            + T * 3 + "</item>\r\n"
            + T * 2 + "</items>\r\n" + T + "</definitions>\r\n</redxml>\r\n")
    import xml.etree.ElementTree as ET
    ET.fromstring(body.replace('<?xml version="1.0" encoding="UTF-16"?>', ""))
    return body


def wcc_pair():
    """wcc_lite и папка, из которой его звать: свой лог рядом с игрой нам не
    нужен, поэтому зеркало в TEMP, если оно есть."""
    for m in (Path(os.environ["TEMP"]) / "frgves_wcc" / "bin" / "x64" / "wcc_lite.exe",
              Path(MIRROR_HINT) / "bin" / "x64" / "wcc_lite.exe"):
        if m.exists():
            return m, m.parent
    return WCC, WCC.parent


def verify():
    """Проверки, которые можно сделать не заходя в игру."""
    say()
    say("   ПРОВЕРКА:")
    idx = [str(getattr(e, "name", "")).replace("/", "\\")
           for e in B.read_index(OUT / "blob0.bundle")]
    bad = [n for n in idx if n.lower().startswith("characters\\models\\geralt\\armor\\"
                                                  + OLD_DIR)]
    say("      ванильные пути Змеи в бандле: %d (должно быть 0)" % len(bad))
    assert not bad, "ВАНИЛЬ ПЕРЕКРЫТА — так нельзя"
    need = [EQUIP_TPL + ".w2ent", "t_01_mg__vsmkm_lvl3_meshes.w2ent",
            "t_01_mg__vsmkm.w2mesh", "i_01_mg__vsmkm.w2mesh"]
    for n in need:
        hit = [x for x in idx if x.lower().endswith(n.lower())]
        say("      %-38s %s" % (n, "есть" if hit else "НЕТ"))
        assert hit, n
    if (OUT / "buffers0.bundle").exists():
        bufs = B.read_index(OUT / "buffers0.bundle")
        say("      буферов геометрии: %d (должно быть 2)" % len(bufs))
    say("      записей всего: %d" % len(idx))


def install():
    head("ПЕРЕНОС В ИГРУ")
    if game_running():
        say("   [!!] игра запущена — закрой её и повтори")
        sys.exit(1)
    if not (OUT / "blob0.bundle").exists():
        say("   [!!] нечего ставить, сначала сборка без --install")
        sys.exit(1)
    dst = DLC / "content"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for f in OUT.iterdir():
        if f.is_file():
            shutil.copyfile(f, dst / f.name)
    say("   [ok] %s" % dst)
    key = "DlcEnabled_%s" % DLC_ID
    for name in ("user.settings", "dx12user.settings"):
        p = DOCS / name
        if not p.exists():
            continue
        t = p.read_bytes().decode("utf-8", "replace")
        if key in t:
            say("   [--] %s — уже включено" % name)
            continue
        m = re.search(r"\[DLC\]\r?\n", t)
        t = (t[:m.end()] + "%s=1\r\n" % key + t[m.end():]) if m else \
            (t.rstrip("\r\n") + "\r\n[DLC]\r\n%s=1\r\n" % key)
        p.write_bytes(t.encode("utf-8"))
        say("   [ok] %s — включено" % name)
    say()
    say("   Дальше: пересобрать dlcFRGBlanks (build_blanks.py) — тогда облик")
    say("   появится жетоном у Элихаля, и можно сносить моды-замены.")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        if game_running():
            say("   [i] игра запущена — собираю в TEMP, папку игры не трогаю")
        main()
