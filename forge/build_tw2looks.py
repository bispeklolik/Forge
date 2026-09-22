# -*- coding: utf-8 -*-
u"""ОБЛИКИ TW2 GEAR — отдельными предметами-донорами в своём DLC (dlcFRGTW2).

Заказ ГД 18.09: «Добавить облики из мода как DLC, только как жетоны обликов и
все. Оригинальные файлы не трогать вообще.»

TW2 Gear написан как ЗАМЕНА: кладёт свои меши поверх ванильных путей обычной
брони (armor_human__common, legs/shoes/gloves_human__common, armor__cat,
casual_nilfgaardian_suit, dlc1 armor__temerian). Здесь — обратное: каждый его
облик становится НОВЫМ шаблоном по пути-двойнику, ваниль не перекрывается ни
одним файлом. Приём — тот же, что в forge\\build_vesemir.py:

    карточный слой .w2ent (его basename = equip_template)   -> копия с подменой
    [мешевый слой _meshes.w2ent — только у Кота]             -> копия с подменой
    меши .w2mesh мода (+ парный .1.buffer)                   -> байт-в-байт по пути-двойнику
    подмена путей — ТОЛЬКО полной строкой и ТОЙ ЖЕ ДЛИНЫ (смещения не едут, CRC не трогаем)

Вход — таблица разведки tw2_looks.json (54 облика). Что из неё берётся:
  * 49 обликов kind=mesh. 5 перекрасок (kind=retexture) НЕ собираются: разведка
    текстур выбрала способ (а) — из texture.cache мода вырезаются 3 записи с
    ванильными ключами, а без них перекраска = ванильный вид (дубль жетона).
  * 3 «альтернативные» перчатки g_01_* (alt) — это НЕ отдельные облики: в
    ванильной карточке тех же перчаток они стоят вариантом category="armor"
    («жирная» версия, когда надет доспех). Они собираются шаблонами и вешаются
    вариантом на донора g_01a — отдельных доноров для них нет. Итого доноров 46.
  * Варианты карточки-примера переносятся ВСЕ, что имеют двойника (включая
    <variant> со списком <item> — «при надетой вещи X»); вариант без двойника
    (его меши мод не менял) снимается — облик TW2 виден всегда. Всё снятое
    печатается.

Текстуры (способ (а) разведки): свои .xbm мода (w2*tex, 81 шт.) кладутся по
СВОИМ путям; texture.cache мода кладётся без записей, чьи ключи уже есть в
любом кэше игры (ожидаются ровно 3 — текстуры мода по ванильным путям).

Подписи: у каждого донора свой ключ frgtw2_<шаблон>, текст = ванильное имя
вещи-примера + « (TW2)» — иначе жетон TW2 неотличим от ванильного жетона того
же предмета. id-space 4486 (проверяется на свободу при каждой сборке).

Режимы:
    python build_tw2looks.py            сухая сборка: всё в <скретчпад>\\tw2out,
                                        в папку игры НЕ пишется ни байта
    python build_tw2looks.py --install  перенос в игру (только при закрытой игре)
                                        + DlcEnabled_frg_tw2 в user.settings/dx12user.settings

На выходе — <скретчпад>\\tw2_donors.json: записи в формате donors_armor.json для
жетонов Элихаля.
"""
import io, json, os, re, shutil, struct, subprocess, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
sys.path.insert(0, r"D:\Apps\w3ee-tweaks\setbonus")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from medallion import bundles as B
import passport

# ---- пути ---------------------------------------------------------------------
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
DOCS = Path(os.environ["USERPROFILE"]) / "Documents" / "The Witcher 3"
# Исходники живут В ПРОЕКТЕ (forge/tw2): таблица обликов, распакованный
# мод и список доноров. Раньше всё лежало во временной папке сессии и
# пропало бы вместе с ней.
SCRATCH = Path(os.environ.get(
    "TW2_SCRATCH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tw2")))
# wcc_lite: зеркало вне папки игры, если задано (он пишет wcc.log рядом
# с собой), иначе — тот же, что у build_blanks.py
_MIRROR = Path(os.environ.get("TW2_WCC_MIRROR", "-"))
WCC = (_MIRROR if _MIRROR.is_file() else
       GAME / "mods" / "Tools" / "wcc_lite" / "bin" / "x64" / "wcc_lite.exe")
ENC = Path(r"D:\Apps\w3ee-tweaks\tools\w3strings\w3strings.exe")

LOOKS_JSON = SCRATCH / "tw2_looks.json"
MOD = SCRATCH / "tw2gear" / "modTW2Gear" / "content"
MODI = SCRATCH / "tw2gear" / "modTW2Gear_Icons" / "content"
# сборка — во временную папку системы, как у build_vesemir.py
WORK = Path(os.environ["TEMP"]) / "frgtw2"
RAW = WORK / "raw"
OUT = WORK / "content"
STRW = WORK / "strings"
DONORS_JSON = SCRATCH / "tw2_donors.json"

DLC = GAME / "dlc" / "dlcFRGTW2"
MOUNT = "frgtw2"
DLC_ID = "frg_tw2"
ITEMS = "frgtw2_items.xml"
SHOP = "frgtw2_shop.xml"
EXTS = "frgtw2_item_extensions.xml"
KEY_PREFIX = "frgtw2_"

# 4480-4482 — dlcFRGBlanks, 4490 — modW3EERedux_DynRagdolls (скан 18.09);
# 4483-4485 оставлены болванкам на рост
IDSPACE = 4486
LOCALES = ["ar", "br", "cn", "cz", "de", "en", "es", "esmx",
           "fr", "hu", "it", "jp", "kr", "pl", "ru", "tr", "zh"]
META_LANG = {"cn": "zh"}

EXPECT = dict(looks=54, mod_meshes=91, mod_meshes_over_vanilla=89,
              mod_xbm_over_vanilla=3, mod_xbm_own=81)
WEIGHT_TAGS = ("LightArmor", "MediumArmor", "HeavyArmor")

EMPTY_XML = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
             '\t\t<items>\r\n\t\t</items>\r\n\t</definitions>\r\n</redxml>\r\n')

INSTALL = "--install" in sys.argv


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 72); say("  " + s); say("=" * 72)


def norm(p):
    return str(p).replace("/", "\\").lower()


def base(p):
    return norm(p).rsplit("\\", 1)[-1].rsplit(".", 1)[0]


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        # не смогли спросить — считаем, что игра ЗАПУЩЕНА: лучше отказать,
        # чем писать в папку работающей игры
        return True


# ---- запись: в сухом режиме в папку игры нельзя НИЧЕГО -------------------------
def guard(p):
    p = Path(p).resolve()
    if not INSTALL:
        g = str(GAME.resolve()).lower().rstrip("\\") + "\\"
        if str(p).lower().startswith(g):
            raise SystemExit("[!!] сухой режим пытается писать в папку игры: %s" % p)
    return p


def wbytes(p, data):
    p = guard(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


# ---- бандлы -------------------------------------------------------------------
def game_index():
    """lower-путь -> [(корень, бандл, запись)] по content, dlc, mods.
    Собственное установленное дополнение (dlcFRGTW2) не считается — иначе
    пересборка «столкнулась» бы сама с собой."""
    idx = {}
    nb = 0
    for r in ("content", "dlc", "mods"):
        for f in sorted((GAME / r).rglob("*.bundle")):
            if "Tools" in f.parts or "WitcherScriptMerger" in str(f):
                continue
            if r == "dlc" and f.relative_to(GAME / "dlc").parts[0].lower() == DLC.name.lower():
                continue
            try:
                ents = B.read_index(f)
            except Exception:
                continue
            nb += 1
            for e in ents:
                idx.setdefault(norm(e.name), []).append((r, f, e))
    return idx, nb


def bundle_map(bundle):
    return {norm(e.name): e for e in B.read_index(bundle)}


def ext(bundle, e, what):
    if not B.can_extract(e):
        raise SystemExit("[!!] не распаковывается: %s (%s)" % (what, bundle))
    data = B.extract(bundle, e)
    if not data:
        raise SystemExit("[!!] пусто: %s (%s)" % (what, bundle))
    if getattr(e, "size", 0) and len(data) != e.size:
        raise SystemExit("[!!] %s: размер %d, в оглавлении %d" % (what, len(data), e.size))
    return data


def dec(b):
    for enc in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            t = b.decode(enc)
            if "<" in t[:400]:
                return t
        except Exception:
            pass
    return None


# ---- подмена путей ------------------------------------------------------------
def swap(buf, old, new, tag, count):
    """Замена РАВНОЙ ДЛИНЫ, полной строкой пути: ни одно смещение не едет."""
    o, n = old.encode("latin-1"), new.encode("latin-1")
    assert len(o) == len(n), (tag, "разная длина", old, new)
    got = buf.count(o)
    assert got == count, (tag, old, "вхождений %d, ждали %d" % (got, count))
    return buf.replace(o, n)


PATH_RE = re.compile(rb"(?:characters|dlc|items|environment|fx|engine|gameplay|"
                     rb"animations|levels|qa)\\[\w\\.\- ]+", re.I)
REF_EXT = {"w2mesh", "w2ent", "xbm", "w3dyng", "w2mi", "w2mg", "redcloth", "w2fur",
           "w2phase", "w2rig", "w2ragdoll", "w2anims", "w2beh", "w2behtree", "w2p",
           "w2animev", "w2je", "w3app", "w2cloth", "csv", "xml", "w2mat"}


def refs(data):
    """Все depot-пути внутри файла (импорты И flatCompiledData — побайтово)."""
    out = set()
    for m in PATH_RE.finditer(data):
        s = m.group(0).decode("latin-1").rstrip(" .").lower()
        last = s.rsplit("\\", 1)[-1]
        if "." in last and last.rsplit(".", 1)[-1] in REF_EXT:
            out.add(s)
    return out


# ---- texture.cache (TXCH v6) ----------------------------------------------------
# [страницы по 4096] [mip-таблица nmip*4] [строки ssz] [записи n*52] [подвал 32]
# подвал: u64 crc, u32 usedPages, u32 n, u32 ssz, u32 nmip, 'HCXT', u32 6
# crc = FNV-1a 64 над [mip + строки + записи]; ключ записи = textureCacheKey .xbm
def fnv64(b, h=0xcbf29ce484222325):
    for x in b:
        h = ((h ^ x) * 0x100000001b3) & 0xffffffffffffffff
    return h


def cache_tables(path, strict=True):
    with open(path, "rb") as f:
        f.seek(0, 2)
        L = f.tell()
        if L < 32 and not strict:
            return None
        f.seek(L - 32)
        crc, pages, n, ssz, nmip, magic, ver = struct.unpack("<QIIIIII", f.read(32))
        if not strict and not (magic == 0x54584348 and ver == 6):
            return None
        assert magic == 0x54584348 and ver == 6, (path, hex(magic), ver)
        tsz = nmip * 4 + ssz + n * 52
        tried = []
        for start in (pages * 4096, L - 32 - tsz):
            f.seek(start)
            T = f.read(tsz)
            ok = fnv64(T) == crc
            tried.append(ok)
            if ok:
                break
        if strict:
            assert ok, "crc кэша не сошёлся: %s" % path
    keys = [struct.unpack_from("<I", T, nmip * 4 + ssz + i * 52)[0] for i in range(n)]
    return dict(crc=crc, pages=pages, n=n, ssz=ssz, nmip=nmip, T=T, keys=keys, ok=ok)


def xbm_key(d):
    """textureCacheKey кукнутой CBitmapTexture (.xbm)."""
    tabs = [struct.unpack_from("<III", d, 0x28 + i * 12) for i in range(10)]
    soff, ssize, _ = tabs[0]
    blob = d[soff:soff + ssize]

    def s_at(o):
        z = blob.find(b"\0", o)
        return blob[o:z].decode("latin-1")
    names = [s_at(struct.unpack_from("<II", d, tabs[1][0] + i * 8)[0]) for i in range(tabs[1][1])]
    coff, ccnt, _ = tabs[4]
    for i in range(ccnt):
        _cn, _obf, _par, dsz, doff, _t, _c = struct.unpack_from("<HHIIIII", d, coff + i * 24)
        off, end = doff + 1, doff + dsz
        while off + 2 <= end:
            ni = struct.unpack_from("<H", d, off)[0]
            if ni == 0:
                break
            _ti, sz = struct.unpack_from("<HI", d, off + 2)
            if names[ni] == "textureCacheKey" and sz == 8:
                return struct.unpack_from("<I", d, off + 8)[0]
            off += 4 + sz
    return None


def strip_cache(src, dst, drop):
    """Режется ТОЛЬКО массив записей: страницы, mip-таблица и строки остаются
    (индексы у оставшихся записей не сдвигаются), пересчитываются n и crc."""
    c = cache_tables(src)
    h = c["nmip"] * 4 + c["ssz"]
    ents = c["T"][h:]
    keep = [ents[i * 52:(i + 1) * 52] for i in range(c["n"]) if c["keys"][i] not in drop]
    newT = c["T"][:h] + b"".join(keep)
    foot = struct.pack("<QIIIIII", fnv64(newT), c["pages"], len(keep), c["ssz"], c["nmip"],
                       0x54584348, 6)
    dst = guard(dst)
    with open(src, "rb") as f, open(dst, "wb") as o:
        left = c["pages"] * 4096
        while left:
            buf = f.read(min(left, 1 << 24))
            o.write(buf)
            left -= len(buf)
        o.write(newT)
        o.write(foot)
    return c["n"], len(keep)


# ---- карточки предметов -------------------------------------------------------
def cut_card(text, item_name):
    """Карточка ЦЕЛИКОМ, с учётом вложенных <item>Geralt Shirt</item> в <variant>.
    (Разведка резала тело на первом </item> и потеряла вторые варианты.)"""
    m = re.search(r'<item\b[^>]*?\bname\s*=\s*"%s"' % re.escape(item_name), text, re.S)
    if not m:
        return None
    s, depth = m.start(), 0
    for mm in re.finditer(r"<(/?)item\b([^>]*?)(/?)>", text[s:], re.S):
        if mm.group(1):
            depth -= 1
        elif mm.group(3):
            continue
        else:
            depth += 1
        if depth == 0:
            return text[s:s + mm.end()]
    return None


def card_parts(card):
    opening = card[:card.find(">") + 1]
    attrs = re.findall(r'(\w+)\s*=\s*"([^"]*)"', opening)
    tags = re.search(r"<tags>(.*?)</tags>", card, re.S)
    tags = [t.strip() for t in (tags.group(1) if tags else "").split(",") if t.strip()]
    coll = re.search(r"<collapse>.*?</collapse>", card, re.S)
    variants = []
    for a, body in re.findall(r"<variant\b([^>]*)>(.*?)</variant>", card, re.S):
        tp = re.search(r'equip_template\s*=\s*"([^"]*)"', a).group(1).strip()
        cat = re.search(r'category\s*=\s*"([^"]*)"', a)
        variants.append(dict(tpl=tp, cat=cat.group(1) if cat else None,
                             items=[i.strip() for i in re.findall(r"<item>(.*?)</item>", body)]))
    return attrs, tags, (coll.group(0) if coll else None), variants


def make_card(d):
    T = "\t"
    out = T * 2 + "<item\r\n"
    out += "".join(T * 3 + '%-32s="%s"\r\n' % (k, v) for k, v in d["attrs"])
    out += T * 2 + ">\r\n"
    out += T * 3 + "<tags>%s</tags>\r\n" % ", ".join(d["tags"])
    out += T * 3 + "<base_abilities></base_abilities>\r\n"
    if d["collapse"]:
        inner = re.search(r"<collapse>(.*)</collapse>", d["collapse"], re.S).group(1)
        els = re.findall(r"<[^>]+/>", inner)
        assert not re.sub(r"<[^>]+/>", "", inner).strip(), ("collapse: не только условия", inner)
        out += (T * 3 + "<collapse>\r\n" + "".join(T * 4 + e + "\r\n" for e in els)
                + T * 3 + "</collapse>\r\n")
    if d["variants"]:
        out += T * 3 + "<variants>\r\n"
        for v in d["variants"]:
            a = 'equip_template="%s"' % v["tpl"]
            if v["cat"] is not None:
                a += ' category="%s"' % v["cat"]
            if v["items"]:
                out += T * 4 + "<variant %s>\r\n" % a
                out += "".join(T * 5 + "<item>%s</item>\r\n" % i for i in v["items"])
                out += T * 4 + "</variant>\r\n"
            else:
                out += T * 4 + "<variant %s></variant>\r\n" % a
        out += T * 3 + "</variants>\r\n"
    out += T * 2 + "</item>\r\n"
    return out


def items_xml(cards):
    body = ('<?xml version="1.0" encoding="UTF-16"?>\r\n<redxml>\r\n\t<definitions>\r\n'
            "\t\t<items>\r\n" + "".join(cards) + "\t\t</items>\r\n"
            "\t</definitions>\r\n</redxml>\r\n")
    ET.fromstring(body.replace('<?xml version="1.0" encoding="UTF-16"?>', ""))
    return body


# ---- подписи ------------------------------------------------------------------
def h31(s):
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xffffffff
    return h


def decode_w3s(src, tag):
    """Копия .w3strings в рабочую папку и расшифровка там (рядом с игрой
    w3strings.exe положил бы .csv прямо в папку игры)."""
    dst = guard(STRW / "dec" / ("%s.w3strings" % tag))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    subprocess.run([str(ENC), "--decode", str(dst)], capture_output=True, cwd=str(dst.parent))
    csv = Path(str(dst) + ".csv")
    rows = []
    if csv.exists():
        for line in io.open(csv, encoding="utf-8", errors="replace").read().splitlines():
            p = line.split("|", 3)
            if len(p) == 4 and not line.startswith(";"):
                rows.append((p[0].strip(), p[1].strip(), p[3]))
    return rows


def vanilla_names(keys, loc):
    """Ключ -> текст по ванильным .w3strings: content0, затем официальные DLC."""
    want = {"%08x" % h31(k): k for k in keys}
    got = {}
    srcs = [GAME / "content" / "content0" / ("%s.w3strings" % loc)]
    srcs += sorted(p for p in (GAME / "dlc").glob("*/content/%s.w3strings" % loc)
                   if re.match(r"(dlc\d+|bob|ep1)$", p.parent.parent.name, re.I))
    for src in srcs:
        if len(got) == len(want):
            break
        if not src.exists():
            continue
        tag = "%s_%s" % (src.parent.parent.name if src.parent.name == "content"
                         else src.parent.name, loc)
        for _i, hx, text in decode_w3s(src, tag):
            k = want.get(hx.lower())
            if k and k not in got and text.strip():
                got[k] = text.strip()
    return got


def idspace_owners(space):
    """Кто в сборке уже занимает id-space (dlc и mods, en.w3strings)."""
    owners = set()
    for r in ("mods", "dlc"):
        for d in sorted((GAME / r).iterdir()):
            if not d.is_dir() or (r == "dlc" and d.name.lower() == DLC.name.lower()):
                continue
            src = d / "content" / "en.w3strings"
            if not src.exists():
                continue
            for i, _h, _t in decode_w3s(src, "ids_%s_%s" % (r, d.name)):
                if i.isdigit() and i.startswith("211%04d" % space):
                    owners.add("%s\\%s" % (r, d.name))
                    break
    return owners


# ============================================================================
def main():
    t0 = time.time()
    head("TW2 GEAR -> dlcFRGTW2 (сухая сборка, в игру ничего не пишется)")
    for p in (LOOKS_JSON, MOD / "blob0.bundle", MOD / "buffers0.bundle",
              MOD / "texture.cache", MODI / "blob0.bundle", WCC, ENC):
        if not p.exists():
            raise SystemExit("[!!] нет входного файла: %s" % p)
    if WORK.exists():
        shutil.rmtree(guard(WORK))
    RAW.mkdir(parents=True)
    STRW.mkdir(parents=True)

    J = json.load(io.open(LOOKS_JSON, encoding="utf-8"))
    LOOKS = J["looks"]
    assert len(LOOKS) == EXPECT["looks"], len(LOOKS)

    # ---- 1. оглавления -------------------------------------------------------
    say("   Читаю оглавления игры...")
    GI, nb = game_index()
    say("   [ok] бандлов %d, путей %d" % (nb, len(GI)))
    live_tpl = {n.rsplit("\\", 1)[-1][:-6] for n in GI if n.endswith(".w2ent")}
    mod_blob = bundle_map(MOD / "blob0.bundle")
    mod_buf = bundle_map(MOD / "buffers0.bundle")
    modi_blob = bundle_map(MODI / "blob0.bundle")
    MOD_VAN = {p for p in mod_blob if p in GI}          # мод поверх ванильных путей
    n_mesh = sum(1 for p in mod_blob if p.endswith(".w2mesh"))
    n_mesh_v = sum(1 for p in MOD_VAN if p.endswith(".w2mesh"))
    n_xbm_v = sum(1 for p in MOD_VAN if p.endswith(".xbm"))
    own_xbm = sorted(p for p in mod_blob if p.endswith(".xbm") and p not in GI)
    say("   [ok] мод: %d записей; меши %d (по ванильным путям %d), xbm своих %d, "
        "xbm по ванильным %d" % (len(mod_blob), n_mesh, n_mesh_v, len(own_xbm), n_xbm_v))
    assert n_mesh == EXPECT["mod_meshes"] and n_mesh_v == EXPECT["mod_meshes_over_vanilla"]
    assert len(own_xbm) == EXPECT["mod_xbm_own"] and n_xbm_v == EXPECT["mod_xbm_over_vanilla"]

    # ---- 2. отбор обликов ----------------------------------------------------
    sel = [L for L in LOOKS if L["kind"] == "mesh"]
    skipped = [L for L in LOOKS if L["kind"] != "mesh"]
    say("   [ok] обликов kind=mesh: %d; перекрасок снято: %d (%s)"
        % (len(sel), len(skipped), ", ".join(L["equip_template"] for L in skipped)))

    # карточки-примеры: ваниль (content, затем официальные dlc), не моды
    xml_cache = {}

    def example_card(ex):
        f = norm(ex["file"])
        want_src = ex["src"].split(":", 1)[1].lower()
        if f not in xml_cache:
            cands = [(r, b, e) for r, b, e in GI.get(f, []) if r in ("content", "dlc")]
            # content раньше dlc; среди равных — тот, что назвала разведка
            cands.sort(key=lambda x: (x[0] != "content",
                                      x[1].parent.parent.name.lower() != want_src, str(x[1])))
            if not cands:
                raise SystemExit("[!!] нет ванильного %s" % f)
            r, b, e = cands[0]
            t = dec(ext(b, e, f))
            xml_cache[f] = (re.sub(r"<!--.*?-->", "", t.replace("\r", ""), flags=re.S), b)
        t, b = xml_cache[f]
        c = cut_card(t, ex["name"])
        if not c:
            raise SystemExit("[!!] нет карточки %r в %s" % (ex["name"], f))
        return c, b

    EXC = {}
    for L in sel:
        EXC[L["equip_template"]] = example_card(L["example_item"])

    # «альтернативные» перчатки — вариант category=armor у основных
    var_of_main = {}
    for L in sel:
        if L["alt"]:
            continue
        for v in card_parts(EXC[L["equip_template"]][0])[3]:
            var_of_main.setdefault(v["tpl"].lower(), L["equip_template"])
    absorbed = {L["equip_template"]: var_of_main[base(L["card_layer"])]
                for L in sel if L["alt"] and base(L["card_layer"]) in var_of_main}
    donors_looks = [L for L in sel if L["equip_template"] not in absorbed]
    for L in sel:
        if L["alt"] and L["equip_template"] not in absorbed:
            raise SystemExit("[!!] alt-облик без хозяина: %s" % L["equip_template"])
    say("   [ok] alt-перчатки стали вариантом «при доспехе»: %d -> доноров %d"
        % (len(absorbed), len(donors_looks)))

    # ---- 3. шаблоны: карточные и мешевые слои -------------------------------
    RAWF = {}        # lower-путь -> (исходное написание, байты)

    def put(path, data, tag):
        k = norm(path)
        if k in RAWF:
            assert RAWF[k][1] == data, ("один путь — разные байты", path, tag)
            return
        RAWF[k] = (path, data)

    def read_layer(source, bundle_rel, path):
        path_l = norm(path)
        if source == "vanilla":
            bpath = (GAME / bundle_rel).resolve()
            hits = [(b, e) for r, b, e in GI.get(path_l, []) if b.resolve() == bpath]
            if not hits:
                raise SystemExit("[!!] %s нет в %s" % (path, bundle_rel))
            others = sorted({"%s:%s" % (r, b.parent.parent.name) for r, b, e in GI[path_l]
                             if b.resolve() != bpath})
            if others:
                say("      [i] %s есть ещё в: %s — берём ваниль" % (base(path), ", ".join(others)))
            return ext(hits[0][0], hits[0][1], path)
        if source == "modTW2Gear_Icons":
            e = modi_blob.get(path_l)
            if not e:
                raise SystemExit("[!!] %s нет в modTW2Gear_Icons" % path)
            return ext(MODI / "blob0.bundle", e, path)
        raise SystemExit("[!!] неизвестный источник слоя: %s" % source)

    TPLMAP = {}      # ванильный шаблон -> шаблон-двойник
    n_swaps = 0

    def build_template(spec, tag):
        nonlocal n_swaps
        tpl_old = base(spec["card_layer"])
        card = read_layer(spec["card_source"], spec["card_src_bundle"], spec["card_layer"])
        n0 = len(card)
        for old, new, cnt in spec["swaps"]["card"]:
            card = swap(card, old, new, "%s/card" % tag, cnt)
            n_swaps += 1
        assert len(card) == n0, (tag, "карточный слой: размер поехал")
        if spec.get("dyes"):
            assert card.count(b"componentName") >= 1, (tag, "краски потеряны")
        dst = spec["card_twin"].replace("<mount>", MOUNT)
        assert base(dst) == spec["equip_template"].lower(), (tag, dst)
        assert norm(dst).startswith("dlc\\%s\\data\\items\\" % MOUNT), dst
        assert len(dst.rsplit("\\", 1)[-1]) == len(spec["card_layer"].rsplit("\\", 1)[-1]), dst
        put(dst, card, tag)
        # мешевых слоёв бывает и два (Кот 3-4: карточка тянет слои lvl1 и lvl2)
        mls, mts = spec.get("mesh_layer"), spec.get("mesh_twin")
        if isinstance(mls, str):
            mls, mts = [mls], [mts]
        for ml, mt in zip(mls or [], mts or []):
            mesh = read_layer("vanilla", spec["mesh_layer_src_bundle"][ml], ml)
            n0 = len(mesh)
            for old, new, cnt in spec["swaps"][ml]:
                mesh = swap(mesh, old, new, "%s/meshes" % tag, cnt)
                n_swaps += 1
            assert len(mesh) == n0, (tag, "мешевый слой: размер поехал")
            assert len(mt) == len(ml), (tag, "мешевый слой: длина пути")
            assert any(new == mt for _o, new, _c in spec["swaps"]["card"]), (tag, "карточка не ведёт на", mt)
            put(mt, mesh, tag)
        assert tpl_old not in TPLMAP or TPLMAP[tpl_old] == spec["equip_template"]
        TPLMAP[tpl_old] = spec["equip_template"]

    say("   Собираю шаблоны...")
    for L in sel:
        build_template(L, L["equip_template"])
        if L.get("variant"):
            v = dict(L["variant"])
            build_template(v, v["equip_template"])
    n_tpl = sum(1 for k in RAWF if k.startswith("dlc\\%s\\data\\items\\" % MOUNT))
    n_ml = sum(1 for k in RAWF if k.endswith("_meshes.w2ent"))
    say("   [ok] шаблонов-двойников %d (+ мешевых слоёв %d), подмен %d — все равной длины"
        % (n_tpl, n_ml, n_swaps))
    clash = sorted(t for t in TPLMAP.values() if t.lower() in live_tpl)
    assert not clash, ("equip_template уже занят в сборке", clash)

    # ---- 4. меши мода + буферы --------------------------------------------
    mesh_src = {}
    for L in sel:
        for f in L["files"]:
            m = re.match(r"modTW2Gear (blob0|buffers0): (.+)$", f["src"])
            assert m, ("неожиданный источник", L["equip_template"], f["src"])
            item = (m.group(1), norm(m.group(2)), f["dst"])
            prev = mesh_src.setdefault(norm(f["dst"]), item)
            assert prev[:2] == item[:2], ("в один путь — разные исходники", f["dst"])
    n_mesh_put = n_buf_put = 0
    for k, (bnd, src, dst) in sorted(mesh_src.items()):
        if bnd == "blob0":
            data = ext(MOD / "blob0.bundle", mod_blob[src], src)
            put(dst, data, "mesh")
            n_mesh_put += 1
            # страховка: все буферы меша, не только .1
            extra = [p for p in mod_buf if p.startswith(src + ".") and p != src + ".1.buffer"]
            for p in extra:
                put(dst + p[len(src):], ext(MOD / "buffers0.bundle", mod_buf[p], p), "buf+")
                n_buf_put += 1
                say("      [i] доп. буфер %s" % p)
        else:
            put(dst, ext(MOD / "buffers0.bundle", mod_buf[src], src), "buf")
            n_buf_put += 1
    meshes = [k for k in RAWF if k.endswith(".w2mesh")]
    for k in meshes:
        assert k + ".1.buffer" in RAWF, ("нет буфера", k)
    say("   [ok] меши мода: %d, буферов: %d" % (n_mesh_put, n_buf_put))
    assert n_mesh_put == EXPECT["mod_meshes"], ("не все меши мода разложены", n_mesh_put)

    # ---- 5. текстуры: свои пути, свои ключи ---------------------------------
    own_keys = {}
    for p in own_xbm:
        data = ext(MOD / "blob0.bundle", mod_blob[p], p)
        k = xbm_key(data)
        assert k is not None and k == h31(p), ("ключ xbm не равен h31(пути)", p)
        own_keys[k] = p
        put(p, data, "xbm")
    van_keys_mod = {}
    for p in sorted(MOD_VAN):
        if p.endswith(".xbm"):
            van_keys_mod[xbm_key(ext(MOD / "blob0.bundle", mod_blob[p], p))] = p
    say("   [ok] свои текстуры мода: %d .xbm по родным путям (ключ = h31(путь))" % len(own_keys))

    say("   Кэш текстур: сверяю ключи со всеми texture.cache сборки...")
    game_keys = {}
    ncache = 0
    for c in sorted(GAME.rglob("texture.cache")):
        if "Tools" in c.parts or DLC.name.lower() in [x.lower() for x in c.parts]:
            continue
        info = cache_tables(c, strict=False)
        if info is None:
            say("      [i] не кэш TXCH v6 (пустой?) — пропущен: %s" % c.relative_to(GAME))
            continue
        if not info["ok"]:
            say("      [i] crc не сошёлся (ключи всё равно взяты): %s" % c.relative_to(GAME))
        ncache += 1
        for k in info["keys"]:
            game_keys.setdefault(k, str(c.relative_to(GAME)))
    mc = cache_tables(MOD / "texture.cache")
    drop = {k for k in mc["keys"] if k in game_keys}
    say("   [ok] кэшей в сборке %d; у мода записей %d, совпали с игрой: %d"
        % (ncache, mc["n"], len(drop)))
    for k in sorted(drop):
        say("      вырезаю 0x%08x  %s  (есть в %s)"
            % (k, van_keys_mod.get(k, "?"), game_keys[k]))
    assert drop == set(van_keys_mod), ("вырезаемое не совпало с текстурами по ванильным путям",
                                       sorted(map(hex, drop)), sorted(map(hex, van_keys_mod)))
    assert set(mc["keys"]) - drop == set(own_keys), "записи кэша != свои .xbm"

    # ---- 6. карточки предметов + подписи -------------------------------------
    say("   Карточки предметов...")
    names_ru = vanilla_names({L["example_item"]["localisation_key_name"] for L in donors_looks}, "ru")
    names_en = vanilla_names({L["example_item"]["localisation_key_name"] for L in donors_looks}, "en")
    cards, donors, strings, notes, table = [], [], [], [], []
    seen_names, seen_text = set(), {}
    for L in donors_looks:
        tpl = L["equip_template"]
        ex = L["example_item"]
        card, _b = EXC[tpl]
        attrs, tags, coll, variants = card_parts(card)
        # имя: "TW2 <вещь-пример>", латиницей
        nm = re.sub(r"^DLC\d+\s+", "", ex["name"]).replace("_crafted", "").strip()
        nm = "TW2 " + re.sub(r"\s+", " ", nm)
        assert nm not in seen_names, ("имя донора повторилось", nm)
        seen_names.add(nm)
        key = KEY_PREFIX + tpl
        new_attrs = []
        for k, v in attrs:
            if k == "name":
                v = nm
            elif k == "equip_template":
                assert TPLMAP.get(v.strip().lower()) == tpl, (tpl, v)
                v = tpl
            elif k == "localisation_key_name":
                v = key
            new_attrs.append((k, v))
        attr_d = dict(new_attrs)
        assert attr_d.get("icon_path") == ex["icon_path"], (tpl, "иконка")
        weight = [t for t in tags if t in WEIGHT_TAGS]
        new_tags = ["Armor"] + weight[:1] + ["mod_armor", "NoShow"]
        new_vars = []
        for v in variants:
            tw = TPLMAP.get(v["tpl"].lower())
            if tw:
                new_vars.append(dict(v, tpl=tw))
            else:
                notes.append("%s: снят вариант %s (%s) — мод его не менял, облик TW2 виден всегда"
                             % (nm, v["tpl"], ("category=%s" % v["cat"]) if v["cat"] is not None
                                else "при " + "/".join(v["items"])))
        cards.append(make_card(dict(attrs=new_attrs, tags=new_tags, collapse=coll,
                                    variants=new_vars)))
        ru = names_ru.get(ex["localisation_key_name"]) or ex["name"]
        en = names_en.get(ex["localisation_key_name"]) or ex["name"]
        n_same = seen_text.get(ru, 0) + 1
        seen_text[ru] = n_same
        suf = " (TW2)" if n_same == 1 else " (TW2, %s)" % ["", "", "II", "III", "IV"][n_same]
        strings.append((key, ru + suf, en + suf))
        donors.append(dict(name=nm, cat=ex["category"], icon=ex["icon_path"], lockey=key,
                           quality=5 if "mod_legendary" in tags else 4, tags_effects=[]))
        table.append((nm, ex["category"], tpl, [v["tpl"] for v in new_vars], ru + suf))
    xml_text = items_xml(cards)
    say("   [ok] карточек-доноров: %d" % len(cards))

    # подписи: id-space свободен?
    owners = idspace_owners(IDSPACE)
    assert not owners, ("id-space %d занят: %s" % (IDSPACE, ", ".join(sorted(owners))))
    base_id = int("211%04d000" % IDSPACE)
    assert len(strings) < 1000
    n_loc = 0
    for loc in LOCALES:
        rows = [";meta[language=%s]" % META_LANG.get(loc, loc), "; id      |key(hex)|key(str)| text"]
        for i, (k, ru, en) in enumerate(strings):
            rows.append("%d|        |%s|%s" % (base_id + i, k, ru if loc == "ru" else en))
        csv = guard(STRW / ("frgtw2_%s.csv" % loc))
        csv.write_bytes(("\r\n".join(rows) + "\r\n").encode("utf-8"))
        subprocess.run([str(ENC), "--encode", str(csv), "--id-space", str(IDSPACE)],
                       capture_output=True, cwd=str(STRW))
        if Path(str(csv) + ".w3strings").exists():
            n_loc += 1
    assert n_loc == len(LOCALES), "подписи собрались не для всех локалей: %d" % n_loc
    # проверка: ru расшифровывается обратно в наши строки
    back = {hx: t for _i, hx, t in decode_w3s(Path(str(STRW / "frgtw2_ru.csv") + ".w3strings"),
                                               "check_ru")}
    for k, ru, _en in strings:
        assert back.get("%08x" % h31(k)) == ru, ("подпись не читается обратно", k)
    say("   [ok] подписи: %d ключей x %d локалей, id-space %d свободен"
        % (len(strings), n_loc, IDSPACE))

    # ---- 7. раскладка сырья ---------------------------------------------------
    for k, (p, data) in RAWF.items():
        wbytes(RAW / p, data)
    dd = RAW / "dlc" / MOUNT
    for branch in ("items", "items_plus"):
        g = dd / "data" / "gameplay" / branch
        wbytes(g / ITEMS, xml_text.encode("utf-16"))
        wbytes(g / SHOP, EMPTY_XML.encode("utf-16"))
        wbytes(g / EXTS, EMPTY_XML.encode("utf-16"))
    wbytes(dd / (MOUNT + ".reddlc"),
           passport.build(mount=MOUNT, name_key=DLC_ID, desc_key=DLC_ID + "_desc",
                          items_xml=ITEMS, shop_xml=SHOP, exts_xml=EXTS,
                          templates_dir="data/items/"))
    # strings.list (как у Весемира) НЕ кладём: pack без него работает (Ворон,
    # Бродяга живут без него), а корневой strings.list есть у шести чужих
    # дополнений — это было бы единственное перекрытие чужого пути
    raw_files = [p for p in RAW.rglob("*") if p.is_file()]
    say("   [ok] сырьё: %d файлов, %.1f МБ"
        % (len(raw_files), sum(p.stat().st_size for p in raw_files) / 1048576.0))

    # ---- 8. проверки ДО упаковки ----------------------------------------------
    head("ПРОВЕРКА СЫРЬЯ")
    raw_rel = {norm(p.relative_to(RAW)) for p in raw_files}
    over = sorted(p for p in raw_rel if p in GI)
    say("   путей, уже существующих в игре (content/dlc/mods): %d (должно быть 0)" % len(over))
    for p in over[:10]:
        say("      !! %s" % p)
    assert not over, "ВАНИЛЬ ПЕРЕКРЫТА — так нельзя"
    van_dirs = [norm(k) for k in J["dir_twins"]]
    bad = sorted(p for p in raw_rel if any(p.startswith(d) for d in van_dirs))
    assert not bad, ("файлы в ванильных каталогах", bad[:5])
    say("   файлов в ванильных каталогах мода-замены: 0")

    known_broken = {norm(b) for L in sel for _m, b in L.get("broken_textures", [])}
    missing, to_mod_van, van_ents, broken_seen = [], [], set(), set()
    for k, (p, data) in RAWF.items():
        if not (k.endswith(".w2ent") or k.endswith(".w2mesh")):
            continue
        for r in refs(data):
            if r in MOD_VAN:
                to_mod_van.append((k, r))
            elif r in RAWF:
                pass
            elif r in GI:
                if r.endswith(".w2ent"):
                    van_ents.add(r)
            elif r in known_broken:
                broken_seen.add(r)
            else:
                missing.append((k, r))
    say("   ссылок на пути, которые мод-замена ПЕРЕКРЫВАЕТ: %d (должно быть 0)" % len(to_mod_van))
    for a, r in to_mod_van[:10]:
        say("      !! %s -> %s" % (a, r))
    say("   ссылок в пустоту: %d (должно быть 0)" % len(missing))
    for a, r in missing[:10]:
        say("      !! %s -> %s" % (a, r))
    if broken_seen:
        say("   [i] известная ошибка мода (текстуры нет и в TW2 Gear): %s" % ", ".join(sorted(broken_seen)))
    assert not to_mod_van and not missing
    # вложенные ванильные шаблоны не тянут перекрытых модом мешей?
    deep = []
    for r in sorted(van_ents):
        rr, b, e = sorted(GI[r], key=lambda x: x[0] != "content")[0]
        sub = refs(ext(b, e, r))
        deep += [(r, x) for x in sub if x in MOD_VAN]
    say("   ванильных .w2ent по ссылкам: %d, из них тянут меши мода: %d (должно быть 0)"
        % (len(van_ents), len(deep)))
    assert not deep, deep[:5]
    # карточки: шаблоны и варианты — только свои
    ours = {base(k) for k in RAWF if k.startswith("dlc\\%s\\data\\items\\" % MOUNT)}
    for m in re.finditer(r'equip_template\s*=\s*"([^"]+)"', xml_text):
        assert m.group(1).lower() in ours, ("шаблон карточки не собран", m.group(1))
    say("   шаблонов в карточках: %d, все собраны" % len(re.findall(r"equip_template", xml_text)))

    # ---- 9. упаковка ------------------------------------------------------------
    head("УПАКОВКА (wcc_lite из зеркала)")
    OUT.mkdir(parents=True)
    r = subprocess.run([str(WCC), "pack", "-dir=" + str(RAW), "-outdir=" + str(OUT)],
                       capture_output=True, text=True, timeout=900, cwd=str(WCC.parent))
    if not (OUT / "blob0.bundle").exists():
        say("   [!!] pack не собрал (код %d)" % r.returncode)
        for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-15:]:
            say("      " + line.strip()[:140])
        sys.exit(1)
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines():
        l = line.lower()
        if "error" in l or "buffers" in l or "bundle" in l and "creat" in l:
            say("      pack: " + line.strip()[:140])
    r = subprocess.run([str(WCC), "metadatastore", "-path=" + str(OUT)],
                       capture_output=True, text=True, timeout=900, cwd=str(WCC.parent))
    for line in ((r.stdout or "") + (r.stderr or "")).splitlines():
        l = line.lower()
        if "buffer" in l or "numresources" in l or "error" in l or "corrupt" in l:
            say("      metadatastore: " + line.strip()[:140])
    if not (OUT / "metadata.store").exists():
        raise SystemExit("[!!] metadatastore не создал metadata.store")
    # кэш и подписи — после pack: pack выбрасывает .cache из сырья
    n_all, n_keep = strip_cache(MOD / "texture.cache", OUT / "texture.cache", drop)
    oc = cache_tables(OUT / "texture.cache")
    assert oc["n"] == n_keep and set(oc["keys"]) == set(own_keys)
    assert not (set(oc["keys"]) & set(game_keys)), "ключ кэша совпал с игрой"
    say("   [ok] texture.cache: %d -> %d записей, crc сходится, совпадений с игрой 0"
        % (n_all, n_keep))
    for loc in LOCALES:
        shutil.copyfile(STRW / ("frgtw2_%s.csv.w3strings" % loc), guard(OUT / ("%s.w3strings" % loc)))

    # ---- 10. проверка собранного ------------------------------------------------
    head("ПРОВЕРКА СОБРАННОГО")
    blob = {norm(e.name) for e in B.read_index(OUT / "blob0.bundle")}
    bufs = ({norm(e.name) for e in B.read_index(OUT / "buffers0.bundle")}
            if (OUT / "buffers0.bundle").exists() else set())
    want_blob = {p for p in raw_rel if not p.endswith(".buffer")}
    want_buf = {p for p in raw_rel if p.endswith(".buffer")}
    say("   blob0: записей %d (ждали %d), buffers0: %d (ждали %d)"
        % (len(blob), len(want_blob), len(bufs), len(want_buf)))
    lost = sorted((want_blob - blob) | (want_buf - bufs))
    for p in lost[:10]:
        say("      !! не упаковано: %s" % p)
    assert not lost
    over = sorted(p for p in blob | bufs if p in GI)
    say("   путей бандла, совпавших с игрой: %d (должно быть 0)" % len(over))
    assert not over
    for p in (blob | bufs):
        assert norm(p) not in MOD_VAN

    # ---- 11. доноры для кузницы -------------------------------------------------
    DONORS_JSON.write_text(json.dumps(donors, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    head("СОБРАНО")
    say("   %-34s %-6s %-36s %s" % ("донор", "слот", "equip_template", "подпись (ru)"))
    for nm, cat, tpl, vs, ru in table:
        say("   %-34s %-6s %-36s %s" % (nm, cat, tpl, ru))
        for v in vs:
            say("   %-34s %-6s   вариант %s" % ("", "", v))
    if notes:
        say()
        say("   Снятые варианты (%d):" % len(notes))
        for n in notes:
            say("     - " + n)
    say()
    for f in sorted(OUT.iterdir()):
        if f.suffix != ".w3strings":
            say("   %-18s %12d Б" % (f.name, f.stat().st_size))
    say("   %-18s %12d Б  (x%d локалей)" % ("<loc>.w3strings", (OUT / "ru.w3strings").stat().st_size,
                                            len(LOCALES)))
    say()
    by = {}
    for d in donors:
        by[d["cat"]] = by.get(d["cat"], 0) + 1
    say("   доноров: %d (%s)" % (len(donors), ", ".join("%s %d" % kv for kv in sorted(by.items()))))
    say("   шаблонов-двойников: %d, мешевых слоёв: %d, мешей мода: %d, своих текстур: %d"
        % (n_tpl, n_ml, n_mesh_put, len(own_keys)))
    say("   Готово в: %s" % OUT)
    say("   Доноры:   %s" % DONORS_JSON)
    say("   Время: %.0f с" % (time.time() - t0))
    say("   Перенести в игру (ТОЛЬКО при закрытой игре):  python build_tw2looks.py --install")

    # ⛔ МЕТКА ГОДНОСТИ — последней строкой, после всех проверок. Нет метки —
    # install() ничего не поставит (дефект, найденный аудитом 18.09).
    import hashlib
    marks = []
    for f in sorted(OUT.iterdir()):
        if f.is_file() and f.name != "BUILD_OK":
            marks.append("%s %s" % (hashlib.sha1(f.read_bytes()).hexdigest(), f.name))
    (OUT / "BUILD_OK").write_text("\n".join(marks) + "\n", encoding="utf-8")
    say("   [ok] метка годности записана: %d файлов" % len(marks))


def install():
    head("ПЕРЕНОС В ИГРУ — dlc\\dlcFRGTW2")
    if game_running():
        say("   [!!] игра запущена — закрой её и повтори")
        sys.exit(1)
    # ⛔ ставим ТОЛЬКО сборку, прошедшую все проверки
    import hashlib
    okf = OUT / "BUILD_OK"
    if not okf.exists():
        say("   [!!] нет метки годности — сборка не прошла проверки или не делалась")
        sys.exit(1)
    for line in okf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, fname = line.split(" ", 1)
        f = OUT / fname
        if not f.exists() or hashlib.sha1(f.read_bytes()).hexdigest() != digest:
            say("   [!!] файл изменился после сборки: %s — пересобери" % fname)
            sys.exit(1)
    # сверка с игрой ещё раз, прямо перед копированием: между сборкой и
    # установкой могли поставить новые моды
    # game_index() отдаёт ПАРУ (указатель, число бандлов): проверять
    # вхождение надо в указатель, иначе сверка всегда «чистая»
    GI, _nb = game_index()
    mine = set()
    for bn in ("blob0.bundle", "buffers0.bundle"):
        if (OUT / bn).exists():
            mine |= set(bundle_map(OUT / bn))
    clash = sorted(p for p in mine if p in GI)
    if clash:
        say("   [!!] %d путей дополнения совпали с игрой — НЕ ставлю:" % len(clash))
        for p in clash[:10]:
            say("        " + p)
        sys.exit(1)
    say("   [ok] сверка с игрой перед установкой: совпадений 0 из %d путей" % len(mine))
    dst = DLC / "content"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for f in OUT.iterdir():
        if f.is_file() and f.name != "BUILD_OK":
            shutil.copyfile(f, dst / f.name)
    say("   [ok] %s (%d файлов)" % (dst, sum(1 for _ in dst.iterdir())))
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
    say("   Дальше: tw2_donors.json -> доноры кузницы (skin-only), пересобрать")
    say("   dlcFRGBlanks (build_blanks.py) — жетоны TW2 появятся у Элихаля.")


if __name__ == "__main__":
    if INSTALL:
        install()
    else:
        if game_running():
            say("   [i] игра запущена — собираю в скретчпад, папку игры не трогаю")
        main()
