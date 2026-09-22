# -*- coding: utf-8 -*-
u"""ОБЛИКИ СЛОТА ЗМЕИ (armor__viper) — своими предметами в dlcFRGZmeya.

Заказ ГД 18.09: «Змея — вынести облики отдельными жетонами и снести замены».
На ванильный слот брони Змеи два мода кладут ДВА разных облика Каэр-Морхена:
набор Весемира (5 модов) и Perfect Kaer Morhen. Здесь оба выносятся своими
предметами по путям-двойникам ТОЙ ЖЕ ДЛИНЫ — ваниль не перекрывается ни одним
файлом (приём build_vesemir), а сами моды-замены гасятся при --install
обратимо (префикс «~»), и ванильная Змея возвращается.

Тело+пояс Весемира уже вынесены отдельным жетоном «Vesemir KM Armor»
(dlcFRGVesemir) — его не трогаем. Здесь: сапоги/перчатки/штаны Весемира и весь
набор PKM (торс/перчатки/штаны/сапоги).

ТЕКСТУРЫ. Меши тянут .xbm по пути. Часть — ванильные (в игре всегда, ссылку
не трогаем). Часть мод кладёт СВОИМ файлом:
  * по ВАНИЛЬНОМУ пути (замена) — после сноса мода вернётся ванильная краска,
    поэтому такой .xbm копируем на путь-двойник, чиним его textureCacheKey и
    ссылку в меше (рекей);
  * по СВОЕМУ новому пути — после сноса мода он исчезнет, копируем как есть.
Пиксели живут в texture.cache мода (заголовок .xbm — в blob). Кэши нужных
модов сливаются в один texture.cache DLC (страницы/мип-таблица/строки —
конкатенация со сдвигом), с рекеем строк-замен.

Сухая сборка: python build_zmeya.py           (всё в TEMP, игру не трогает)
Перенос:      python build_zmeya.py --install  (только при закрытой игре;
              переносит DLC И гасит 6 модов-замен префиксом «~»)
"""
import io, json, os, re, struct, shutil, sys
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.path.insert(0, r"D:\Apps\w3ee-tweaks\setbonus")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from medallion import bundles as B
import passport
import build_vesemir as V          # grab, find_bundle_with, swap, wcc_pair, say, head

say, head, grab = V.say, V.head, V.grab
GAME = V.GAME
DOCS = V.DOCS

WORK = Path(os.environ["TEMP"]) / "frgzmeya"
RAW = WORK / "raw"
OUT = WORK / "content"
DLC = GAME / "dlc" / "dlcFRGZmeya"
MOUNT = "frgzmeya"
DLC_ID = "frg_zmeya"
ITEMS = "frgzmeya_items.xml"
SHOP = "frgzmeya_shop.xml"
EXTS = "frgzmeya_item_extensions.xml"

ARM = "characters/models/geralt/armor/"
VDIR = "armor__viper"                       # 12 символов
# слой-карточка (dye) лежит в подпапке слота, не всегда в trunk
CARD_SUB = {"armor": "trunk", "gloves": "gloves", "pants": "legs", "boots": "shoes"}

# путь-двойник на облик: РОВНО 12 символов, как armor__viper, чтобы менять
# путь байт-в-байт. Уникальность проверяется в build().
TWIN = {"Ves": ("armor__vsmkm", "vsmkm"), "PKM": ("armor__prfkm", "prfkm")}

EMPTY_XML = V.EMPTY_XML

# 6 модов, чей облик выносим и которые гасим при --install
REPLACERS = ["modperfectkm", "modVesemirArmourKaerMoV2", "modVesemirArmourKaerMoBeltsV3",
             "modVesemirArmourKaerMoBootsV2", "modVesemirArmourKaerMoGlovesV2",
             "modVesemirArmourKaerMoPantsV4"]


# ---------------------------------------------------------------- h31 / cache --
def h31(s):
    """textureCacheKey = h31(путь при куке) — тот же хэш, что у ключей кэша."""
    if isinstance(s, str):
        s = s.encode("latin-1")
    h = 0
    for b in s:
        h = (h * 31 + b) & 0xFFFFFFFF
    return h


def fnv64(b, h=0xcbf29ce484222325):
    for x in b:
        h = ((h ^ x) * 0x100000001b3) & 0xffffffffffffffff
    return h


def cache_parts(path):
    """Полный разбор texture.cache (TXCH v6): страницы, мип-таблица, строки,
    записи (по 52 Б). Записи держат стартовую страницу [f2], мип-индекс [f8]
    и смещение имени [f1] — их и сдвигаем при слиянии."""
    d = Path(path).read_bytes()
    L = len(d)
    crc, pages, n, ssz, nmip, magic, ver = struct.unpack("<QIIIIII", d[L - 32:L])
    assert magic == 0x54584348 and ver == 6, (path, hex(magic), ver)
    tsz = nmip * 4 + ssz + n * 52
    tstart = L - 32 - tsz
    mip = d[tstart:tstart + nmip * 4]
    strs = d[tstart + nmip * 4:tstart + nmip * 4 + ssz]
    ents = d[tstart + nmip * 4 + ssz:tstart + nmip * 4 + ssz + n * 52]
    page_bytes = d[:pages * 4096]
    # проверка crc
    assert fnv64(mip + strs + ents) == crc, "crc кэша не сошёлся: %s" % path
    return dict(pages=pages, n=n, ssz=ssz, nmip=nmip, mip=mip, strs=strs,
                ents=ents, page_bytes=page_bytes)


def cache_entry_name(strs, ent):
    off = struct.unpack_from("<I", ent, 4)[0]
    z = strs.find(b"\0", off)
    return strs[off:z].decode("latin-1")


def merge_caches(sources):
    """Слить несколько texture.cache в один. sources = [(cache_parts, rekey)]
    где rekey: {старый_путь_с_обратным_слэшем_lower: новый_путь(той же длины)}.
    ⛔ Ключ кэша = h31 пути С ОБРАТНЫМ СЛЭШЕМ (проверено на живых ключах:
    h31('...\\armor__viper\\g_01...') == b9f7ec32), а не с прямым.
    Возвращает готовые байты texture.cache."""
    all_pages = []
    all_mip = []
    all_strs = []
    all_ents = []
    page_ofs = 0        # в СТРАНИЦАХ
    mip_ofs = 0         # в мип-записях
    str_ofs = 0         # в байтах строк
    for c, rekey in sources:
        all_pages.append(c["page_bytes"])
        all_mip.append(c["mip"])
        # строки перекладываем ЦЕЛИКОМ, но у переименованных заменяем текст
        strs = bytearray(c["strs"])
        for i in range(c["n"]):
            ent = bytearray(c["ents"][i * 52:(i + 1) * 52])
            name = cache_entry_name(c["strs"], ent).lower()      # обратный слэш, как в кэше
            noff = struct.unpack_from("<I", ent, 4)[0]
            if name in rekey:
                new = rekey[name]
                old = cache_entry_name(c["strs"], ent)
                assert len(new) == len(old), ("рекей: длина строки", old, new)
                strs[noff:noff + len(old)] = new.encode("latin-1")
                struct.pack_into("<I", ent, 0, h31(new))      # ключ = h31(нового пути, слэши \\)
            # сдвиги
            struct.pack_into("<I", ent, 4, noff + str_ofs)
            sp = struct.unpack_from("<I", ent, 8)[0]
            struct.pack_into("<I", ent, 8, sp + page_ofs)
            mi = struct.unpack_from("<I", ent, 8 + 24)[0]     # field[8] = мип-индекс
            struct.pack_into("<I", ent, 8 + 24, mi + mip_ofs)
            all_ents.append(bytes(ent))
        all_strs.append(bytes(strs))
        page_ofs += c["pages"]
        mip_ofs += c["nmip"]
        str_ofs += c["ssz"]
    mip = b"".join(all_mip)
    strs = b"".join(all_strs)
    ents = b"".join(all_ents)
    pages = b"".join(all_pages)
    n = len(all_ents)
    nmip = len(mip) // 4
    foot = struct.pack("<QIIIIII", fnv64(mip + strs + ents), page_ofs, n, len(strs),
                       nmip, 0x54584348, 6)
    return pages + mip + strs + ents + foot


def xbm_setkey(data, newkey):
    """Прописать textureCacheKey в кукнутый .xbm (по разбору его CProperty)."""
    tabs = [struct.unpack_from("<III", data, 0x28 + i * 12) for i in range(10)]
    soff, ssize, _ = tabs[0]
    blob = data[soff:soff + ssize]

    def s_at(o):
        z = blob.find(b"\0", o)
        return blob[o:z].decode("latin-1")
    names = [s_at(struct.unpack_from("<II", data, tabs[1][0] + i * 8)[0]) for i in range(tabs[1][1])]
    coff, ccnt, _ = tabs[4]
    out = bytearray(data)
    for i in range(ccnt):
        _cn, _obf, _par, dsz, doff, _t, _c = struct.unpack_from("<HHIIIII", data, coff + i * 24)
        off, end = doff + 1, doff + dsz
        while off + 2 <= end:
            ni = struct.unpack_from("<H", data, off)[0]
            if ni == 0:
                break
            _ti, sz = struct.unpack_from("<HI", data, off + 2)
            if names[ni] == "textureCacheKey" and sz == 8:
                struct.pack_into("<I", out, off + 8, newkey)
                return bytes(out), True
            off += 4 + sz
    return data, False


def xbm_key(data):
    tabs = [struct.unpack_from("<III", data, 0x28 + i * 12) for i in range(10)]
    soff, ssize, _ = tabs[0]
    blob = data[soff:soff + ssize]

    def s_at(o):
        z = blob.find(b"\0", o)
        return blob[o:z].decode("latin-1")
    names = [s_at(struct.unpack_from("<II", data, tabs[1][0] + i * 8)[0]) for i in range(tabs[1][1])]
    coff, ccnt, _ = tabs[4]
    for i in range(ccnt):
        _cn, _obf, _par, dsz, doff, _t, _c = struct.unpack_from("<HHIIIII", data, coff + i * 24)
        off, end = doff + 1, doff + dsz
        while off + 2 <= end:
            ni = struct.unpack_from("<H", data, off)[0]
            if ni == 0:
                break
            _ti, sz = struct.unpack_from("<HI", data, off + 2)
            if names[ni] == "textureCacheKey" and sz == 8:
                return struct.unpack_from("<I", data, off + 8)[0]
            off += 4 + sz
    return None


# ---------------------------------------------------------------- карточка -----
def find_card(equip_tpl):
    """Ванильная item-карточка по equip_template — поля списываем с неё, как в
    build_vesemir.build_card (ничего не выдумываем)."""
    want = re.compile(r'equip_template\s*=\s*"%s"' % re.escape(equip_tpl))
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
            t = None
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
                return t[s:j + 1]
    return None


def make_item(name, equip_tpl, category, icon, lockey, desc_key):
    """Один <item> облика (NoShow, без статов) — блок для общего items.xml."""
    T = "\t"
    tagword = {"armor": "MediumArmor", "gloves": "Gloves", "pants": "Pants",
               "boots": "Boots"}[category]
    attrs = [("name", name), ("category", category), ("price", "88"),
             ("initial_durability", "100"), ("max_durability", "100"),
             ("enhancement_slots", "0"), ("stackable", "1"), ("grid_size", "2"),
             ("ability_mode", "OnMount"), ("equip_template", equip_tpl),
             ("localisation_key_name", lockey),
             ("localisation_key_description", desc_key), ("icon_path", icon)]
    return (T * 3 + "<item\r\n"
            + "".join(T * 4 + '%-32s="%s"\r\n' % (k, v) for k, v in attrs)
            + T * 3 + ">\r\n"
            + T * 4 + "<tags>Armor, %s, mod_armor, NoShow</tags>\r\n" % tagword
            + T * 4 + "<base_abilities></base_abilities>\r\n"
            + T * 3 + "</item>\r\n")


def items_xml(items):
    T = "\t"
    body = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n'
            + T + "<definitions>\r\n" + T * 2 + "<items>\r\n"
            + "".join(items) + T * 2 + "</items>\r\n"
            + T + "</definitions>\r\n</redxml>\r\n")
    import xml.etree.ElementTree as ET
    ET.fromstring(body.replace('<?xml version="1.0" encoding="UTF-16"?>', ""))
    return body


# ---------------------------------------------------------------- таблица ------
def _p(*parts):
    return ARM.replace("/", "\\") + "\\".join(parts)


VES = "modVesemirArmourKaerMo"
PKM = "modperfectkm"
MOD_LOOK = {VES + "BootsV2": "Ves", VES + "GlovesV2": "Ves", VES + "PantsV4": "Ves",
            PKM: "PKM"}

# Предмет: имя, облик, слот, слой-карточка (dye), слой-меши, меши (basename, мод).
# Тело+пояс Весемира уже вынесены жетоном «Vesemir KM Armor» (dlcFRGVesemir) —
# здесь его нет. У PKM своё тело (торс+пояс) есть.
PIECES = [
    dict(name="Vesemir KM Boots", look="Ves", cat="boots",
         card="s_01_mg__viper_lvl3", layer="s_01_mg__viper_lvl3_meshes",
         meshes=[("s_01_mg__viper", VES + "BootsV2")]),
    dict(name="Vesemir KM Gloves", look="Ves", cat="gloves",
         card="g_01_mg__viper_lvl3", layer="g_01_mg__viper_lvl3_meshes",
         meshes=[("g_01_mg__viper", VES + "GlovesV2")]),
    dict(name="Vesemir KM Pants", look="Ves", cat="pants",
         card="l_01a_mg__viper_lvl3", layer="l_01a_mg__viper_lvl3_meshes",
         meshes=[("l_01a_mg__viper", VES + "PantsV4")]),
    dict(name="Perfect KM Armor", look="PKM", cat="armor",
         card="t_01_mg__viper_lvl3", layer="t_01_mg__viper_lvl3_meshes",
         meshes=[("t_01_mg__viper", PKM), ("i_01_mg__viper", PKM)]),
    dict(name="Perfect KM Gloves", look="PKM", cat="gloves",
         card="g_01_mg__viper_lvl3", layer="g_01_mg__viper_lvl3_meshes",
         meshes=[("g_01_mg__viper", PKM)]),
    dict(name="Perfect KM Pants", look="PKM", cat="pants",
         card="l_01a_mg__viper_lvl3", layer="l_01a_mg__viper_lvl3_meshes",
         meshes=[("l_01a_mg__viper", PKM)]),
    dict(name="Perfect KM Boots", look="PKM", cat="boots",
         card="s_01_mg__viper_lvl3", layer="s_01_mg__viper_lvl3_meshes",
         meshes=[("s_01_mg__viper", PKM)]),
]


def vanilla_paths():
    """Все пути игры (content + dlc) в нижнем регистре с обратным слэшем."""
    van = set()
    for root in ("content", "dlc"):
        for f in sorted((GAME / root).rglob("*.bundle")):
            try:
                for e in B.read_index(f):
                    van.add(str(e.name).lower().replace("/", "\\"))
            except Exception:
                pass
    return van


def mod_textures(mod, look, van):
    """Разбор кэша мода: rekey {ванильный_путь_lower: двойник}, список путей-
    замен (для .xbm) и своих путей (копия). Двойник = armor__viper -> armor__<look>."""
    newdir = TWIN[look][0]
    cf = GAME / "mods" / mod / "content" / "texture.cache"
    if not cf.exists():                      # мод без текстур (напр. сапоги)
        return None, {}, [], []
    c = cache_parts(cf)
    rekey, over, own = {}, [], []
    for i in range(c["n"]):
        nm = cache_entry_name(c["strs"], c["ents"][i * 52:(i + 1) * 52])
        low = nm.lower()
        if low in van:                       # мод положил .xbm на ВАНИЛЬНЫЙ путь
            new = nm.replace("armor__viper", newdir, 1)
            assert len(new) == len(nm) and new.lower() not in van, ("рекей", nm, new)
            rekey[low] = new
            over.append(nm)
        else:
            own.append(nm)
    return c, rekey, over, own


def _swap_ci(buf, old_low, new):
    """Подмена пути-текстуры в меше. Пути в меше — латиница нижнего регистра,
    как в кэше; заменяем byte-в-byte (armor__viper -> двойник той же длины)."""
    o = old_low.encode("latin-1")
    n = new.lower().encode("latin-1")
    return buf.replace(o, n)


def build():
    head("ОБЛИКИ ЗМЕИ — сборка (Весемир: сапоги/перчатки/штаны + Perfect KM)")
    for k, (d, _tag) in TWIN.items():
        assert len(d) == len(VDIR), (k, d)
    if WORK.exists():
        shutil.rmtree(WORK)
    RAW.mkdir(parents=True)
    say("   читаю оглавления игры (ванильные пути)...")
    van = vanilla_paths()

    # текстуры каждого мода (рекей/копия) считаем ОДИН раз из его кэша
    mods = []
    for pc in PIECES:
        for _m, mod in pc["meshes"]:
            if mod not in mods:
                mods.append(mod)
    mod_cache, mod_rekey, mod_over, mod_own = {}, {}, {}, {}
    for mod in mods:
        c, rekey, over, own = mod_textures(mod, MOD_LOOK[mod], van)
        mod_cache[mod], mod_rekey[mod], mod_over[mod], mod_own[mod] = c, rekey, over, own
        say("   %-32s замен(рекей) %d, своих %d" % (mod, len(over), len(own)))

    cards_xml, donors = [], []
    mesh_root = RAW / "characters" / "models" / "geralt" / "armor"

    for pc in PIECES:
        newdir, tag = TWIN[pc["look"]]
        say("\n   • %s" % pc["name"])
        card_path = ("items\\bodyparts\\geralt_items\\%s\\witcher_viper\\%s.w2ent"
                     % (CARD_SUB[pc["cat"]], pc["card"]))
        layer_path = _p(VDIR, pc["layer"] + ".w2ent")
        b_card = V.find_bundle_with(GAME / "content", card_path)
        b_lay = V.find_bundle_with(GAME / "content", layer_path)
        assert b_card and b_lay, ("нет слоёв", pc["card"], b_card, b_lay)
        A = grab(b_card, card_path)
        C = grab(b_lay, layer_path)
        # слой мешей: путь каждого модового меша dir viper->twin
        for mesh, _mod in pc["meshes"]:
            old = _p(VDIR, mesh + ".w2mesh").encode("latin-1")
            new = _p(newdir, mesh + ".w2mesh").encode("latin-1")
            assert C.count(old) >= 1, ("меш не в слое", mesh)
            C = C.replace(old, new)
        # карточка красок: ссылка на слой мешей (полный путь -> двойник, dir)
        oldL = layer_path.encode("latin-1")
        newL = _p(newdir, pc["layer"] + ".w2ent").encode("latin-1")
        assert A.count(oldL) == 1, ("ссылка на слой мешей", A.count(oldL))
        A = A.replace(oldL, newL)
        # модовые меши + буферы; в меше подменить ссылки на текстуры-замены
        put = {}
        for mesh, mod in pc["meshes"]:
            mroot = GAME / "mods" / mod / "content"
            data = grab(mroot / "blob0.bundle", _p(VDIR, mesh + ".w2mesh"))
            buf = grab(mroot / "buffers0.bundle", _p(VDIR, mesh + ".w2mesh") + ".1.buffer")
            for low, new in mod_rekey[mod].items():
                data = _swap_ci(data, low, new)
            put[_p(newdir, mesh + ".w2mesh")] = data
            put[_p(newdir, mesh + ".w2mesh") + ".1.buffer"] = buf
        # разложить слои и меши под двойник
        d = mesh_root / newdir
        d.mkdir(parents=True, exist_ok=True)
        (d / (pc["layer"] + ".w2ent")).write_bytes(C)
        for path, data in put.items():
            fp = RAW / Path(path.replace("\\", "/"))
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(data)
        # карточка-предмет: equip_template = слой-карточка с ТЕГОМ облика
        equip_tpl = pc["card"].replace("viper", tag)
        src = find_card(pc["card"])
        icon = "icons/inventory/quests/ico_recipe.png"
        if src:
            m = re.search(r'icon_path\s*=\s*"([^"]*)"', src)
            if m:
                icon = m.group(1)
        lockey = "frgz_" + tag + "_" + pc["cat"]
        desc = {"armor": "item_category_medium_armor_description",
                "gloves": "item_category_gloves_description",
                "pants": "item_category_pants_description",
                "boots": "item_category_boots_description"}[pc["cat"]]
        cards_xml.append(make_item(pc["name"], equip_tpl, pc["cat"], icon, lockey, desc))
        donors.append(dict(name=pc["name"], cat=pc["cat"], icon=icon, lockey=lockey,
                           quality=4, tags_effects=[]))
        base = RAW / "dlc" / MOUNT / "data" / "items"
        base.mkdir(parents=True, exist_ok=True)
        (base / (equip_tpl + ".w2ent")).write_bytes(A)
        say("     [ok] слои и меши разложены")

    # текстуры: по каждому моду один раз (рекей .xbm на двойник + свои)
    cache_sources = []
    for mod in mods:
        mroot = GAME / "mods" / mod / "content"
        newdir = TWIN[MOD_LOOK[mod]][0]
        n_re = n_own = 0
        for nm in mod_over[mod]:
            xbm = grab(mroot / "blob0.bundle", nm)
            new = nm.replace("armor__viper", newdir, 1)
            xbm, ok = xbm_setkey(xbm, h31(new))
            assert ok, ("нет textureCacheKey", nm)
            fp = RAW / Path(new.replace("\\", "/"))
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(xbm)
            n_re += 1
        for nm in mod_own[mod]:
            try:
                xbm = grab(mroot / "blob0.bundle", nm)
            except SystemExit:
                continue                     # запись кэша есть, заголовка в blob нет
            fp = RAW / Path(nm.replace("\\", "/"))
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(xbm)
            n_own += 1
        if mod_cache[mod] is not None:
            cache_sources.append((mod_cache[mod], mod_rekey[mod]))
        say("   %-32s .xbm: рекей %d, свои %d" % (mod, n_re, n_own))

    # паспорт DLC + xml
    base = RAW / "dlc" / MOUNT
    for branch in ("items", "items_plus"):
        d = base / "data" / "gameplay" / branch
        d.mkdir(parents=True, exist_ok=True)
        (d / ITEMS).write_bytes(items_xml(cards_xml).encode("utf-16"))
        (d / SHOP).write_bytes(EMPTY_XML.encode("utf-16"))
        (d / EXTS).write_bytes(EMPTY_XML.encode("utf-16"))
    (base / (MOUNT + ".reddlc")).write_bytes(
        passport.build(mount=MOUNT, name_key=DLC_ID, desc_key=DLC_ID + "_desc",
                       items_xml=ITEMS, shop_xml=SHOP, exts_xml=EXTS,
                       templates_dir="data/items/"))
    (RAW / "strings.list").write_bytes(b'{\n    "files": []\n}')
    say("\n   [ok] сырьё: %d файлов, предметов %d"
        % (sum(1 for _ in RAW.rglob("*") if _.is_file()), len(cards_xml)))

    # упаковка
    import subprocess
    OUT.mkdir(parents=True)
    wcc, cwd = V.wcc_pair()
    r = subprocess.run([str(wcc), "pack", "-dir=" + str(RAW), "-outdir=" + str(OUT)],
                       capture_output=True, text=True, timeout=900, cwd=str(cwd))
    if not (OUT / "blob0.bundle").exists():
        say("   [!!] pack не собрал (код %d)" % r.returncode)
        for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-12:]:
            say("      " + line.strip()[:120])
        sys.exit(1)
    subprocess.run([str(wcc), "metadatastore", "-path=" + str(OUT)],
                   capture_output=True, text=True, timeout=900, cwd=str(cwd))

    # texture.cache: слить кэши источников (pack .cache из сырья выбросил)
    cache = merge_caches(cache_sources)
    (OUT / "texture.cache").write_bytes(cache)
    m = cache_parts(OUT / "texture.cache")
    say("   [ok] texture.cache слит: %d Б, записей %d" % (len(cache), m["n"]))

    verify(donors, van)
    (Path(__file__).parent / "zmeya_donors.json").write_text(
        json.dumps(donors, ensure_ascii=False, indent=1), encoding="utf-8")
    head("СОБРАНО")
    say("   Готово в: %s" % OUT)
    say("   Жетонов: %d — %s" % (len(donors), ", ".join(x["name"] for x in donors)))
    say("   Перенос (ТОЛЬКО при закрытой игре): python build_zmeya.py --install")


def verify(donors, van):
    say()
    say("   ПРОВЕРКА:")
    idx = [str(getattr(e, "name", "")).replace("/", "\\")
           for e in B.read_index(OUT / "blob0.bundle")]
    # strings.list — служебный манифест бандла (есть в КАЖДОМ бандле игры), не
    # ассет; его совпадение с ванилью не является перекрытием.
    over = [n for n in idx if n.lower() in van and not n.lower().endswith("strings.list")]
    say("      перекрытых ванильных путей в бандле: %d (должно быть 0)" % len(over))
    for n in over[:8]:
        say("        " + n)
    assert not over, "ВАНИЛЬ ПЕРЕКРЫТА бандлом"
    m = cache_parts(OUT / "texture.cache")
    covan = [cache_entry_name(m["strs"], m["ents"][i * 52:(i + 1) * 52])
             for i in range(m["n"])
             if cache_entry_name(m["strs"], m["ents"][i * 52:(i + 1) * 52]).lower() in van]
    say("      записей кэша на ванильном пути: %d (должно быть 0)" % len(covan))
    for n in covan[:8]:
        say("        " + n)
    assert not covan, "КЭШ ПЕРЕКРЫВАЕТ ВАНИЛЬНУЮ ТЕКСТУРУ"
    xbms = [e for e in B.read_index(OUT / "blob0.bundle")
            if str(e.name).lower().endswith(".xbm")]
    bad = 0
    for e in xbms:
        n = str(e.name).replace("/", "\\")
        if xbm_key(B.extract(OUT / "blob0.bundle", e)) != h31(n):
            bad += 1
            say("        ключ .xbm != h31: %s" % n)
    say("      .xbm с верным ключом: %d/%d" % (len(xbms) - bad, len(xbms)))
    assert bad == 0, "у .xbm неверный ключ кэша"
    say("      записей в бандле: %d, жетонов: %d" % (len(idx), len(donors)))


def disable_replacers():
    """Обратимо гасит 6 модов-замен: mod... -> ~mod... (игра пропускает «~»)."""
    done = []
    for mod in REPLACERS:
        src = GAME / "mods" / mod
        dst = GAME / "mods" / ("~" + mod)
        if dst.exists():
            done.append("~" + mod + " (уже)")
            continue
        if src.exists():
            src.rename(dst)
            done.append("~" + mod)
    return done


def install():
    head("ПЕРЕНОС ЗМЕИ В ИГРУ")
    if V.game_running():
        say("   [!!] игра запущена — закрой её и повтори")
        sys.exit(1)
    if not (OUT / "blob0.bundle").exists() or not (OUT / "texture.cache").exists():
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
    say("\n   Гашу моды-замены Змеи (обратимо, префикс «~»):")
    for dmod in disable_replacers():
        say("      " + dmod)
    say("\n   [ok] ванильная Змея вернётся; облики — жетонами.")
    say("   Дальше: интеграция в build_blanks + пересборка.")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        if V.game_running():
            say("   [i] игра запущена — собираю в TEMP, папку игры не трогаю")
        build()
