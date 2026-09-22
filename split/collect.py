# -*- coding: utf-8 -*-
"""
Собирает всё готовое в одну папку D:\\Apps\\w3ee-mods.

Папка ГЕНЕРИРУЕТСЯ целиком: правится всегда исходник, потом запускается это.
Так она не может разъехаться с тем, что стоит в игре.

  py -3 collect.py        пересобрать папку

Порядок работы:  build.py (--stage-only при запущенной игре) -> pack.py -> collect.py
"""
import os, sys, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from spec import MODS

DIST     = os.path.join(ROOT, "dist")
SRC      = os.path.join(ROOT, "src")
DOCS     = os.path.join(ROOT, "docs")
ARCHIVES = r"C:\Users\New\Downloads\w3ee-addons"
OUT      = r"D:\Apps\w3ee-mods"

D_ALL  = os.path.join(OUT, "Установить всё разом")
D_ZIP  = os.path.join(OUT, "Архивы по отдельности")
D_DOC  = os.path.join(OUT, "Документация")
D_SRC  = os.path.join(OUT, "Исходники")


def say(s=""):
    print(s, flush=True)


# что делает каждый мод — для оглавления
WHAT = {
    "modW3EERedux_SignShatter":
        ("Разрыв знаками", "Аард и Игни рвут врагов на куски вместо нокдауна. "
         "Сгоревшие заживо — тоже. Шанс растёт по мере падения здоровья, добивание знаком рвёт гарантированно."),
    "modW3EERedux_DismemberAnyone":
        ("Расчленять всех", "Броня перестаёт мешать мечу. Нильфгаардские солдаты, латники и рыцари "
         "начинают разваливаться так же, как все прочие."),
    "modW3EERedux_FinisherVariety":
        ("Разнообразие добиваний", "Возвращает случайный выбор добивания плюс все анимации из дополнений. "
         "W3EE выбирал по кнопке движения, и стоя на месте это был один и тот же удар в грудь."),
    "modW3EERedux_MetamorphPicker":
        ("Выбор мутаций Метаморфозы", "Метаморфоза включает все изученные мутации разом. "
         "Теперь можно отключить лишние прямо в экране мутаций, пометки [+] и [-]."),
    "modW3EERedux_NoHeartbeat":
        ("Без стука сердца", "Убирает звук сердцебиения на низком здоровье."),
    "modW3EERedux_TierBonuses":
        ("Сетовые бонусы по тирам", "Гроссмейстерский бонус комплекта работает на любом тире, но ослабленным. "
         "Четыре ползунка силы, и описания показывают настоящие числа, а не гроссмейстерские."),
    "modW3EERedux_Mutations":
        ("Починка мутаций", "Инсектоид: курс обмена токсичности занижен в 2.5 раза против собственного описания. "
         "Призрак: показывает настоящую прибавку к знакам вместо обещанных +50%, плюс ползунок обхода сжатия. "
         "Ванильное снижение урона Инсектоида — отдельным тумблером."),
    "modW3EERedux_HonestNumbers":
        ("Честные числа", "Окно персонажа перестаёт завышать. Строки мощи знаков показывают, на чём знак бьёт "
         "на самом деле, а не личную надбавку. Урон мечей учитывает износ клинка, как в бою."),
    "modW3EERedux_FinisherFix":
        ("Починка добиваний", "Лечит баг W3EE: один глифворд Purgation навсегда выключал ВСЕ добивания "
         "до перезапуска игры. Настроек нет."),
}


def copy_tree_into(src, dst):
    for base, _dirs, files in os.walk(src):
        for fn in files:
            s = os.path.join(base, fn)
            d = os.path.join(dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(s, d)


say("=" * 66)
say("  СБОРКА ПАПКИ С МОДАМИ")
say("=" * 66)

if os.path.exists(OUT):
    shutil.rmtree(OUT)
for d in (D_ALL, D_ZIP, D_DOC, D_SRC):
    os.makedirs(d)

# 1. одно дерево на все моды — перетащить в папку игры
n = 0
for m in MODS:
    root = os.path.join(DIST, m["mod"])
    if not os.path.isdir(root):
        say("   [!!] нет сборки %s — сначала build.py" % m["mod"]); continue
    copy_tree_into(root, D_ALL)
    n += 1
say("   [ok] единое дерево: %d модов" % n)

# 2. архивы
z = 0
for f in sorted(glob.glob(os.path.join(ARCHIVES, "*.zip"))):
    shutil.copyfile(f, os.path.join(D_ZIP, os.path.basename(f)))
    z += 1
say("   [ok] архивов: %d" % z)

# 3. документация
d = 0
for f in sorted(glob.glob(os.path.join(DOCS, "*.md"))):
    shutil.copyfile(f, os.path.join(D_DOC, os.path.basename(f)))
    d += 1
tz = os.path.join(ROOT, "ТЗ-Сетовые-бонусы.md")
if os.path.exists(tz):
    shutil.copyfile(tz, os.path.join(D_DOC, os.path.basename(tz)))
    d += 1
say("   [ok] документов: %d" % d)

# 4. исходники
s = 0
for m in MODS:
    p = os.path.join(SRC, m["src"])
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(D_SRC, m["src"])); s += 1
for extra in ("spec.py", "build.py", "pack.py", "collect.py"):
    p = os.path.join(HERE, extra)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(D_SRC, extra)); s += 1
say("   [ok] исходников: %d" % s)

# 5. оглавление
lines = []
lines.append("# Мои моды на Ведьмака 3\n")
lines.append("Надстройки над **W3EE Redux**. Ни один файл W3EE не тронут — всё работает")
lines.append("на аннотациях расширений скриптов, поэтому обновление W3EE их не откатит,")
lines.append("а Script Merger'у нечего сшивать.\n")
lines.append("Папка собирается скриптом `Исходники\\collect.py`. Руками её не правь —")
lines.append("перезапишется. Правится исходник, потом `build.py`, `pack.py`, `collect.py`.\n")
lines.append("## Моды\n")
lines.append("| Папка | Название | Что делает |")
lines.append("|---|---|---|")
for m in MODS:
    name, what = WHAT.get(m["mod"], ("", ""))
    lines.append("| `%s` | **%s** | %s |" % (m["mod"], name, what))
lines.append("")
lines.append("Настройки у всех, кроме починки добиваний: **Настройки → Моды → W3EE →")
lines.append("Дополнения → Надстройки W3EE Redux**.\n")
lines.append("Подписи на 17 языках — все, что понимает игра.\n")
lines.append("## Что где лежит\n")
lines.append("| Папка | Зачем |")
lines.append("|---|---|")
lines.append("| `Установить всё разом` | Готовое дерево `mods` + `bin`. Перетащить обе папки в папку игры. |")
lines.append("| `Архивы по отдельности` | По архиву на мод, для Nexus или чтобы поставить только нужное. |")
lines.append("| `Документация` | Описание и техническая документация. |")
lines.append("| `Исходники` | Тексты модов и сборщик. |")
lines.append("")
lines.append("## Установка\n")
lines.append("1. Перетащить `mods` и `bin` из `Установить всё разом` в папку игры —")
lines.append("   ту, где уже есть `bin`, `content` и `mods`.")
lines.append("2. Вписать имена XML в **оба** файла `dx12filelist.txt` и `dx11filelist.txt`")
lines.append("   в `bin\\config\\r4game\\user_config_matrix\\pc\\`. Без этого моды работают,")
lines.append("   но страница настроек не появляется. Это делает мод Menu Filelist Updater")
lines.append("   (Nexus 7171) — за все установленные моды разом.")
lines.append("")
lines.append("   ⚠️ Оба списка — в кодировке UTF-16 LE. Сохранение их в UTF-8 ломает меню")
lines.append("   ВСЕХ установленных модов, а не только наших.\n")
lines.append("## Удаление\n")
lines.append("Удалить папки модов и убрать строки из обоих списков. В сохранение ничего не")
lines.append("пишется, кроме одного факта у «Выбора мутаций» — он хранит твой выбор и")
lines.append("безвреден после снятия мода.\n")

with open(os.path.join(OUT, "README.md"), "wb") as f:
    f.write(("\r\n".join(lines)).encode("utf-8"))
say("   [ok] оглавление README.md")

say()
total = sum(len(files) for _b, _d, files in os.walk(OUT))
say("   папка: %s" % OUT)
say("   файлов всего: %d" % total)
