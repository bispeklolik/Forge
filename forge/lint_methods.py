# -*- coding: utf-8 -*-
u"""ЛИНТ: методы игрока, позванные из чужого класса без объекта.

Ровно та ошибка, что трижды стоила сборки: `@addMethod( W3PlayerWitcher )
function FRG_X` зовётся внутри `@addMethod( W3CraftingManager )` просто как
`FRG_X( ... )` — компилятор ищет среди методов ТОГО класса и не находит.

Проверка: собрать имена методов каждого класса, пройти по телам функций и
найти голые вызовы чужих методов.
"""
import io, re, sys

WS = [r"F:\SteamLibrary\steamapps\common\The Witcher 3\mods\modForgeLab\content\scripts\local\forgelab.ws",
      r"F:\SteamLibrary\steamapps\common\The Witcher 3\mods\modCharmTransfer\content\scripts\local\CharmTransfer.ws"]

HEAD = re.compile(r"^(?:@(addMethod|wrapMethod|replaceMethod)\(\s*(\w+)\s*\)\s*)?"
                  r"(?:timer\s+)?(?:exec\s+)?function\s+(\w+)\s*\(", re.M)

# Слова языка, которыми нельзя называть переменные и параметры. Проверяются
# только НАШИ файлы, поэтому список без экзотики: тут то, на чём реально
# спотыкаешься. `def` уже стоил одной сборки (16.09).
RESERVED = set("""
def var function class extends import final latent entry in out optional
saved quest storyscene reward statemachine state event timer cleanup abstract
const editable inlined private protected public default new delete return
if else switch case break continue for while do true false NULL this super
parent virtual_parent enum struct array exec hint single replicate
""".split())

VARDECL = re.compile(r"\bvar\s+([^;:]+):", re.M)
PARAMS = re.compile(r"function\s+\w+\s*\(([^)]*)\)")
ASSIGN = re.compile(r"^\s*(\w+)\s*=[^=]", re.M)


def reserved_hits(s):
    """Имена-нарушители: объявления var и параметры функций."""
    out = []
    for m in VARDECL.finditer(s):
        for nm in m.group(1).split(","):
            nm = nm.strip()
            if nm in RESERVED:
                out.append((s.count("\n", 0, m.start()) + 1, nm, "var"))
    # присваивание: `def = '...'` компилятор тоже не проглотит, а прошлая
    # версия проверки смотрела только объявления и параметры — и пропустила
    # ровно этот случай (16.09, вторая упавшая сборка подряд)
    for m in ASSIGN.finditer(s):
        if m.group(1) in RESERVED:
            out.append((s.count(chr(10), 0, m.start()) + 1,
                        m.group(1), "присваивание"))
    for m in PARAMS.finditer(s):
        for part in m.group(1).split(","):
            part = part.split(":")[0]
            for w in ("out", "optional"):
                part = part.replace(w + " ", " ")
            nm = part.strip()
            if nm in RESERVED:
                out.append((s.count("\n", 0, m.start()) + 1, nm, "параметр"))
    return out


# Правило рода строки живёт в ОДНОМ судье (18.09). Кто ещё зовёт эти
# функции — пишет свою копию правила, и протечка броневых свойств в мечи
# возвращается. Разрешены: судья, печатающий отчёт frgrelic и сами функции
# (генератор может нарезать их на куски FRGL_Cat_1, FRGL_Cat_2 ...).
JUDGE_ONLY = ("FRGL_IsArmorLine", "FRGL_Cat")
JUDGE_ALLOWED = ("FRGW_LineVerdict", "frgrelic")


def judge_hits(s):
    heads = [(m.start(), m.group(1)) for m in
             re.finditer(r"function\s+(\w+)\s*\(", s)]
    out = []
    for m in re.finditer(r"\b(" + "|".join(JUDGE_ONLY) + r")\s*\(", s):
        fn = "?"
        for pos, name in heads:
            if pos < m.start():
                fn = name
            else:
                break
        if fn in JUDGE_ALLOWED or any(fn == j or fn.startswith(j + "_")
                                      for j in JUDGE_ONLY):
            continue
        out.append((s.count("\n", 0, m.start()) + 1, fn, m.group(1)))
    return out


bad_total = 0
for path in WS:
    s = io.open(path, encoding="utf-16").read()
    heads = [(m.start(), m.group(2) or "", m.group(3)) for m in HEAD.finditer(s)]
    # имя метода -> класс, на котором объявлен (только классовые)
    owner = {}
    for _pos, cls, fn in heads:
        if cls:
            owner.setdefault(fn, set()).add(cls)
    globals_ = set(fn for _p, cls, fn in heads if not cls)

    bad = []
    for i, (pos, cls, fn) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(s)
        body = s[pos:end]
        for m in re.finditer(r"(^|[^\w.])(\w+)\s*\(", body):
            name = m.group(2)
            if name in globals_ or name not in owner:
                continue
            if cls and cls in owner[name]:
                continue          # свой класс - можно без объекта
            n = s.count("\n", 0, pos + m.start()) + 1
            bad.append((n, fn, cls or "(global)", name, sorted(owner[name])))

    res = reserved_hits(s)
    jh = judge_hits(s) if "forgelab" in path.lower() else []
    print("### %s" % path.split("\\")[-1])
    for n, fn, name in jh:
        print("    строка %5d  %s зовёт %s — правило рода только у судьи FRGW_LineVerdict" % (n, fn, name))
    bad_total += len(jh)
    for n, nm, kind in res:
        print("    строка %5d  %s '%s' — это слово языка, компилятор откажет" % (n, kind, nm))
    bad_total += len(res)
    if not bad:
        print("    чисто")
    for n, fn, cls, name, own in bad:
        print("    строка %5d  в %s [%s] зовёт %s — метод %s" % (n, fn, cls, name, ", ".join(own)))
    bad_total += len(bad)

sys.exit(1 if bad_total else 0)
