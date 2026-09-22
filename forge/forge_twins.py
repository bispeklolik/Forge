# -*- coding: utf-8 -*-
u"""Сущности-двойники для КРОСС-обликов мечей (22–23.09).

Задача: у кросс-меча (например серебряный клинок со стальным обликом) ножны не
показываются, потому что НАЛИЧИЕ/СТОРОНА ножен у игрока гейтится свойством
`swordType` (EWitcherSwordType) в сущности клинка .w2ent — НЕ категорией/слотом.
Серебряные сущности несут swordType=WST_Silver, стальные — свойство опускают.

Решение (проверено в игре): equip_template кросс-карточки указывает не на
сущность донора, а на ДВОЙНИКА — сущность-ОБОЛОЧКУ целевого металла, в которой
ссылка на меш заменена на меш ДОНОРА. Паспорт целевого металла → верные ножны;
геометрия донора (оригинальный путь, буфер геометрии на месте) → нужный облик.

Устройство .w2ent — «МАТРЁШКА» CR2W (23.09): внешний CEntityTemplate несёт
вложенные CR2W (flatCompiledData → скомпилированная сущность → streamingDataBuffer
с компонентами). Путь к мешу — ПОСЛЕДНЯЯ строка блока строк (T0) самых внутренних
CR2W, импорт T2. У каждого вложенного CR2W своё оглавление + префикс у родителя
(u32 длина массива @-4, u32 размер свойства @-8). retarget_mesh правит всё это на
всех уровнях. ОРАКУЛ: 52 пары ванильных уникальных мечей одного шаблона —
перенаправленная оболочка структурно совпадает с настоящим файлом байт-в-байт
(отличия только в данных: GUID компонентов). Прежний edit_meshref правил лишь
внешний CR2W → вложенные ломались → игра падала на экипировке.

Оболочки — две проверенные оракулом уникальные сущности (SHELL). Игра CRC не
проверяет. Копирование меша на новый путь — тупик (геометрия в отдельном
сжатом буфере <путь>.w2mesh.1.buffer, doboz) — не использовать.
"""
from __future__ import annotations
import re, sys, struct
from pathlib import Path

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
from medallion import bundles as B

GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
# оболочки по целевому металлу — ванильные уникальные мечи (CWitcherSword),
# на которых оракул подтвердил retarget_mesh
SHELL = {"silver": "silver_unique_anth", "steel": "steel_unique_abarad"}
_ANY_MESH = re.compile(rb"[a-z0-9_/]+\.w2mesh")


def _norm(s):
    return str(s).replace("\\", "/").lower()


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _cr2w_list(b):
    u"""Все CR2W в байтах: внешний (с 0) и ВЛОЖЕННЫЕ. Вложенный обязан иметь
    префикс свойства: u32 @-4 == fileSize, u32 @-8 == fileSize+8."""
    out = []
    for m in re.finditer(b"CR2W", b):
        s = m.start()
        if s + 160 > len(b):
            continue
        fs = _u32(b, s + 24)
        if fs < 160 or s + fs > len(b):
            continue
        if s > 0 and not (_u32(b, s - 4) == fs and _u32(b, s - 8) == fs + 8):
            continue
        out.append((s, fs))
    return out


def _tables(b, cs):
    return [struct.unpack_from("<III", b, cs + 40 + i * 12) for i in range(10)]


# ── doboz (сжатие 3 в бандлах; medallion его не читает) ──────────────────────
# Формат Doboz (A. T. Áfra): байт атрибутов (версия 0..2 бит, размер полей
# длины 3..5 бит +1, «хранится как есть» 7 бит), затем несжатый и сжатый размеры.
# Далее 32-битные управляющие слова (31 флаг + сторожевая 1 в старшем бите):
# 0 — литерал (1 байт), 1 — совпадение, кодированное 1..4 байтами по младшим
# битам (таблица ниже); длина совпадения >= 3. Копия LZ77 побайтно (перекрытия ок).
_DOBOZ_LUT = [
    (0xff, 2, 0, 0, 1), (0xffff, 2, 0, 0, 2), (0xffff, 6, 15, 2, 2),
    (0xffffff, 8, 31, 3, 3), (0xff, 2, 0, 0, 1), (0xffff, 2, 0, 0, 2),
    (0xffff, 6, 15, 2, 2), (0xffffffff, 11, 255, 3, 4),
]


def doboz_decompress(src):
    attr = src[0]
    scs = ((attr >> 3) & 7) + 1
    fmt = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}.get(scs)
    if fmt is None:
        raise ValueError("doboz: размер поля %d" % scs)
    usize = struct.unpack_from(fmt, src, 1)[0]
    hs = 1 + 2 * scs
    if attr & 128:                                   # хранится без сжатия
        return bytes(src[hs:hs + usize])
    s = bytes(src) + b"\0" * 8                       # запас для чтения слова в хвосте
    out = bytearray()
    ip, cw = hs, 1
    while len(out) < usize:
        if cw == 1:
            cw = struct.unpack_from("<I", s, ip)[0]
            ip += 4
        if cw & 1 == 0:
            out.append(s[ip])
            ip += 1
        else:
            w = struct.unpack_from("<I", s, ip)[0]
            mask, osh, lmask, lsh, size = _DOBOZ_LUT[w & 7]
            off = (w & mask) >> osh
            ln = ((w >> lsh) & lmask) + 3
            ip += size
            if off <= 0 or off > len(out):
                raise ValueError("doboz: битое смещение")
            for _ in range(ln):
                out.append(out[-off])
        cw >>= 1
    return bytes(out[:usize])


def extract_any(f, e):
    u"""Как B.extract, плюс doboz. Doboz проверяем по длине и шапке CR2W."""
    if B.can_extract(e):
        return B.extract(f, e)
    if getattr(e, "comp", None) == 3:
        with open(f, "rb") as fh:
            fh.seek(e.offset)
            blob = fh.read(e.zsize)
        data = doboz_decompress(blob)
        if e.size and len(data) != e.size:
            raise ValueError("doboz: длина %d != %d" % (len(data), e.size))
        return data
    raise ValueError("сжатие %s не поддержано" % getattr(e, "comp", "?"))


def cr2w_imports(b):
    u"""Пути импортов (прямые слеши, нижний регистр) из ВСЕХ уровней матрёшки."""
    out = []
    for s, _fs in _cr2w_list(b):
        tabs = _tables(b, s)
        t0o, _t0c, _ = tabs[0]
        o2, c2, _ = tabs[2]
        for k in range(c2):
            a = s + t0o + _u32(b, s + o2 + k * 8)
            try:
                e = b.index(b"\0", a)
            except ValueError:
                continue
            out.append(_norm(b[a:e].decode("latin1")))
    return out


def retarget_mesh(data, old_fwd, new_fwd):
    u"""Заменить меш-путь old→new (ЛЮБОЙ длины) во всей «матрёшке» CR2W и
    пересчитать ВСЕ смещения/размеры на каждом уровне вложенности.

    При вставке delta байт в точке P (строка в блоке строк T0 самого внутреннего X):
      X:        размер T0; смещения таблиц после P; смещения строк в именах(T1)
                и импортах(T2) после P; смещения чанков(T4) после P; fileSize/bufSize
      предки:   чанк, содержащий P — size+=; чанки/таблицы после P — offset+=;
                fileSize/bufSize
      префиксы: у каждого вложенного — длина массива (@-4) и размер свойства (@-8)
    Поля пишем ДО вставки (в старых координатах) — вставка сдвигает их сама.
    Таблицы T5+ (буферы/встроенное) не встречались — при их наличии отказ (None)."""
    old = old_fwd.replace("/", "\\").encode()
    new = new_fwd.replace("/", "\\").encode()
    if old == new:
        return bytes(data)
    buf = bytearray(data)
    delta = len(new) - len(old)
    occs = [m.start() for m in re.finditer(re.escape(old), buf)
            if m.start() > 0 and buf[m.start() - 1] == 0
            and m.end() < len(buf) and buf[m.end()] == 0]
    if not occs:
        return None
    for P in sorted(occs, reverse=True):          # с конца — ранние позиции не едут
        chain = sorted(c for c in _cr2w_list(buf) if c[0] <= P < c[0] + c[1])
        if not chain:
            return None
        fix = []

        def chunks(cs, t4):
            o4, c4, _ = t4
            for k in range(c4):
                pos = cs + o4 + k * 24
                size, off = _u32(buf, pos + 8), _u32(buf, pos + 12)
                a = cs + off
                if a <= P < a + size:
                    fix.append((pos + 8, size + delta))
                elif a > P:
                    fix.append((pos + 12, off + delta))

        xs, _xfs = chain[-1]
        tx = _tables(buf, xs)
        if any(tx[i][1] for i in range(5, 10)):
            return None
        t0o, t0c, _ = tx[0]
        if not (xs + t0o <= P and P + len(old) < xs + t0o + t0c):
            return None
        rel = P - (xs + t0o)
        fix.append((xs + 40 + 4, t0c + delta))
        for i in range(1, 10):
            o, c, _ = tx[i]
            if (o or c) and xs + o > P:
                fix.append((xs + 40 + i * 12, o + delta))
        for ti in (1, 2):
            o, c, _ = tx[ti]
            for k in range(c):
                pos = xs + o + k * 8
                so = _u32(buf, pos)
                if so > rel:
                    fix.append((pos, so + delta))
        chunks(xs, tx[4])
        fix.append((xs + 24, _u32(buf, xs + 24) + delta))
        fix.append((xs + 28, _u32(buf, xs + 28) + delta))
        for as_, _afs in chain[:-1]:
            ta = _tables(buf, as_)
            if any(ta[i][1] for i in range(5, 10)):
                return None
            for i in range(10):
                o, c, _ = ta[i]
                if (o or c) and as_ + o > P:
                    fix.append((as_ + 40 + i * 12, o + delta))
            chunks(as_, ta[4])
            fix.append((as_ + 24, _u32(buf, as_ + 24) + delta))
            fix.append((as_ + 28, _u32(buf, as_ + 28) + delta))
        for s, _fs in chain:
            if s > 0:
                fix.append((s - 4, _u32(buf, s - 4) + delta))
                fix.append((s - 8, _u32(buf, s - 8) + delta))
        if len(set(p for p, _v in fix)) != len(fix):
            return None
        for pos, v in fix:
            struct.pack_into("<I", buf, pos, v)
        buf[P:P + len(old)] = new
    lst = _cr2w_list(buf)
    if not lst or lst[0] != (0, len(buf)):
        return None
    return bytes(buf)


def fnv1a_nul(s):
    u"""Хэш имени в таблице имён CR2W: FNV-1a-32 по строке ВМЕСТЕ с \\0
    (сверено на 7 из 7 настоящих имён меша ножен)."""
    h = 0x811c9dc5
    for c in bytes(s) + b"\0":
        h ^= c
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def replace_whole_string(data, old, new):
    u"""Обобщение retarget_mesh для ОДИНОЧНЫХ и вложенных CR2W: заменить ЦЕЛУЮ
    строку блока строк old→new (bytes, любой длины) и пересчитать всё, плюс:
      * хэш имени в таблице имён (T1), если строка — имя (FNV-1a+\\0);
      * таблица буферов (T5, записи по 24 Б: флаги, индекс, смещение, размеры, crc):
        внешние буферы (смещение 0) не трогаем, встроенные после P — сдвигаем.
    Таблицы T6+ — отказ (None). Для мешей ножен (переименование костей)."""
    if old == new:
        return bytes(data)
    buf = bytearray(data)
    delta = len(new) - len(old)
    occs = [m.start() for m in re.finditer(re.escape(old), buf)
            if m.start() > 0 and buf[m.start() - 1] == 0
            and m.end() < len(buf) and buf[m.end()] == 0]
    if not occs:
        return None
    for P in sorted(occs, reverse=True):
        chain = sorted(c for c in _cr2w_list(buf) if c[0] <= P < c[0] + c[1])
        if not chain:
            return None
        fix = []

        def chunks(cs, t4):
            o4, c4, _ = t4
            for k in range(c4):
                pos = cs + o4 + k * 24
                size, off = _u32(buf, pos + 8), _u32(buf, pos + 12)
                a = cs + off
                if a <= P < a + size:
                    fix.append((pos + 8, size + delta))
                elif a > P:
                    fix.append((pos + 12, off + delta))

        def buffers(cs, t5):
            o5, c5, _ = t5
            for k in range(c5):
                pos = cs + o5 + k * 24
                off = _u32(buf, pos + 8)
                if off and cs + off > P:
                    fix.append((pos + 8, off + delta))

        xs, _xfs = chain[-1]
        tx = _tables(buf, xs)
        if any(tx[i][1] for i in range(6, 10)):
            return None
        t0o, t0c, _ = tx[0]
        if not (xs + t0o <= P and P + len(old) < xs + t0o + t0c):
            return None
        rel = P - (xs + t0o)
        fix.append((xs + 40 + 4, t0c + delta))
        for i in range(1, 10):
            o, c, _ = tx[i]
            if (o or c) and xs + o > P:
                fix.append((xs + 40 + i * 12, o + delta))
        o1, c1, _ = tx[1]
        for k in range(c1):                                   # имена: смещение + хэш
            pos = xs + o1 + k * 8
            so = _u32(buf, pos)
            if so > rel:
                fix.append((pos, so + delta))
            elif so == rel:
                fix.append((pos + 4, fnv1a_nul(new)))
        o2, c2, _ = tx[2]
        for k in range(c2):                                   # импорты: смещение
            pos = xs + o2 + k * 8
            so = _u32(buf, pos)
            if so > rel:
                fix.append((pos, so + delta))
        chunks(xs, tx[4])
        buffers(xs, tx[5])
        fix.append((xs + 24, _u32(buf, xs + 24) + delta))
        fix.append((xs + 28, _u32(buf, xs + 28) + delta))
        for as_, _afs in chain[:-1]:
            ta = _tables(buf, as_)
            if any(ta[i][1] for i in range(6, 10)):
                return None
            for i in range(10):
                o, c, _ = ta[i]
                if (o or c) and as_ + o > P:
                    fix.append((as_ + 40 + i * 12, o + delta))
            chunks(as_, ta[4])
            buffers(as_, ta[5])
            fix.append((as_ + 24, _u32(buf, as_ + 24) + delta))
            fix.append((as_ + 28, _u32(buf, as_ + 28) + delta))
        for s, _fs in chain:
            if s > 0:
                fix.append((s - 4, _u32(buf, s - 4) + delta))
                fix.append((s - 8, _u32(buf, s - 8) + delta))
        if len(set(p for p, _v in fix)) != len(fix):
            return None
        for pos, v in fix:
            struct.pack_into("<I", buf, pos, v)
        buf[P:P + len(old)] = new
    lst = _cr2w_list(buf)
    if not lst or lst[0] != (0, len(buf)):
        return None
    return bytes(buf)


def cr2w_selfcheck(b):
    u"""Самопроверка CR2W после правки: у всех уровней — смещения строк имён и
    импортов внутри блока строк и указывают на целую строку; хэши имён = FNV-1a+\\0;
    чанки внутри файла. True/False."""
    try:
        for s, fs in _cr2w_list(b):
            tabs = _tables(b, s)
            t0o, t0c, _ = tabs[0]
            for ti in (1, 2):
                o, c, _ = tabs[ti]
                for k in range(c):
                    so = _u32(b, s + o + k * 8)
                    if so >= t0c or (so and b[s + t0o + so - 1] != 0):
                        return False
                    if ti == 1 and so:
                        a = s + t0o + so
                        if _u32(b, s + o + k * 8 + 4) != fnv1a_nul(b[a:b.index(b"\0", a)]):
                            return False
            o4, c4, _ = tabs[4]
            for k in range(c4):
                size, off = _u32(b, s + o4 + k * 24 + 8), _u32(b, s + o4 + k * 24 + 12)
                if off + size > fs:
                    return False
        return True
    except Exception:
        return False


# имена костей скелета ножен у игрока (scabbards_crossbow.w2rig), по стороне
_SCAB_BONES = ("%s_sword_scabbard", "%s_sword_scabbard_1", "%s_sword_scabbard_2",
               "%s_sword_scabbard_3", "%s_sword_back")


class TwinMaker:
    u"""Собирает двойников: оболочка целевого металла (SHELL) + меш донора."""

    def __init__(self):
        self._names = None          # base -> (bundle, entry) — все .w2ent игры
        self._files = None          # множество всех путей файлов игры (для проверки мешей)
        self._cache = {}            # base -> bytes | None
        self.made = {}              # twin_name -> bytes
        self.extra = {}             # совместимость со сборщиком (копий мешей больше нет)
        self.stats = {"ok": 0, "no_donor": 0, "no_mesh": 0, "fail": 0}
        self.problems = {}          # donor -> причина (уникально)
        self.picked = {}            # donor -> (выбранный меш, из скольких кандидатов)
        self._paths = None          # путь -> (bundle, entry) — ВСЕ файлы игры
        self._scab = None           # имя предмета-ножен -> (категория, шаблон)
        self._scab_by_tpl = None    # шаблон -> [имена предметов]
        self._scab_made = {}        # (шаблон, металл) -> имя нового предмета-ножен
        self.scab_defs_new = []     # XML новых предметов-ножен (кладём в карточки)
        self.scab_log = {}          # предмет -> как решили (пара / двойник / запас)

    # ---- доступ к сущностям и файлам ----------------------------------------------
    def _scan_names(self):
        m, files, paths = {}, set(), {}
        for r in ("content", "dlc"):
            for f in sorted((GAME / r).rglob("*.bundle")):
                sf = str(f)
                if "~" in sf or "FRGBlank" in sf or "FRGScabTest" in sf:
                    continue
                try:
                    entries = B.read_index(f)
                except Exception:
                    continue
                for e in entries:
                    n = _norm(getattr(e, "name", ""))
                    files.add(n)
                    paths.setdefault(n, (f, e))
                    if n.endswith(".w2ent") and "buffer" not in f.name:
                        m.setdefault(n.split("/")[-1][:-6], (f, e))
        self._names, self._files, self._paths = m, files, paths

    def entity(self, base):
        if self._names is None:
            self._scan_names()
        base = base.lower()
        if base in self._cache:
            return self._cache[base]
        hit = self._names.get(base)
        data = None
        if hit:
            try:
                data = extract_any(*hit)
            except Exception:
                data = None
        self._cache[base] = data
        return data

    def mesh_ok(self, p):
        u"""Меш реально есть в игре (и его буфер геометрии, если он вообще нужен)."""
        if self._files is None:
            self._scan_names()
        return p in self._files

    # ---- какой меш показывает донор -------------------------------------------------
    def _meshes_of(self, b):
        out = []
        for p in cr2w_imports(b):
            if p.endswith(".w2mesh") and p not in out:
                out.append(p)
        return out

    def donor_meshes(self, base, _depth=0):
        u"""(список [основной меш] или [], статус).
        1) прямые импорты .w2mesh, только СУЩЕСТВУЮЩИЕ файлы;
        2) если нет — идём по включённым шаблонам .w2ent (кроме fx), до 2 уровней;
        3) если кандидатов несколько — основной: имя файла == имя донора, иначе
           имя файла, чья основа входит в имя донора (axe1 ⊂ axe1geralt), иначе первый."""
        d = self.entity(base)
        if d is None:
            return [], "no_donor"
        cands = [p for p in self._meshes_of(d) if self.mesh_ok(p)]
        if not cands and _depth < 2:
            for inc in cr2w_imports(d):
                if not inc.endswith(".w2ent") or "_fx" in inc or "/fx/" in inc:
                    continue
                sub, st = self.donor_meshes(inc.split("/")[-1][:-6], _depth + 1)
                for p in sub:
                    if p not in cands:
                        cands.append(p)
        if not cands:
            return [], "no_mesh"
        if len(cands) > 1:
            b0 = base.lower()
            stems = [(p, p.split("/")[-1][:-7]) for p in cands]
            exact = [p for p, s in stems if s == b0]
            inside = sorted([p for p, s in stems if s and s in b0],
                            key=lambda p: -len(p.split("/")[-1]))
            chosen = (exact or inside or cands)[0]
            self.picked[b0] = (chosen, len(cands))
            return [chosen], "ok"
        return cands, "ok"

    # ---- ножны кросс-меча ----------------------------------------------------------
    def file_bytes(self, path):
        if self._paths is None:
            self._scan_names()
        hit = self._paths.get(_norm(path))
        if not hit:
            return None
        try:
            return extract_any(*hit)
        except Exception:
            return None

    def scabbard_defs(self):
        u"""Все предметы-ножны игры (включая моды и doboz-XML): имя -> (категория, шаблон)."""
        if self._scab is not None:
            return self._scab
        defs = {}
        for r in ("content", "dlc", "mods"):
            for f in sorted((GAME / r).rglob("*.bundle")):
                sf = str(f)
                if "~" in sf or "FRGBlank" in sf or "FRGScabTest" in sf or "buffer" in f.name:
                    continue
                try:
                    entries = B.read_index(f)
                except Exception:
                    continue
                for e in entries:
                    if not _norm(getattr(e, "name", "")).endswith(".xml"):
                        continue
                    try:
                        raw = extract_any(f, e)
                    except Exception:
                        continue
                    t = None
                    for enc in ("utf-16", "utf-8"):
                        try:
                            t = raw.decode(enc)
                            if "<" in t[:400]:
                                break
                            t = None
                        except Exception:
                            t = None
                    if not t or "scabbard" not in t.lower():
                        continue
                    for mm in re.finditer(r'<item\b([^>]*?)/?>', t):
                        head = mm.group(1)
                        cat = re.search(r'category\s*=\s*"([^"]*)"', head)
                        nm = re.search(r'name\s*=\s*"([^"]+)"', head)
                        if not cat or not nm or "scabbard" not in cat.group(1):
                            continue
                        tpl = re.search(r'equip_template\s*=\s*"([^"]*)"', head)
                        defs.setdefault(nm.group(1), (cat.group(1), tpl.group(1) if tpl else ""))
        by = {}
        for nm, (cat, tpl) in defs.items():
            by.setdefault(tpl.lower(), []).append(nm)
        self._scab, self._scab_by_tpl = defs, by
        return defs

    @staticmethod
    def _side(cat):
        return "silver" if cat.startswith("silver") else ("steel" if cat.startswith("steel") else "")

    def _pair_template(self, tpl, want):
        u"""Шаблон ножен ТОГО ЖЕ стиля, но другого металла (или None)."""
        src = "steel" if want == "silver" else "silver"
        special = {("q704_vampire_scabbard", "silver"): "q704_silver_vampire_scabbard",
                   ("q704_silver_vampire_scabbard", "steel"): "q704_vampire_scabbard"}
        t = tpl.lower()
        if (t, want) in special:
            return special[(t, want)]
        if src in t:
            return t.replace(src, want)
        return None

    def cross_scabbard(self, item, want):
        u"""Какие ножны привязать кросс-мечу вместо item (сторона want).
        1) уже нужной стороны — оставить; 2) пара того же стиля; 3) двойник ножен
        (тот же меш, кости другой стороны); 4) запас — обычные ножны нужной стороны."""
        defs = self.scabbard_defs()
        d = defs.get(item)
        if not d:
            self.scab_log[item] = "неизвестно — оставлено"
            return item
        cat, tpl = d
        if self._side(cat) == want:
            return item
        pt = self._pair_template(tpl, want)
        if pt:
            cands = [n for n in self._scab_by_tpl.get(pt, [])
                     if self._side(defs[n][0]) == want]
            if cands:
                cands.sort(key=lambda n: (n.lower() != pt, "npc" in n.lower(), n))
                self.scab_log[item] = "пара: " + cands[0]
                return cands[0]
        tw = self.make_scabbard_twin(item, want)
        if tw:
            self.scab_log[item] = "двойник: " + tw
            return tw
        fb = "scabbard_%s_3_04" % want
        self.scab_log[item] = "запас: " + fb
        return fb

    def make_scabbard_twin(self, item, want):
        u"""Ножны того же вида, но на другой стороне: меш с переименованными костями
        (steel_sword_scabbard* <-> silver_sword_scabbard*), копия буфера геометрии,
        сущность ножен → на новый меш, новый предмет категории <want>_scabbards."""
        cat, tpl = self.scabbard_defs()[item]
        src = self._side(cat)
        key = (tpl.lower(), want)
        if key in self._scab_made:
            return self._scab_made[key]
        self._scab_made[key] = None
        E = self.entity(tpl)
        if not isinstance(E, (bytes, bytearray)):
            return None
        meshes = [p for p in self._meshes_of(E) if self.mesh_ok(p)]
        if len(meshes) != 1:
            return None
        M = meshes[0]
        mb = self.file_bytes(M)
        if not mb:
            return None
        mb2, renamed = mb, 0
        for pat in _SCAB_BONES:
            r = replace_whole_string(mb2, (pat % src).encode(), (pat % want).encode())
            if r is not None:
                mb2, renamed = r, renamed + 1
        if not renamed or not cr2w_selfcheck(mb2):
            return None
        stem = M.split("/")[-1][:-7]
        new_mesh = "characters/models/geralt/scabbards/model/frg/%s_frg%s.w2mesh" % (stem, want)
        files = {new_mesh: mb2}
        o5, c5, _ = _tables(mb, 0)[5]
        for k in range(c5):
            idx = _u32(mb, o5 + k * 24 + 4)
            bb = self.file_bytes("%s.%d.buffer" % (M, idx))
            if not bb:
                return None
            files["%s.%d.buffer" % (new_mesh, idx)] = bb
        E2 = retarget_mesh(E, M, new_mesh)
        if E2 is None or not cr2w_selfcheck(E2):
            return None
        ent = "frgsc_%s_%s" % (tpl.lower(), want)
        files["items/bodyparts/geralt_items/scabbards/frg/%s.w2ent" % ent] = E2
        name = "FRG Scabbard %s %s" % (tpl.lower(), want)
        self.extra.update(files)
        self.scab_defs_new.append(
            '<item name="%s" category="%s_scabbards" equip_template="%s" '
            'attachment_type="skinning"><tags>NoShow,NoDrop,EncumbranceOff</tags>'
            '<base_abilities></base_abilities></item>' % (name, want, ent))
        self._scab_made[key] = name
        return name

    def twin_name(self, donor_base, metal):
        u"""Металл В ИМЕНИ: один шаблон бывает у стального И серебряного предмета
        (W3EE: dwarven/gnomish_sword_lvl1/2) — двойники разные."""
        return "frgtw_%s_%s" % (donor_base.lower(), metal)

    def entity_metal(self, base, _depth=0):
        u"""Металл «паспорта» сущности: silver, если swordType=WST_Silver есть в ней
        САМОЙ или во ВКЛЮЧЁННЫХ шаблонах .w2ent (не fx), до 3 уровней; иначе steel.
        Включения важны: у Аэрондита из «Крови и вина», змеиных/мантикоровых школьных
        мечей паспорт лежит во включённом шаблоне — без обхода они выглядели бы
        стальными (ложный двойник у родной карточки, нет двойника у кросс-карточки).
        None — сущность не нашлась."""
        d = self.entity(base)
        if not isinstance(d, (bytes, bytearray)):
            return None
        if b"WST_Silver" in d:
            return "silver"
        if _depth < 3:
            for inc in cr2w_imports(d):
                if not inc.endswith(".w2ent") or "_fx" in inc or "/fx/" in inc:
                    continue
                if self.entity_metal(inc.split("/")[-1][:-6], _depth + 1) == "silver":
                    return "silver"
        return "steel"

    # ---- сборка двойника --------------------------------------------------------
    def make(self, donor_template, target_metal):
        u"""(twin_name, twin_bytes) или None (карточка остаётся на доноре —
        клинок верный, ножен нет; без регресса)."""
        tw = self.twin_name(donor_template, target_metal)
        if tw in self.made:
            self.stats["ok"] += 1
            return tw, self.made[tw]
        meshes, st = self.donor_meshes(donor_template)
        if not meshes:
            self.stats[st if st in self.stats else "fail"] += 1
            self.problems.setdefault(donor_template.lower(), st)
            return None
        shell = SHELL[target_metal]
        sb = self.entity(shell)
        if not isinstance(sb, (bytes, bytearray)):
            self.stats["fail"] += 1
            self.problems.setdefault(donor_template.lower(), "shell_missing")
            return None
        shell_meshes = sorted(set(self._meshes_of(sb)))
        if len(shell_meshes) != 1:
            self.stats["fail"] += 1
            self.problems.setdefault(donor_template.lower(), "shell_multi")
            return None
        twin = retarget_mesh(sb, shell_meshes[0], meshes[0])
        if twin is None or (b"WST_Silver" in twin) != (target_metal == "silver"):
            self.stats["fail"] += 1
            self.problems.setdefault(donor_template.lower(), "retarget_fail")
            return None
        self.made[tw] = twin
        self.stats["ok"] += 1
        return tw, twin


if __name__ == "__main__":
    tm = TwinMaker()
    for donor, tgt in [("steel_unique_abarad", "silver"), ("silver_unique_aerondight", "steel"),
                       ("wildhunt_sword_lvl1", "silver"), ("skellige_sword_lvl1", "silver"),
                       ("toussaint_sword_lv1", "silver")]:
        r = tm.make(donor, tgt)
        print("  %-26s -> %-6s : %s" % (donor, tgt, ("OK %s (%d Б)" % (r[0], len(r[1]))) if r else "НЕТ"))
    print("stats:", tm.stats, "| проблемы:", tm.problems)
