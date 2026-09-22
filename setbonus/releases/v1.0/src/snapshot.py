# -*- coding: utf-8 -*-
"""
Снимает копию рабочей версии мода: и то, что установлено в игру, и исходники.

Зачем отдельно от обычной сборки: сборка ВСЕГДА перезаписывает установленное.
Пока версия не снята, любая следующая правка стирает работающее состояние — и
если правка окажется неудачной, возвращаться будет некуда.

Копия самодостаточна: по ней можно и восстановить мод, и пересобрать заново.
"""
import os, shutil, sys, zipfile
from pathlib import Path

HERE = Path(__file__).parent
GAME = Path(r"F:\SteamLibrary\steamapps\common\The Witcher 3")
MOD = GAME / "mods" / "modSetBonusTransfer"
CFG = GAME / "bin" / "config" / "r4game" / "user_config_matrix" / "pc"
OUT = HERE / "releases"

VERSION = sys.argv[1] if len(sys.argv) > 1 else "v1.0"

NOTES = """modSetBonusTransfer %s
=================================

ЧТО РАБОТАЕТ (проверено в игре)

  Восемь рунных камней, по одному на ведьмачью школу. Камень применяется к надетой
  вещи из инвентаря — как краска — и вещь начинает считаться частью этого комплекта.
  Бонус выдаёт сама игра.

    * гнездо руны НЕ занимается — меняется свойство самой вещи;
    * камень НЕ тратится, одним камнем можно пройтись по всем шести слотам;
    * цели — вся броня И оба меча (в игре краски мечей не касаются, это добавка мода);
    * работает и на обычных вещах, и на настоящих комплектных — тогда вещь
      считается ОДНИМ комплектом, нашим, а не двумя сразу;
    * переживает сохранение и полный перезапуск игры.

  Рецепты: камень школы стоит пустого рунного камня И ВЛАДЕНИЯ полным комплектом
  этой школы (6 предметов ЛЮБОГО качества). Комплект не расходуется — его надо иметь.
  Пока комплекта нет, рецепт серый.

  Раздел настроек: Настройки -> Модификации -> «Перенос сетовых бонусов».
  Пять переключателей: сообщения, мечи, комплектные вещи, расход камня, выдача чертежей.

  Подписи: 17 локалей. Русский и английский написаны, остальные получают английский.

УСТРОЙСТВО (кратко)

  * принадлежность к комплекту хранится ЧИСЛОМ на экземпляре вещи
    (SetItemModifierInt) — оно переживает сейв, в отличие от ярлыков;
  * ярлыки комплекта проставляются заново при каждой загрузке, из обёртки OnSpawned;
  * счётчик надетых частей ПЕРЕСЧИТЫВАЕТСЯ с нуля, а не двигается на +-1;
  * пять обёрток, ни одного скопированного чужого файла.

  ⚠️ Класс меню инвентаря в этой сборке — WmkCR4InventoryMenu (W3EE вмёржил
     Quick Slots). В ванильной игре он называется CR4InventoryMenu. Это
     единственное место, где ванильная версия мода разойдётся с редуксовой.

КАК ВОССТАНОВИТЬ

  1. Скопировать папку  mod/modSetBonusTransfer  в  <игра>/mods/
  2. Скопировать  config/SetBonusTransfer.xml  в
     <игра>/bin/config/r4game/user_config_matrix/pc/
  3. Дописать строку  SetBonusTransfer.xml;  в ОБА списка
     dx11filelist.txt и dx12filelist.txt (они в UTF-16 LE!)
  4. Прописать мод в mods.settings

  Либо пересобрать из src: build_core.py, build_item.py, build_menu.py.
""" % VERSION


def say(s=""):
    print(s, flush=True)


dst = OUT / VERSION
if dst.exists():
    say("  Версия %s уже снята: %s" % (VERSION, dst))
    say("  Укажите другое имя:  python snapshot.py v1.1")
    sys.exit(2)

say("=" * 66)
say("  Снимок версии %s" % VERSION)
say("=" * 66)

(dst / "mod").mkdir(parents=True)
(dst / "config").mkdir()
(dst / "src").mkdir()

shutil.copytree(MOD, dst / "mod" / MOD.name)
n_mod = sum(1 for _ in (dst / "mod").rglob("*") if _.is_file())
say("   [ok] мод: %d файлов" % n_mod)

xml = CFG / "SetBonusTransfer.xml"
if xml.exists():
    shutil.copyfile(xml, dst / "config" / xml.name)
    say("   [ok] окно настроек")
else:
    say("   [!!] окна настроек нет — запустите build_menu.py")

for f in ("build_core.py", "build_item.py", "build_menu.py", "snapshot.py"):
    p = HERE / f
    if p.exists():
        shutil.copyfile(p, dst / "src" / f)
say("   [ok] исходники сборки")

(dst / "README.txt").write_bytes(NOTES.encode("utf-8"))

# готовый архив: дерево игры целиком, чтобы менеджер модов разложил правильно
zp = OUT / ("modSetBonusTransfer %s.zip" % VERSION)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (dst / "mod").rglob("*"):
        if p.is_file():
            z.write(p, str(Path("mods") / p.relative_to(dst / "mod")))
    if xml.exists():
        z.write(xml, r"bin/config/r4game/user_config_matrix/pc/SetBonusTransfer.xml")
    z.writestr("README.txt", NOTES)
say("   [ok] архив: %s (%d КБ)" % (zp.name, zp.stat().st_size // 1024))

say()
say("   Снимок: %s" % dst)
say("   Дальнейшие правки идут поверх установленного мода;")
say("   вернуться к этой версии можно по README.txt из снимка.")
