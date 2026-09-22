# -*- coding: utf-8 -*-
"""
Собирает ДВА одноразовых мода-опыта.

  modASHTagTest   - чистый скрипт, две консольные команды: повесить ярлык и прочитать.
                    Отвечает на вопрос: переживает ли ярлык сохранение игры.

  modASHItemTest  - набор файлов с НОВЫМ именем файла определений и одним предметом.
                    Отвечает на вопрос: подхватывает ли игра новые карточки предметов.

Оба ставятся в игру и снимаются целиком. Ничего чужого не трогают.
"""
import os, re, shutil, subprocess, sys

sys.path.insert(0, r"D:\Apps\w3-mod-manager")
from medallion import bundles

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
WCC = os.path.join(GAME, "mods", "Tools", "wcc_lite", "bin", "x64", "wcc_lite.exe")

TAGMOD = os.path.join(GAME, "mods", "modASHTagTest")
ITEMMOD = os.path.join(GAME, "mods", "modASHItemTest")


def say(s=""):
    print(s, flush=True)


def head(s):
    say(); say("=" * 64); say("  " + s); say("=" * 64)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


# ---- сверка имён, которые собираемся использовать -------------------
def scan_names(names):
    found = {n: 0 for n in names}
    for root in (os.path.join(GAME, "content", "content0", "scripts"),
                 os.path.join(GAME, "mods", "modW3EE", "content", "scripts")):
        for base, _d, fs in os.walk(root):
            for fn in fs:
                if not fn.endswith(".ws"):
                    continue
                raw = open(os.path.join(base, fn), "rb").read()
                t = raw.decode("utf-16", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8", "replace")
                for n in names:
                    found[n] += len(re.findall(r"\b%s\b" % re.escape(n), t))
    return found


head("Сверка имён перед сборкой")
NEED = ["EES_Gloves", "EES_Armor", "EES_Boots", "EES_Pants", "SItemUniqueId"]
res = scan_names(NEED)
bad = [n for n, c in res.items() if c == 0]
for n, c in res.items():
    say("   [%s] %-16s %d" % ("OK" if c else "!!", n, c))
if bad:
    say(); say("  ОСТАНОВКА: не найдены имена: %s" % ", ".join(bad))
    sys.exit(1)

if game_running():
    say(); say("  ИГРА ЗАПУЩЕНА. Закройте её и запустите сборку снова.")
    sys.exit(3)


# =====================================================================
# ОПЫТ 1 — ярлык и пометка
# =====================================================================
TAGWS = """// modASHTagTest - throwaway experiment, safe to delete.
// Two console commands. Open the debug console and type them.
//
//   ashtag     - put a tag AND an int modifier on the equipped GLOVES
//   ashread    - report whether the tag and the modifier are still there
//
// The question: does a custom tag survive a save/load round trip?
// The int modifier is the control sample - it is already known to survive.

exec function ashtag()
{
\tvar item : SItemUniqueId;
\tvar ok   : bool;

\tok = GetWitcherPlayer().GetItemEquippedOnSlot( EES_Gloves, item );
\tif( !ok )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "ASH: no gloves equipped" );
\t\treturn;
\t}

\tthePlayer.inv.AddItemTag( item, 'ASH_TestTag' );
\tthePlayer.inv.SetItemModifierInt( item, 'ASH_TestMod', 777 );

\ttheGame.GetGuiManager().ShowNotification( "ASH: tag and modifier written on gloves" );
}

exec function ashread()
{
\tvar item : SItemUniqueId;
\tvar ok   : bool;
\tvar hasTag : bool;
\tvar modVal : int;
\tvar msg : string;

\tok = GetWitcherPlayer().GetItemEquippedOnSlot( EES_Gloves, item );
\tif( !ok )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "ASH: no gloves equipped" );
\t\treturn;
\t}

\thasTag = thePlayer.inv.ItemHasTag( item, 'ASH_TestTag' );
\tmodVal = thePlayer.inv.GetItemModifierInt( item, 'ASH_TestMod', 0 );

\tif( hasTag )
\t\tmsg = "TAG: YES";
\telse
\t\tmsg = "TAG: no";

\tmsg = msg + "   MODIFIER: " + modVal;

\t// duration is in MILLISECONDS, not seconds. 6.0 meant six milliseconds -
\t// the notification died in the same frame it was born. Vanilla uses 9000.
\ttheGame.GetGuiManager().ShowNotification( msg, 9000 );
\tLogChannel( 'ASH', msg );
}
"""

head("Опыт 1: modASHTagTest")
d = os.path.join(TAGMOD, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "ASHTagTest.ws")
data = TAGWS.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
say("   [ok] ASHTagTest.ws  %d Б  UTF-16 LE + BOM" % len(data))


# =====================================================================
# ОПЫТ 2 — новый предмет через НОВОЕ имя файла определений
# =====================================================================
ITEMXML = """<?xml version="1.0" encoding="UTF-16"?>
<redxml>
\t<definitions>
\t\t<items>
\t\t\t<item
\t\t\t\tname\t\t\t\t\t\t\t="ASH Test Stone"
\t\t\t\tcategory\t\t\t\t\t\t="upgrade"
\t\t\t\tprice\t\t\t\t\t\t\t="155"
\t\t\t\tweight\t\t\t\t\t\t\t="0.06"
\t\t\t\tstackable\t\t\t\t\t\t="1"
\t\t\t\tgrid_size\t\t\t\t\t\t="1"
\t\t\t\tlocalisation_key_name\t\t\t="item_name_rune_stribog_lesser"
\t\t\t\tlocalisation_key_description\t="item_category_runes_desc"
\t\t\t\ticon_path\t\t\t\t\t\t="icons/inventory/ingredients/runes/rune_stribog_lesser_64x64.png"
\t\t\t>
\t\t\t\t<tags>\t\t\t\t\t\t\tUpgrade, mod_upgrade
\t\t\t\t</tags>
\t\t\t</item>
\t\t</items>
\t</definitions>
</redxml>
"""

head("Опыт 2: modASHItemTest")
cdir = os.path.join(ITEMMOD, "content")
os.makedirs(cdir, exist_ok=True)

payload = ITEMXML.replace("\n", "\r\n").encode("utf-16")
items = {
    r"gameplay\items\ash_test_items.xml": payload,
    r"gameplay\items_plus\ash_test_items.xml": payload,
}
info = bundles.write(os.path.join(cdir, "blob0.bundle"), items, compress=True)
say("   [ok] blob0.bundle — записей: %d, %d Б" % (len(items), os.path.getsize(os.path.join(cdir, "blob0.bundle"))))
say("        имя файла НОВОЕ: ash_test_items.xml (это и есть проверяемый вопрос)")
say("        положен дважды: обычная ветка и ветка Новой игры+")

# опись архива
head("Опись архива (metadata.store)")
if not os.path.exists(WCC):
    say("   [!!] wcc_lite не найден: %s" % WCC)
else:
    try:
        r = subprocess.run([WCC, "metadatastore", "-path=" + cdir],
                           capture_output=True, text=True, timeout=180)
        out = (r.stdout or "") + (r.stderr or "")
        made = os.path.exists(os.path.join(cdir, "metadata.store"))
        say("   код выхода: %d | metadata.store: %s" % (r.returncode, "СОЗДАН" if made else "НЕТ"))
        for line in out.splitlines()[-6:]:
            say("      " + line.strip()[:110])
    except Exception as e:
        say("   [!!] не запустился: %s" % e)


# =====================================================================
# регистрация в mods.settings
# =====================================================================
head("Регистрация в mods.settings")
ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read().decode("utf-8", "replace")
if not os.path.exists(ms + ".bak_ashtests"):
    shutil.copyfile(ms, ms + ".bak_ashtests")
added = []
for name, prio in (("modASHTagTest", 16), ("modASHItemTest", 17)):
    if "[%s]" % name in raw:
        say("   [--] %s уже прописан" % name)
        continue
    raw = raw.rstrip("\r\n") + "\r\n[%s]\r\nEnabled=1\r\nPriority=%d\r\n" % (name, prio)
    added.append(name)
if added:
    open(ms, "wb").write(raw.encode("utf-8"))
    say("   [ok] добавлены: %s" % ", ".join(added))

head("ГОТОВО")
say("   Запустите игру и откройте отладочную консоль.")
say()
say("   ОПЫТ 2 (новый предмет) — проверяется первым, он быстрый:")
say("      additem('ASH Test Stone')")
say("      Появился в сумке на вкладке улучшений -> новые предметы РАБОТАЮТ.")
say("      Не появился -> нужен путь через папку дополнений.")
say()
say("   ОПЫТ 1 (ярлык):")
say("      1. Наденьте любые перчатки")
say("      2. ashtag         -> напишет, что пометки поставлены")
say("      3. ashread        -> должно быть TAG: YES   MODIFIER: 777")
say("      4. Сохранитесь, выйдите в меню, загрузите этот сейв")
say("      5. ashread снова  -> вот это и есть ответ")
say()
say("   Снести оба опыта: удалить папки modASHTagTest и modASHItemTest,")
say("   в mods.settings убрать их секции (бэкап рядом).")
