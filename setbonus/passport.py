# -*- coding: utf-8 -*-
r"""
Собирает паспорт дополнения (.reddlc) из файла САМОЙ ИГРЫ.

ЗАЧЕМ ЭТОТ ФАЙЛ ПОЯВИЛСЯ
  Раньше болванку паспорта брали из архива чужого мода «Vagabond Armor»
  (Nexus 3278), лежащего в Загрузках. Для раздачи это негодно по двум
  причинам, и вторая важнее первой:
    1. в цепочке сборки чужой файл;
    2. сборка зависела от архива в личной папке — на другой машине мод
       не пересобирался вообще.

  Выяснилось попутно: паспорт «Бродяги» и сам сделан из паспорта CDPR.
  Таблица строк у него посимвольно совпадает с ванильными dlc1/dlc5/dlc13,
  плюс одна дописанная строка — имя дополнения. Ровно это здесь и делается,
  только болванка берётся из ванильного dlc1, который есть у каждого.

ГДЕ ЛЕЖАТ ВАНИЛЬНЫЕ ПАСПОРТА
  ⚠️ Не там, где у модов. У модов  dlc\<имя>\content\blob0.bundle,
     у CDPR              dlc\<имя>\content\bundles\blob.bundle
  Поиск по blob0.bundle не находит их вовсе — на этом легко обмануться.

ФОРМАТ (разобран полностью, 13.09.2026)
  Заголовок 40 байт: 'CR2W', версия, флаги, метка времени:u64, номер сборки,
  конец_объектов:u32, конец_буферов:u32, crc32, число_таблиц.
  Затем 10 таблиц по 12 байт: (смещение, количество, crc).
    0 — строковый блок, строки через ноль
    1 — имена: по 8 байт (смещение_в_блоке:u32, хеш:u32)
    3 — служебная, 1 запись 16 байт, копируется как есть
    4 — куски: по 24 байта (тип, родитель, размер, смещение, 0, crc)

  Кусок: один служебный байт, затем свойства подряд, в конце u16 = 0.
  Свойство: имя:u16, тип:u16, размер:u32, значение.
    РАЗМЕР СЧИТАЕТ САМ СЕБЯ — то есть равен 4 + длина значения.
  Строка: варинт длины, затем текст latin-1.
    длина < 64  — один байт  0x80 | len
    длина >= 64 — два байта  (0xC0 | (len & 0x3F)), (len >> 6)
  Тип куска — 0x20000000 или 0x20080000 плюс индекс имени класса.

  ⚠️ Хеш имени пересчитать нечем: ни FNV-1/1a, ни CRC32, ни djb2 не сходятся
  с файлами игры. Поэтому у дописанного имени хеш берётся у соседа и остаётся
  «протухшим». Игра его НЕ проверяет — ровно так же жил прежний паспорт,
  собранный из «Бродяги», и работал. Контрольные суммы кусков игра тоже не
  проверяет, но мы их считаем честно.
"""
import os
import struct
import sys
import zlib
from pathlib import Path

BASE = 40
NTAB = 10
GAME_DEFAULT = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")

# Ванильное дополнение, чей паспорт берём болванкой. Набор монтировщиков у него
# тот же, что нужен нам: определения предметов, папка шаблонов, интерфейс и
# три их NG+-двойника.
TEMPLATE_DLC = "dlc1"


# --------------------------------------------------------------------- чтение

def _tables(buf):
    return [struct.unpack_from("<III", buf, BASE + i * 12) for i in range(NTAB)]


def _strings(buf):
    off, cnt, _ = _tables(buf)[0]
    return buf[off:off + cnt]


def _names(buf):
    off, cnt, _ = _tables(buf)[1]
    return [struct.unpack_from("<II", buf, off + i * 8) for i in range(cnt)]


def _name_text(buf, idx):
    blk = _strings(buf)
    rel = _names(buf)[idx][0]
    end = blk.find(b"\0", rel)
    return blk[rel:end if end >= 0 else len(blk)].decode("latin-1")


def name_index(buf, text):
    for i in range(len(_names(buf))):
        if _name_text(buf, i) == text:
            return i
    raise KeyError("нет имени %r в болванке" % text)


def chunk_types(buf):
    """Сырые значения поля «тип» по имени класса — берём из самой болванки,
    чтобы не зашивать числа."""
    off, cnt, _ = _tables(buf)[4]
    out = {}
    for i in range(cnt):
        t = struct.unpack_from("<I", buf, off + i * 24)[0]
        out[_name_text(buf, t & 0xFFFF)] = t
    return out


def load_template(game=GAME_DEFAULT, dlc=TEMPLATE_DLC):
    """Достаёт паспорт ванильного дополнения прямо из бандла игры."""
    sys.path.insert(0, r"D:\Apps\w3-mod-manager")
    from medallion import bundles

    for blob in sorted(Path(game).glob("dlc/%s/content/bundles/*.bundle" % dlc)):
        for e in bundles.read_index(blob):
            if e.name.endswith(".reddlc"):
                return bundles.extract(blob, e)
    raise FileNotFoundError(
        "не нашёл паспорт ванильного %s — проверьте путь к игре: %s" % (dlc, game))


# --------------------------------------------------------------------- запись

def _varint(n):
    if n < 64:
        return bytes([0x80 | n])
    if n < 64 * 256:
        return bytes([0xC0 | (n & 0x3F), n >> 6])
    raise ValueError("строка длиннее, чем умеет варинт: %d" % n)


def _prop_str(nidx, tidx, text):
    body = _varint(len(text)) + text.encode("latin-1")
    return struct.pack("<HHI", nidx, tidx, 4 + len(body)) + body


def _prop_raw(nidx, tidx, value):
    return struct.pack("<HHI", nidx, tidx, 4 + len(value)) + value


def _chunk(props):
    return b"\x00" + b"".join(props) + b"\x00\x00"


def _fix_crc(buf):
    b = bytearray(buf)
    o0, c0, _ = struct.unpack_from("<III", b, BASE)
    struct.pack_into("<I", b, BASE + 8, zlib.crc32(bytes(b[o0:o0 + c0])) & 0xFFFFFFFF)
    o4, c4, _ = struct.unpack_from("<III", b, BASE + 4 * 12)
    for i in range(c4):
        p = o4 + i * 24
        _t, _par, size, off, _z, _crc = struct.unpack_from("<6I", b, p)
        struct.pack_into("<I", b, p + 20, zlib.crc32(bytes(b[off:off + size])) & 0xFFFFFFFF)
    struct.pack_into("<I", b, BASE + 4 * 12 + 8,
                     zlib.crc32(bytes(b[o4:o4 + c4 * 24])) & 0xFFFFFFFF)
    return bytes(b)


def build(mount, name_key, desc_key, items_xml, shop_xml, exts_xml,
          templates_dir="data/items/", template=None):
    """Собирает паспорт.

    mount        имя папки дополнения, оно же точка монтирования (sbtstone)
    name_key     имя дополнения, оно же его CName-идентификатор (sbt_runestone)
    desc_key     ключ описания (sbt_runestone_desc)
    items_xml    имя файла определений    (sbt_runestones.xml)
    shop_xml     имя файла лавки          (sbt_stoneshop.xml)
    exts_xml     имя файла расширений     (sbt_runestone_extensions.xml)
    Длины строк ничем не ограничены — в отличие от прежней побайтовой подмены.
    """
    tpl = template if template is not None else load_template()

    N_ID = name_index(tpl, "id")
    N_CNAME = name_index(tpl, "CName")
    N_NAME = name_index(tpl, "localizedNameKey")
    N_STR = name_index(tpl, "String")
    N_DESC = name_index(tpl, "localizedDescriptionKey")
    N_MOUNT = name_index(tpl, "mounters")
    N_ARR = name_index(tpl, "array:2,0,ptr:IGameplayDLCMounter")
    N_DEFPATH = name_index(tpl, "definitionXmlFilePath")
    N_TPLPATH = name_index(tpl, "entitieTemplatesDirectoryPath")
    N_VIS = name_index(tpl, "visibleInDLCMenu")
    N_BOOL = name_index(tpl, "Bool")

    T = chunk_types(tpl)
    T_ROOT = T["CDLCDefinition"]
    T_DEF = T["CR4DefinitionsDLCMounter"]
    T_TPLS = T["CR4DefinitionsEntitieTemplatesDLCMounter"]
    T_NGP = T["CR4DefinitionsNGPlusDLCMounter"]

    # --- строковый блок: строки болванки плюс имя нашего дополнения ----------
    old_block = _strings(tpl)
    add = name_key.encode("latin-1") + b"\0"
    block = old_block + add
    new_name_rel = len(old_block)

    old_names = _names(tpl)
    names = list(old_names) + [(new_name_rel, old_names[1][1])]
    id_idx = len(names) - 1     # id указывает на дописанное имя

    # --- куски ---------------------------------------------------------------
    def p(*parts):
        return _chunk(list(parts))

    mount_ids = list(range(2, 9))          # куски #1..#7, нумерация с единицы
    arr = struct.pack("<I", len(mount_ids)) + b"".join(
        struct.pack("<I", x) for x in mount_ids)

    d = "dlc\\%s\\data\\gameplay\\items\\" % mount
    dp = "dlc\\%s\\data\\gameplay\\items_plus\\" % mount
    tpls = ("dlc\\%s\\%s" % (mount, templates_dir.replace("/", "\\")))

    bodies = [
        (T_ROOT, 0, p(_prop_raw(N_ID, N_CNAME, struct.pack("<H", id_idx)),
                      _prop_str(N_NAME, N_STR, name_key),
                      _prop_str(N_DESC, N_STR, desc_key),
                      _prop_raw(N_MOUNT, N_ARR, arr),
                      _prop_raw(N_VIS, N_BOOL, b"\x00"))),
        (T_DEF,  1, p(_prop_str(N_DEFPATH, N_STR, d + items_xml))),
        (T_TPLS, 1, p(_prop_str(N_TPLPATH, N_STR, tpls))),
        (T_DEF,  1, p(_prop_str(N_DEFPATH, N_STR, d + shop_xml))),
        (T_DEF,  1, p(_prop_str(N_DEFPATH, N_STR, d + exts_xml))),
        (T_NGP,  1, p(_prop_str(N_DEFPATH, N_STR, dp + items_xml))),
        (T_NGP,  1, p(_prop_str(N_DEFPATH, N_STR, dp + shop_xml))),
        (T_NGP,  1, p(_prop_str(N_DEFPATH, N_STR, dp + exts_xml))),
    ]

    # --- раскладка -----------------------------------------------------------
    head_len = BASE + NTAB * 12                       # 160
    s_off = head_len
    n_off = s_off + len(block)
    t3_off, t3_cnt, t3_crc = _tables(tpl)[3]
    t3_bytes = tpl[t3_off:t3_off + 16 * t3_cnt]
    t3_new = n_off + len(names) * 8
    c_off = t3_new + len(t3_bytes)
    data_off = c_off + len(bodies) * 24

    out = bytearray(tpl[:head_len])                   # заголовок с таблицами
    out += block
    for rel, h in names:
        out += struct.pack("<II", rel, h)
    out += t3_bytes

    cur = data_off
    ctab = bytearray()
    data = bytearray()
    for t, parent, body in bodies:
        ctab += struct.pack("<6I", t, parent, len(body), cur, 0, 0)
        data += body
        cur += len(body)
    out += ctab
    out += data

    def set_table(i, off, cnt):
        struct.pack_into("<III", out, BASE + i * 12, off, cnt, 0)

    set_table(0, s_off, len(block))
    set_table(1, n_off, len(names))
    set_table(3, t3_new, t3_cnt)
    set_table(4, c_off, len(bodies))

    struct.pack_into("<I", out, 24, len(out))         # конец объектов
    struct.pack_into("<I", out, 28, len(out))         # конец буферов
    return _fix_crc(bytes(out))


# ------------------------------------------------------------------ самоcверка

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    tpl = load_template()
    print("болванка: ванильный %s, %d Б" % (TEMPLATE_DLC, len(tpl)))
    b = build("sbtstone", "sbt_runestone", "sbt_runestone_desc",
              "sbt_runestones.xml", "sbt_stoneshop.xml",
              "sbt_runestone_extensions.xml", template=tpl)
    print("паспорт камней: %d Б" % len(b))
    open(os.environ["TEMP"] + r"\sbt_new.reddlc", "wb").write(b)
    r = build("sbtrelic", "sbt_relicsets", "sbt_relicsets_desc",
              "sbt_relic_sets.xml", "sbt_relicshop.xml",
              "sbt_relic_set_extensions.xml", template=tpl)
    print("паспорт реликтов: %d Б" % len(r))
    open(os.environ["TEMP"] + r"\sbtrelic_new.reddlc", "wb").write(r)
