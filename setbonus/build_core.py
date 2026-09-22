# -*- coding: utf-8 -*-
"""
Собирает ЯДРО мода переноса сетовых бонусов: modSetBonusTransfer.

Что делает мод на этом этапе:
  * помечает конкретную вещь числом «принадлежит комплекту N» — число переживает сейв;
  * проставляет ей игровые ярлыки комплекта, чтобы игра сама считала и выдавала бонус;
  * после каждой загрузки возвращает ярлыки на место (ярлыки сейв не переживают).

Крафт и рунный камень — следующий этап. Пока управление консольными командами.

⚠️ Папка мода НЕ описана в split/spec.py, поэтому split/build.py уберёт её в backup.
   Пересобирать этим скриптом.
"""
import os, shutil, subprocess, sys, time

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
MOD = os.path.join(GAME, "mods", "modSetBonusTransfer")
PRIORITY = 18

# ---- две сборки одного мода: под Redux и под чистую ваниль -------------------
#
# Расходятся они ровно в ОДНОМ: как называется класс окна инвентаря. W3EE вмёржил
# туда Quick Slots и переименовал класс. Всё остальное в моде — ванильные функции.
#
#   ваниль : class CR4InventoryMenu    extends CR4MenuBase
#   W3EE   : class WmkCR4InventoryMenu extends CR4MenuBase
#
# Ключ --vanilla собирает ванильный вариант В ОТДЕЛЬНУЮ ПАПКУ и НЕ ставит его в
# игру: в этой установке стоит Redux, ванильный класс тут не существует, и мод
# просто не скомпилируется. Проверить его можно только на чистой игре.
VANILLA = "--vanilla" in sys.argv
MENU_CLASS = "CR4InventoryMenu" if VANILLA else "WmkCR4InventoryMenu"
# Кладём в ОБЩУЮ dist_vanilla в корне проекта, а не в свою папку: там же лежат
# ванильные сетовые бонусы, и оттуда же собирает архивы pack_release.py.
DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "dist_vanilla", "modSetBonusTransfer")

# Значения EItemSetType из playerTypes.ws (порядок объявления = номер).
# Ярлыки — из gameParams.ws.
SETS = [
    (1, "Lynx",    "LynxSet",    "Cat"),
    (2, "Gryphon", "GryphonSet", "Gryphon"),
    (3, "Bear",    "BearSet",    "Bear"),
    (4, "Wolf",    "WolfSet",    "Wolf"),
    (5, "RedWolf", "RedWolfSet", "Manticore"),
    (6, "Vampire", "VampireSet", "Vampire"),
    (7, "Viper",   "ViperSet",   "Viper (no bonus in vanilla)"),
    (8, "Netflix", "NetflixSet", "Netflix"),
]

WS = """// modSetBonusTransfer - core.
// Gives a chosen item the set membership of another set, so its bonus counts.
//
// HOW STATE IS KEPT
//   The set code lives in an item MODIFIER (SBT_Set). Modifiers survive a save;
//   item tags do not - that was measured, not assumed. So the modifier is the
//   truth and the tags are re-stamped after every load from OnSpawned.
//
// CONSOLE COMMANDS
//   sbtset(2)   - stamp every equipped armour piece as Gryphon (see codes below)
//   sbtclear()  - remove the stamp from every equipped armour piece
//   sbtinfo()   - report the stamp and the live set counters
//
// SET CODES  1 Lynx(Cat) | 2 Gryphon | 3 Bear | 4 Wolf | 5 RedWolf(Manticore)
//            6 Vampire   | 7 Viper   | 8 Netflix

// ------------------------------------------------------------- settings ---
//
// Read straight from the mod's own menu group. Same idiom as the other mods here.
// ⚠️ The group name is repeated INSIDE this file - renaming the group in the XML
// without changing it here drops every setting to its fallback, silently.

function SBT_Str( varName : name, fallback : string ) : string
{
\tvar s : string;

\ts = theGame.GetInGameConfigWrapper().GetVarValue( 'SetBonusTransfer', varName );
\tif( s == "" )
\t\treturn fallback;

\treturn s;
}

function SBT_Bool( varName : name, fallback : bool ) : bool
{
\tvar s : string;

\ts = SBT_Str( varName, "" );
\tif( s == "" )
\t\treturn fallback;

\tif( s == "true" || s == "1" )
\t\treturn true;

\treturn false;
}

// Shows a line only when the player wants to be told.
function SBT_Say( msg : string )
{
\tif( SBT_Bool( 'ShowMessages', true ) )
\t\ttheGame.GetGuiManager().ShowNotification( msg, 6000 );
}

@addField( W3PlayerWitcher ) var SBT_didRestore : bool;

// Коды 1..8 — ведьмачьи школы, есть и в ванили, и в Redux.
// Коды 9..19 — реликтовые комплекты, которые добавляет ТОЛЬКО Redux. Здесь они
// названы одними ЯРЛЫКАМИ (это просто строки), поэтому таблица безопасна и в
// ванили: там таких ярлыков просто нет ни у одной вещи, и коды не сработают.
@addMethod( W3PlayerWitcher ) function SBT_TagForCode( code : int ) : name
{
\tswitch( code )
\t{
\t\tcase 1:\treturn 'LynxSet';
\t\tcase 2:\treturn 'GryphonSet';
\t\tcase 3:\treturn 'BearSet';
\t\tcase 4:\treturn 'WolfSet';
\t\tcase 5:\treturn 'RedWolfSet';
\t\tcase 6:\treturn 'VampireSet';
\t\tcase 7:\treturn 'ViperSet';
\t\tcase 8:\treturn 'NetflixSet';

\t\tcase  9:\treturn 'TemerianSet';
\t\tcase 10:\treturn 'NilfgaardSet';
\t\tcase 11:\treturn 'SkelligeSet';
\t\tcase 12:\treturn 'OfieriSet';
\t\tcase 13:\treturn 'NewMoonSet';
\t\tcase 14:\treturn 'ElvenSet';
\t\tcase 15:\treturn 'TigerSet';
\t\tcase 16:\treturn 'GothicSetTag';
\t\tcase 17:\treturn 'DimeritiumSetTag';
\t\tcase 18:\treturn 'MeteoriteSetTag';
\t\tcase 19:\treturn 'VampireSetAlt';
\t}
\treturn '';
}

// Код -> значение перечисления, и БЕЗ единого редуксового имени в нашем коде.
//
// Здесь была ошибка, из-за которой реликтовые камни молча не работали. Я рассчитывал,
// что для кодов 9..19 хватит проставленного ЯРЛЫКА: вернём «не знаю», вопрос уйдёт
// оригиналу, а тот прочитает ярлык. Оригинал читает ярлыки через GetItemTags — и
// ярлык, добавленный на ЭКЗЕМПЛЯР через AddItemTag, туда не попадает. Для восьми
// ведьмачьих школ это было незаметно: их тип мы называем сами и до ярлыка дело
// не доходит.
//
// Правильный вход — SetItemNameToType( ярлык ). Это ОБЫЧНАЯ функция самой игры,
// она есть и в ванили (8 комплектов), и в Redux (19), принимает строку-ярлык и
// возвращает нужное значение. Никаких имён перечисления называть не приходится:
// на ванили незнакомый ярлык просто вернёт EIST_Undefined.
@addMethod( W3PlayerWitcher ) function SBT_SetTypeForCode( code : int ) : EItemSetType
{
\tvar tag : name;

\ttag = SBT_TagForCode( code );
\tif( tag == '' )
\t\treturn EIST_Undefined;

\treturn SetItemNameToType( tag );
}

// Does this item already belong to a set on its own? Ask the game, do not guess.
//
// The first version of this checked for the 'SetBonusPiece' tag and was WRONG:
// Redux splits set bonuses into a minor and a major tier and only the major tier
// carries that tag, so genuine Wolf gear sailed straight past the guard and got
// counted a second time (Wolf went 4 -> 8). IsItemSetItem asks the real question
// and exists in both vanilla (inventoryComponent.ws:3892) and Redux (:6202).
@addMethod( W3PlayerWitcher ) function SBT_IsRealSetPiece( item : SItemUniqueId ) : bool
{
\treturn inv.IsItemSetItem( item );
}

// The set of a stamped item comes from OUR record, not from tag order.
//
// Relying on tags alone was the second half of the same bug: CheckSetType walks the
// item's tags and takes the FIRST set tag it meets. On real Wolf gear the wolf tag
// is already there from the item card, so an added gryphon tag could never win.
@wrapMethod( W3PlayerWitcher ) function CheckSetType( item : SItemUniqueId ) : EItemSetType
{
\tvar code : int;
\tvar st : EItemSetType;

\tcode = inv.GetItemModifierInt( item, 'SBT_Set', 0 );
\tif( code > 0 )
\t{
\t\tst = SBT_SetTypeForCode( code );
\t\tif( st != EIST_Undefined )
\t\t\treturn st;
\t}

\treturn wrappedMethod( item );
}

@addMethod( W3PlayerWitcher ) function SBT_GetCode( item : SItemUniqueId ) : int
{
\treturn inv.GetItemModifierInt( item, 'SBT_Set', 0 );
}

// Puts the working tags on an item that carries our stamp. Does NOT touch counters.
@addMethod( W3PlayerWitcher ) function SBT_StampTags( item : SItemUniqueId, code : int )
{
\tvar tag : name;

\ttag = SBT_TagForCode( code );
\tif( tag == '' )
\t\treturn;

\tinv.AddItemTag( item, tag );

\t// Ярлык «гроссмейстерская вещь». Ставится ВСЕГДА, и это обязательно: без него
\t// не засчитывается ВТОРАЯ строка бонуса — в W3EE она включается только на
\t// гроссмейстерском комплекте.
\t//
\t// ⚠️ Сила этой второй строки — отдельный вопрос, и решается он НЕ здесь.
\t// Мод Tier-Scaled Set Bonuses читает с вещи наше число 'SBT_Set' и считает силу
\t// по тому комплекту, который игрок реально собрал (в сумке, на Плотве или в
\t// тайнике). Переключается это настройкой 'PowerFromOwnedSet' — её читает тот
\t// мод, здесь она только объявлена в меню.
\tinv.AddItemTag( item, theGame.params.ITEM_SET_TAG_BONUS );
}

// Takes back only what we added. The set tag is ours to remove; the bonus tag is
// only ours if the item has no set of its own once our tag is gone.
@addMethod( W3PlayerWitcher ) function SBT_StripTags( item : SItemUniqueId, code : int )
{
\tvar tag : name;

\ttag = SBT_TagForCode( code );
\tif( tag != '' )
\t\tinv.RemoveItemTag( item, tag );

\tif( !inv.IsItemSetItem( item ) )
\t\tinv.RemoveItemTag( item, theGame.params.ITEM_SET_TAG_BONUS );
}

// Give the item a set. Works on plain gear AND on genuine set pieces - wearing
// wolf armour with a gryphon bonus is the whole point of the mod.
//
// The native tag is deliberately left alone. It no longer decides anything:
// CheckSetType is wrapped above and answers from our record, so the item counts
// for one set only - ours. The order below is what matters: take the item off the
// books under whatever it counts as RIGHT NOW, change the record, then put it back
// on the books. Doing it the other way round decrements the wrong counter and
// leaves a bonus that can never be removed.
@addMethod( W3PlayerWitcher ) function SBT_Apply( item : SItemUniqueId, code : int ) : bool
{
\tvar worn : bool;

\tif( !inv.IsIdValid( item ) )
\t\treturn false;

\t// Проверяем по ЯРЛЫКУ, а не по перечислению: у реликтовых комплектов Redux
\t// своего значения в перечислении мы не называем, но ярлык у них есть.
\tif( SBT_TagForCode( code ) == '' )
\t\treturn false;

\tif( SBT_GetCode( item ) == code )
\t\treturn false;

\t// Some players would rather genuine school gear was left as it is.
\tif( SBT_IsRealSetPiece( item ) && !SBT_Bool( 'AllowSetPieces', true ) )
\t\treturn false;

\tinv.SetItemModifierInt( item, 'SBT_Set', code );
\tSBT_StampTags( item, code );

\t// No nudging the counter up and down - just recount. See SBT_Recount.
\tSBT_Recount();

\treturn true;
}

// Undo. A genuine set piece goes back to counting for its own set, because the
// native tag was never taken away.
@addMethod( W3PlayerWitcher ) function SBT_Remove( item : SItemUniqueId ) : bool
{
\tvar code : int;
\tvar worn : bool;

\tif( !inv.IsIdValid( item ) )
\t\treturn false;

\tcode = SBT_GetCode( item );
\tif( code == 0 )
\t\treturn false;

\tSBT_StripTags( item, code );
\tinv.SetItemModifierInt( item, 'SBT_Set', 0 );

\tSBT_Recount();

\treturn true;
}

// After a load the tags are gone but the modifiers are not. Put the tags back.
// No counting here: the counter itself is a saved field and came back with the save.
@addMethod( W3PlayerWitcher ) function SBT_RestoreAll() : int
{
\tvar items : array< SItemUniqueId >;
\tvar i, code, n : int;

\tinv.GetAllItems( items );

\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tcode = SBT_GetCode( items[i] );
\t\tif( code > 0 )
\t\t{
\t\t\tSBT_StampTags( items[i], code );
\t\t\tn += 1;
\t\t}
\t}

\treturn n;
}

// The six slots that can hold a set piece.
@addMethod( W3PlayerWitcher ) function SBT_Slots() : array< EEquipmentSlots >
{
\tvar s : array< EEquipmentSlots >;

\ts.PushBack( EES_Armor );
\ts.PushBack( EES_Boots );
\ts.PushBack( EES_Gloves );
\ts.PushBack( EES_Pants );
\ts.PushBack( EES_SteelSword );
\ts.PushBack( EES_SilverSword );

\treturn s;
}

// Count the worn pieces from scratch instead of trusting a running total.
//
// The counter is a saved field that everything else nudges up and down by one.
// That only stays honest if every increment is matched by a decrement - across
// saves, mod toggles, and other mods that touch equipment. It stopped being
// honest here (a set showed 8 of 6), and a running total that has drifted cannot
// repair itself. Recounting can: it asks the game what is actually worn and
// throws the old number away. Cheap, and it makes the whole class of drift
// impossible rather than fixing one instance of it.
@addMethod( W3PlayerWitcher ) function SBT_Recount() : int
{
\tvar slots : array< EEquipmentSlots >;
\tvar item : SItemUniqueId;
\tvar st : EItemSetType;
\tvar i, found : int;

\tslots = SBT_Slots();

\t// Refuse to touch anything if nothing is readable yet - at load time the
\t// equipment may not be up, and zeroing on an empty read would wipe live bonuses.
\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( GetItemEquippedOnSlot( slots[i], item ) )
\t\t\tfound += 1;
\t}

\tif( found == 0 )
\t\treturn -1;

\tfor( i = 0; i < amountOfSetPiecesEquipped.Size(); i += 1 )
\t\tamountOfSetPiecesEquipped[i] = 0;

\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( !GetItemEquippedOnSlot( slots[i], item ) )
\t\t\tcontinue;

\t\tst = CheckSetType( item );
\t\tif( st != EIST_Undefined )
\t\t\tamountOfSetPiecesEquipped[ st ] += 1;
\t}

\t// Просим игру пересобрать эффекты для КАЖДОГО комплекта, которого мы могли
\t// коснуться. Раньше здесь были перечислены только восемь ведьмачьих школ, и
\t// реликтовые оставались без обслуживания. Теперь — обход по нашим кодам, а
\t// значение перечисления игра выдаёт сама по ярлыку.
\tfor( i = 1; i <= 19; i += 1 )
\t{
\t\tst = SBT_SetTypeForCode( i );
\t\tif( st != EIST_Undefined )
\t\t\tManageActiveSetBonuses( st );
\t}

\treturn found;
}

// ----------------------------------------------------- the price of a stone ---
//
// A school stone costs a WHOLE SET of that school. The set is not burned - it has to
// be OWNED. That requirement lives here rather than in the recipe's ingredient list,
// and not out of laziness: each school exists in 30 items, five tiers across six
// slots, and upgrading consumes the tier below. A recipe naming six exact items would
// describe one combination out of 15625 and would almost never be satisfiable.
//
// Reading the school TAG instead accepts a set of any tier, and touches nothing.

// Из чего состоит «полный комплект» — у каждого свой набор. Не выдумано, а
// пересчитано сплошной проверкой ВСЕХ бандлов игры (research\scan_sets.py):
// content0…content12, все папки dlc и все моды, 555 файлов определений.
//
//   броня + сапоги + перчатки + штаны — есть у всех, это основа;
//   + два меча   — ведьмачьи школы (кроме вампирской), эльфы, тигр;
//   + маска и ТОЛЬКО стальной меч — вампирский и вампирский иной;
//     ⚠️ у вампирского серебряного меча НЕ СУЩЕСТВУЕТ. Пока мы требовали шесть
//     частей у всех подряд, вампирский камень нельзя было скрафтить в принципе;
//   + маска        — готический, диметриевый, метеоритный (доспехи kotw_* из dlcW3EE);
//   ничего сверх основы — темерский, нильфгаардский, скеллигский, офирский, новолуние:
//     мечей у этих пяти нет вовсе.
@addMethod( W3PlayerWitcher ) function SBT_NeedCats( code : int, out cats : array< name > )
{
\tcats.Clear();
\tcats.PushBack( 'armor' );
\tcats.PushBack( 'boots' );
\tcats.PushBack( 'gloves' );
\tcats.PushBack( 'pants' );

\t// Вампирские: маска есть, серебряного меча нет.
\tif( code == 6 || code == 19 )
\t{
\t\tcats.PushBack( 'mask' );
\t\tcats.PushBack( 'steelsword' );
\t\treturn;
\t}

\t// Готический, диметриевый, метеоритный: бонус берётся с ОДНОЙ БРОНИ,
\t// и четырёх вещей достаточно (решение ГД 18.09). Маску в расчёт не
\t// берём сознательно: kotw_helm_vN_1 помечен NoShow,NoDrop и лежит в
\t// сумке только пока шлем включён — требовать её значит требовать
\t// того, чего в инвентаре обычно нет.
\tif( code >= 16 && code <= 18 )
\t\treturn;

\t// Остальные ведьмачьи школы, эльфы и тигр — с обоими мечами.
\tif( code <= 8 || code == 14 || code == 15 )
\t{
\t\tcats.PushBack( 'steelsword' );
\t\tcats.PushBack( 'silversword' );
\t}
}

@addMethod( W3PlayerWitcher ) function SBT_HasFullSet( code : int ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar slots : array< EEquipmentSlots >;
\tvar cats, have : array< name >;
\tvar item : SItemUniqueId;
\tvar tag, cat : name;
\tvar i : int;

\ttag = SBT_TagForCode( code );
\tif( tag == '' )
\t\treturn false;

\titems = inv.GetItemsByTag( tag );

\t// Worn pieces are checked separately: the bag listing has already been caught
\t// once not returning equipped items.
\tslots = SBT_Slots();
\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( GetItemEquippedOnSlot( slots[i], item ) && inv.ItemHasTag( item, tag ) )
\t\t\titems.PushBack( item );
\t}

\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tcat = inv.GetItemCategory( items[i] );
\t\tif( !have.Contains( cat ) )
\t\t\thave.PushBack( cat );
\t}

\tSBT_NeedCats( code, cats );
\tfor( i = 0; i < cats.Size(); i += 1 )
\t{
\t\tif( !have.Contains( cats[i] ) )
\t\t\treturn false;
\t}

\treturn true;
}

// ------------------------------------ штатная проверка: бонус включён? ---
//
// Спрашиваем у игры, активен ли сейчас сетовый бонус, вместо того чтобы
// считать комплектность самим. Две причины, обе измеренные:
//
//  1) порог у Redux — НАСТРОЙКА, а не «шесть предметов»: игра сравнивает
//     счётчик надетого с настраиваемым числом. Наше число с игрой
//     рано или поздно разойдётся;
//  2) у готического, диметриевого и метеоритного комплектов пятая вещь —
//     маска kotw_helm_vN_1 с ярлыками NoShow,NoDrop. Она лежит в сумке
//     ТОЛЬКО пока шлем включён: RemoveHelm выкидывает всё с ярлыком
//     kotwHelm при выключении. Игра это знает и считает шлем отдельным
//     слагаемым; обход сумки — не знает и знать не может.
//
// Соответствие «комплект -> бонус» спрашиваем у самой игры: у грифона и
// змеи ступени перевёрнуты, а у метеорита первой ступени нет вовсе —
// рукописная таблица наступила бы на эти грабли трижды.
@addMethod( W3PlayerWitcher ) function SBT_BonusActive( code : int, high : bool ) : bool
{
\tvar st : EItemSetType;
\tvar bonus : EItemSetBonus;

\tst = SBT_SetTypeForCode( code );
\tif( st == EIST_Undefined )
\t\treturn false;

\tif( high )
\t{
\t\tbonus = ItemSetTypeToItemSetBonus( st, 2 );
\t\tif( bonus == EISB_Undefined )
\t\t\tbonus = ItemSetTypeToItemSetBonus( st, 1 );
\t}
\telse
\t{
\t\tbonus = ItemSetTypeToItemSetBonus( st, 1 );
\t\tif( bonus == EISB_Undefined )
\t\t\tbonus = ItemSetTypeToItemSetBonus( st, 2 );
\t}
\tif( bonus == EISB_Undefined )
\t\treturn false;
\treturn IsSetBonusActive( bonus );
}

// Какой ступени бонуса хватает для ковки: false — бонус просто включён,
// true — полный порог. Одно слово на весь мод, развилка ГД.
@addMethod( W3PlayerWitcher ) function SBT_CraftNeedsHighTier() : bool
{
\treturn false;
}

function SBT_CodeForSchematic( schematicName : name ) : int
{
\tswitch( schematicName )
\t{
\t\tcase 'SBT Runestone Feline schematic':\t\treturn 1;
\t\tcase 'SBT Runestone Griffin schematic':\t\treturn 2;
\t\tcase 'SBT Runestone Ursine schematic':\t\treturn 3;
\t\tcase 'SBT Runestone Wolven schematic':\t\treturn 4;
\t\tcase 'SBT Runestone Manticore schematic':\treturn 5;
\t\tcase 'SBT Runestone Vampire schematic':\t\treturn 6;
\t\tcase 'SBT Runestone Viper schematic':\t\treturn 7;
\t\tcase 'SBT Runestone Netflix schematic':\t\treturn 8;

\t\t// Из дополнения. Все одиннадцать — по комплекту, как и основные восемь.
\t\tcase 'SBT Runestone Temerian schematic':\treturn 9;
\t\tcase 'SBT Runestone Nilfgaard schematic':\treturn 10;
\t\tcase 'SBT Runestone Skellige schematic':\treturn 11;
\t\tcase 'SBT Runestone Ofieri schematic':\t\treturn 12;
\t\tcase 'SBT Runestone NewMoon schematic':\t\treturn 13;
\t\tcase 'SBT Runestone Elven schematic':\t\treturn 14;
\t\tcase 'SBT Runestone Tiger schematic':\t\treturn 15;
\t\tcase 'SBT Runestone Gothic schematic':\t\treturn 16;
\t\tcase 'SBT Runestone Dimeritium schematic':\treturn 17;
\t\tcase 'SBT Runestone Meteorite schematic':\treturn 18;
\t\tcase 'SBT Runestone VampireAlt schematic':\treturn 19;
\t}
\treturn 0;
}

// One hook covers both the crafting list and the craft itself: Craft() asks this
// first (craftingManager.ws:178), so a refusal here greys the recipe out AND blocks
// the attempt. ECE_TooFewIngredients makes the game say what it always says when
// something is missing.
@wrapMethod( W3CraftingManager ) function CanCraftSchematic( schematicName : name, checkMerchant : bool ) : ECraftingException
{
\tvar code : int;
\tvar w : W3PlayerWitcher;

\tcode = SBT_CodeForSchematic( schematicName );
\tif( code > 0 )
\t{
\t\t// ⛔ ОДНА ПЕРЕДАЧА УПРАВЛЕНИЯ ОРИГИНАЛУ НА ОБЁРТКУ: второй такой
\t\t// вызов компилятор не принимает вовсе и валит сборку скриптов.
\t\t// Поэтому не выходим раньше, а просто не судим без игрока.
\t\tw = GetWitcherPlayer();
\t\t// ДВА ПУТИ, достаточно ЛЮБОГО. Штатный — «бонус реально включён»:
\t\t// только он работает для готики, диметрия и метеорита, где маски в
\t\t// сумке не бывает. Запасной — прежняя проверка «комплект на руках»:
\t\t// она пропускает и того, у кого вещи в сумке, а не надеты.
\t\t// Условие только ОСЛАБЛЯЕТСЯ: что куётся сегодня, куётся и завтра.
\t\tif( w && !w.SBT_BonusActive( code, w.SBT_CraftNeedsHighTier() )
\t\t\t&& !w.SBT_HasFullSet( code ) )
\t\t\treturn ECE_TooFewIngredients;
\t}

\treturn wrappedMethod( schematicName, checkMerchant );
}

// Hands over the eight diagrams once per save. The cost of a stone lives in its
// ingredients, not in hunting for the diagram - and a diagram the player can never
// find would make the whole feature invisible.
//
// Guarded by a game FACT: facts survive saves and add nothing to the save format,
// so this stays a one-time gift even across reloads.
@addMethod( W3PlayerWitcher ) function SBT_GrantSchematics()
{
\tvar schems : array< name >;
\tvar i : int;

\tif( !SBT_Bool( 'GrantSchematics', true ) )
\t\treturn;

\t// Список берётся у самой игры, а не зашит здесь: каждый наш чертёж помечен
\t// ярлыком SBT_Schem. Поэтому дополнение с реликтовыми комплектами подхватывается
\t// само, без единой правки в этом файле, — а если его нет, ничего лишнего не выдаётся.
\t// Имя чертежа предмета совпадает с именем чертежа-рецепта, так что склейка строк
\t// не нужна: StringToName в этой сборке отсутствует (сказал компилятор).
\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'SBT_Schem' );

\t// Число вместо «да/нет»: поставили дополнение — чертежей стало больше, чем выдано,
\t// и недостающие приходят при следующей загрузке.
\tif( FactsQuerySum( 'SBT_Schematics' ) >= schems.Size() )
\t\treturn;

\tfor( i = 0; i < schems.Size(); i += 1 )
\t\tAddCraftingSchematic( schems[i], true, true );

\tFactsSet( 'SBT_Schematics', schems.Size() );
}

@wrapMethod( W3PlayerWitcher ) function OnSpawned( spawnData : SEntitySpawnData )
{
\twrappedMethod( spawnData );

\tSBT_didRestore = true;
\tSBT_RestoreAll();
\tSBT_Recount();
\tSBT_GrantSchematics();
}

// ------------------------------------------------------------- the stone ---
//
// The stone rides the game's own dye machinery. A dye is nothing more than an item
// carrying the tag 'mod_dye' (inventoryComponent.ws:3861), and the inventory already
// knows how to take such an item, let the player pick an equipped piece, and act on
// it. That is exactly the interaction this mod needs, complete with slot picking and
// highlighting, so there is no reason to build a menu of our own.
//
// Two things have to be bent, and only two:
//   * OnUseDye offers FOUR armour slots and screens each through CanItemBeColored,
//     which demands quality 5. Riding it unchanged would leave out swords and most
//     armour. So for our stone we build the target list ourselves.
//   * ApplyDye colours the piece and then spends one of the item. For our stone we
//     do neither - it stamps a set instead, and the stone stays.

// Which school does this piece belong to? Read it off the item's TAGS.
//
// Going through CheckSetType looked cleaner and was wrong: Redux splits every school
// into a major and a MINOR variant (EIST_MinorWolf and friends, 30 enum values against
// vanilla's 9), and a piece without the SetBonusPiece tag comes back as the minor one.
// Those names do not exist in vanilla, so matching on them would tie the mod to Redux
// for no good reason. The eight school TAGS are identical in both, and answer the
// question directly - minor or major, it is still wolf gear.
@addMethod( W3PlayerWitcher ) function SBT_CodeFromTags( item : SItemUniqueId ) : int
{
\tif( inv.ItemHasTag( item, 'LynxSet' ) )\t\treturn 1;
\tif( inv.ItemHasTag( item, 'GryphonSet' ) )\treturn 2;
\tif( inv.ItemHasTag( item, 'BearSet' ) )\t\treturn 3;
\tif( inv.ItemHasTag( item, 'WolfSet' ) )\t\treturn 4;
\tif( inv.ItemHasTag( item, 'RedWolfSet' ) )\treturn 5;
\tif( inv.ItemHasTag( item, 'VampireSet' ) )\treturn 6;
\tif( inv.ItemHasTag( item, 'ViperSet' ) )\treturn 7;
\tif( inv.ItemHasTag( item, 'NetflixSet' ) )\treturn 8;

\treturn 0;
}

@addMethod( W3PlayerWitcher ) function SBT_SetName( code : int ) : string
{
\tswitch( code )
\t{
\t\tcase 1:\treturn "Feline";
\t\tcase 2:\treturn "Griffin";
\t\tcase 3:\treturn "Ursine";
\t\tcase 4:\treturn "Wolven";
\t\tcase 5:\treturn "Manticore";
\t\tcase 6:\treturn "Vampire";
\t\tcase 7:\treturn "Viper";
\t\tcase 8:\treturn "Netflix";

\t\tcase  9:\treturn "Temerian";
\t\tcase 10:\treturn "Nilfgaardian";
\t\tcase 11:\treturn "Skellige";
\t\tcase 12:\treturn "Ofieri";
\t\tcase 13:\treturn "New Moon";
\t\tcase 14:\treturn "Elven";
\t\tcase 15:\treturn "Tiger";
\t\tcase 16:\treturn "Gothic";
\t\tcase 17:\treturn "Dimeritium";
\t\tcase 18:\treturn "Meteorite";
\t\tcase 19:\treturn "Vampire (alt)";
\t}
\treturn "empty";
}

// Each stone is a fixed school, written into its own item card as a tag. There is one
// stone per set rather than one stone that learns, which keeps the item honest - what
// it does is visible from its name - and maps one recipe to one stone later on.
@addMethod( W3PlayerWitcher ) function SBT_StoneCode( stone : SItemUniqueId ) : int
{
\tif( inv.ItemHasTag( stone, 'SBT_Lynx' ) )\t\treturn 1;
\tif( inv.ItemHasTag( stone, 'SBT_Gryphon' ) )\treturn 2;
\tif( inv.ItemHasTag( stone, 'SBT_Bear' ) )\t\treturn 3;
\tif( inv.ItemHasTag( stone, 'SBT_Wolf' ) )\t\treturn 4;
\tif( inv.ItemHasTag( stone, 'SBT_RedWolf' ) )\treturn 5;
\tif( inv.ItemHasTag( stone, 'SBT_Vampire' ) )\treturn 6;
\tif( inv.ItemHasTag( stone, 'SBT_Viper' ) )\t\treturn 7;
\tif( inv.ItemHasTag( stone, 'SBT_Netflix' ) )\treturn 8;

\t// Реликтовые комплекты Redux — из дополнения. Если оно не установлено, камней
\t// с этими ярлыками просто нет, и строки ниже никогда не срабатывают.
\tif( inv.ItemHasTag( stone, 'SBT_Temerian' ) )\t\treturn 9;
\tif( inv.ItemHasTag( stone, 'SBT_Nilfgaard' ) )\t\treturn 10;
\tif( inv.ItemHasTag( stone, 'SBT_Skellige' ) )\t\treturn 11;
\tif( inv.ItemHasTag( stone, 'SBT_Ofieri' ) )\t\treturn 12;
\tif( inv.ItemHasTag( stone, 'SBT_NewMoon' ) )\t\treturn 13;
\tif( inv.ItemHasTag( stone, 'SBT_Elven' ) )\t\treturn 14;
\tif( inv.ItemHasTag( stone, 'SBT_Tiger' ) )\t\treturn 15;
\tif( inv.ItemHasTag( stone, 'SBT_Gothic' ) )\t\treturn 16;
\tif( inv.ItemHasTag( stone, 'SBT_Dimeritium' ) )\treturn 17;
\tif( inv.ItemHasTag( stone, 'SBT_Meteorite' ) )\t\treturn 18;
\tif( inv.ItemHasTag( stone, 'SBT_VampireAlt' ) )\treturn 19;

\treturn 0;
}

@addMethod( W3PlayerWitcher ) function SBT_UseStone( stone : SItemUniqueId, target : SItemUniqueId )
{
\tvar code : int;

\t// The cleansing stone is the same kind of tool pointed the other way: it takes a
\t// transferred set back off. A genuine set piece returns to its own school, because
\t// its native tag was never taken away in the first place.
\tif( inv.ItemHasTag( stone, 'SBT_Clean' ) )
\t{
\t\tif( SBT_Remove( target ) )
\t\t\tSBT_Say( "Transferred set bonus removed." );
\t\telse
\t\t\tSBT_Say( "Nothing was transferred onto this piece." );

\t\treturn;
\t}

\tcode = SBT_StoneCode( stone );

\tif( code == 0 )
\t{
\t\tSBT_Say( "This runestone carries no set." );
\t\treturn;
\t}

\tif( SBT_Apply( target, code ) )
\t{
\t\tSBT_Say( "Piece now counts towards the " + SBT_SetName( code ) + " set." );

\t\t// Off by default: the stone is a tool, not a consumable. A player who wants
\t\t// each transfer to cost something can switch this on.
\t\tif( SBT_Bool( 'ConsumeStone', false ) )
\t\t\tinv.RemoveItem( stone, 1 );
\t}
\telse
\t{
\t\tSBT_Say( "That piece already counts towards the " + SBT_SetName( code ) + " set." );
\t}
}

// ⚠️ THE MENU CLASS IS NOT CALLED CR4InventoryMenu HERE.
//
// Both wrappers below were first written against CR4InventoryMenu - the name the
// VANILLA file uses - and the compiler answered:
//
//     Wrap function 'OnUseDye' must wrap an existing function.
//     Wrap function 'ApplyDye' must wrap an existing function.
//
// The signatures were right. The class was not. W3EE ships its own inventoryMenu.ws
// with the Quick Slots mod merged in, and that copy renames the class:
//
//     vanilla : class CR4InventoryMenu    extends CR4MenuBase        (line 42)
//     W3EE    : class WmkCR4InventoryMenu extends CR4MenuBase        (line 41)
//                                         // -= WMK:modQuickSlots =-
//
// So the lesson is not about signatures at all: when a wrapper is refused, check
// that the CLASS still carries that name in the copy of the file that actually wins,
// not in the vanilla one. A merged mod can rename it out from under you.
//
// This does tie the two wrappers below to a W3EE install. A vanilla build of this mod
// has to name CR4InventoryMenu instead - the one place the two versions genuinely
// diverge so far.

@wrapMethod( """ + MENU_CLASS + """ ) function OnUseDye( item : SItemUniqueId, optional isPreview : bool )
{
\tvar targets : array< int >;
\tvar onSlot : SItemUniqueId;
\tvar w : W3PlayerWitcher;

\tw = GetWitcherPlayer();

\tif( w.inv.ItemHasTag( item, 'SBT_Stone' ) )
\t{
\t\t// our own target list: every worn slot, and no CanItemBeColored screen
\t\tif( w.GetItemEquippedOnSlot( EES_Armor, onSlot ) )\t\ttargets.PushBack( EES_Armor );
\t\tif( w.GetItemEquippedOnSlot( EES_Gloves, onSlot ) )\t\ttargets.PushBack( EES_Gloves );
\t\tif( w.GetItemEquippedOnSlot( EES_Pants, onSlot ) )\t\ttargets.PushBack( EES_Pants );
\t\tif( w.GetItemEquippedOnSlot( EES_Boots, onSlot ) )\t\ttargets.PushBack( EES_Boots );
\t\tif( SBT_Bool( 'AllowSwords', true ) )
\t\t{
\t\t\tif( w.GetItemEquippedOnSlot( EES_SteelSword, onSlot ) )\t\ttargets.PushBack( EES_SteelSword );
\t\t\tif( w.GetItemEquippedOnSlot( EES_SilverSword, onSlot ) )\ttargets.PushBack( EES_SilverSword );
\t\t}

\t\tif( targets.Size() > 0 )
\t\t\tShowSelectionMode( item, targets );

\t\t// An event answers with a flag even when the declaration shows no return type,
\t\t// so a bare "return;" here is rejected: "Unable to convert from 'void' to 'Bool'".
\t\treturn true;
\t}

\treturn wrappedMethod( item, isPreview );
}

@wrapMethod( """ + MENU_CLASS + """ ) function ApplyDye( itemId : SItemUniqueId, targetSlot : int ) : void
{
\tvar w : W3PlayerWitcher;
\tvar target : SItemUniqueId;

\tw = GetWitcherPlayer();

\tif( w.inv.ItemHasTag( itemId, 'SBT_Stone' ) )
\t{
\t\tif( w.GetItemEquippedOnSlot( targetSlot, target ) )
\t\t\tw.SBT_UseStone( itemId, target );

\t\t// the original is deliberately not called: no colouring, and no item spent
\t\treturn;
\t}

\twrappedMethod( itemId, targetSlot );
}

// ---------------------------------------------------------------- console ---

// Uses the runestone on a worn piece by slot number, covering what the dye screen
// will not offer: swords, and armour the game refuses to colour.
//   0 armour | 1 boots | 2 gloves | 3 trousers | 4 steel sword | 5 silver sword
// Почему камень не куётся — одной командой: показывает оба пути гейта.
exec function sbtwhy( code : int )
{
\tvar w : W3PlayerWitcher;
\tvar st : EItemSetType;
\tvar msg : string;

\tw = GetWitcherPlayer();
\tif( !w )
\t\treturn;
\tst = w.SBT_SetTypeForCode( code );
\tmsg = "code " + code + " " + w.SBT_SetName( code ) + " type=" + (int)st;
\tmsg = msg + "<br>worn:" + w.GetSetPartsEquipped( st );
\tmsg = msg + "<br>tier1:" + w.SBT_BonusActive( code, false );
\tmsg = msg + "  tier2:" + w.SBT_BonusActive( code, true );
\tmsg = msg + "<br>bagSet:" + w.SBT_HasFullSet( code );
\ttheGame.GetGuiManager().ShowNotification( msg, 20000 );
}

exec function sbtuse( slot : int, code : int )
{
	var w : W3PlayerWitcher;
	var slots : array< EEquipmentSlots >;
	var target : SItemUniqueId;

	w = GetWitcherPlayer();
	if( !w ) return;

	slots = w.SBT_Slots();
	if( slot < 0 || slot >= slots.Size() )
	{
		theGame.GetGuiManager().ShowNotification( "SBT: slot must be 0..5", 6000 );
		return;
	}

	if( !w.GetItemEquippedOnSlot( slots[slot], target ) )
	{
		theGame.GetGuiManager().ShowNotification( "SBT: that slot is empty", 6000 );
		return;
	}

	if( w.SBT_Apply( target, code ) )
		theGame.GetGuiManager().ShowNotification(
			"Piece now counts towards the " + w.SBT_SetName( code ) + " set.", 6000 );
	else
		theGame.GetGuiManager().ShowNotification( "SBT: nothing changed", 6000 );
}

exec function sbtset( code : int )
{
\tvar w : W3PlayerWitcher;
\tvar slots : array< EEquipmentSlots >;
\tvar item : SItemUniqueId;
\tvar i, done, skipped : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tslots.PushBack( EES_Armor );
\tslots.PushBack( EES_Boots );
\tslots.PushBack( EES_Gloves );
\tslots.PushBack( EES_Pants );

\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( w.GetItemEquippedOnSlot( slots[i], item ) )
\t\t{
\t\t\tif( w.SBT_Apply( item, code ) )
\t\t\t\tdone += 1;
\t\t\telse
\t\t\t\tskipped += 1;
\t\t}
\t}

\ttheGame.GetGuiManager().ShowNotification( "SBT: stamped " + done + ", skipped " + skipped
\t\t+ " (bad code, or already that set)", 8000 );
}

// Clears the WORN pieces. Walks the equipment slots directly rather than the whole
// inventory: the first version used GetAllItems and reported "cleared 0" while the
// worn pieces were plainly stamped, so that list is not to be trusted here.
exec function sbtclear()
{
\tvar w : W3PlayerWitcher;
\tvar slots : array< EEquipmentSlots >;
\tvar items : array< SItemUniqueId >;
\tvar item : SItemUniqueId;
\tvar i, done, bag : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tslots = w.SBT_Slots();
\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( w.GetItemEquippedOnSlot( slots[i], item ) )
\t\t{
\t\t\tif( w.SBT_Remove( item ) )
\t\t\t\tdone += 1;
\t\t}
\t}

\t// second sweep over the bag, for anything stamped but not worn
\tw.inv.GetAllItems( items );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( w.SBT_Remove( items[i] ) )
\t\t\tbag += 1;
\t}

\tw.SBT_Recount();

\ttheGame.GetGuiManager().ShowNotification( "SBT: cleared " + done + " worn, " + bag + " in bag", 8000 );
}

// Repairs a drifted counter without changing any stamp.
exec function sbtfix()
{
\tvar w : W3PlayerWitcher;
\tvar n : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tn = w.SBT_Recount();
\ttheGame.GetGuiManager().ShowNotification( "SBT: recounted from " + n + " worn slots", 8000 );
}

// ОПЫТ ДЛЯ КУЗНИЦЫ: сменить ВНЕШНИЙ ВИД надетой вещи на внешность другого предмета.
//   sbtlook(4, 'Cheesecutter')  — стальному мечу дать облик «Эмменталя»
//
// Цепочка целиком собрана из функций самой игры, каждая проверена в этой сборке:
//   inv.GetItemEntityUnsafe( вещь )                 -> сущность вещи (CItemEntity)
//   .GetComponentByClassName('CAppearanceComponent')-> её компонент внешности
//   dm.GetItemEquipTemplate( имя донора )           -> ПУТЬ к модели донора
//   LoadResource( путь, true )                      -> сам шаблон
//   comp.IncludeAppearanceTemplate( шаблон )        -> подмешать чужие внешности
//   GetAppearanceNames2( путь, out имена )          -> как они называются
//   comp.ApplyAppearance( имя )                     -> надеть
//
// Образец рабочего вызова есть в самой игре: damageManagerProcessor.ws меняет облик
// лука на «rigid» ровно через GetItemEntityUnsafe(...).ApplyAppearance(...).
//
// ⚠️ Смена почти наверняка НЕ переживёт снятие вещи и загрузку: сущность создаётся
// заново. Лечится тем же приёмом, что и ярлыки комплектов, — возвращать при загрузке.
exec function sbtlook( slot : int, donor : name )
{
\tvar w : W3PlayerWitcher;
\tvar slots : array< EEquipmentSlots >;
\tvar item : SItemUniqueId;
\tvar ent : CItemEntity;
\tvar comp : CAppearanceComponent;
\tvar tpl : CEntityTemplate;
\tvar names : array< name >;
\tvar path, msg : string;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tslots = w.SBT_Slots();
\tif( slot < 0 || slot >= slots.Size() )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "SBT: slot must be 0..5", 6000 );
\t\treturn;
\t}

\tif( !w.GetItemEquippedOnSlot( slots[slot], item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "SBT: that slot is empty", 6000 );
\t\treturn;
\t}

\tpath = theGame.GetDefinitionsManager().GetItemEquipTemplate( donor );
\tif( path == "" )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "SBT: no equip template for " + donor, 9000 );
\t\treturn;
\t}

\tGetAppearanceNames2( path, names );

\tmsg = "path: " + path + "<br>appearances: " + names.Size();
\tfor( i = 0; i < names.Size() && i < 6; i += 1 )
\t\tmsg = msg + " " + names[i];
\tmsg = msg + "<br>";

\tent = w.inv.GetItemEntityUnsafe( item );
\tif( !ent )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( msg + "NO ENTITY (item not spawned?)", 25000 );
\t\treturn;
\t}

\tcomp = (CAppearanceComponent)ent.GetComponentByClassName( 'CAppearanceComponent' );
\tif( !comp )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( msg + "NO APPEARANCE COMPONENT", 25000 );
\t\treturn;
\t}

\ttpl = (CEntityTemplate)LoadResource( path, true );
\tif( !tpl )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( msg + "TEMPLATE DID NOT LOAD", 25000 );
\t\treturn;
\t}

\tcomp.IncludeAppearanceTemplate( tpl );

\tif( names.Size() > 0 )
\t\tcomp.ApplyAppearance( NameToString( names[0] ) );

\ttheGame.GetGuiManager().ShowNotification( msg + "APPLIED - look at the weapon", 25000 );
}

// Разведка для будущей кузницы: показывает СВОЙСТВА надетой вещи.
//   sbtabil(0) — броня, 1 сапоги, 2 перчатки, 3 штаны, 4 стальной меч, 5 серебряный
// Уникальная строка реликта («шанс создать взрывное облако») — это свойство, а не
// число в карточке. Если оно видно здесь, значит его можно снять и перевесить тем
// же приёмом, что уже работает с комплектами.
exec function sbtabil( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar slots : array< EEquipmentSlots >;
\tvar abilities : array< name >;
\tvar item : SItemUniqueId;
\tvar msg : string;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tslots = w.SBT_Slots();
\tif( slot < 0 || slot >= slots.Size() )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "SBT: slot must be 0..5", 6000 );
\t\treturn;
\t}

\tif( !w.GetItemEquippedOnSlot( slots[slot], item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "SBT: that slot is empty", 6000 );
\t\treturn;
\t}

\tw.inv.GetItemAbilities( item, abilities );
\tmsg = "" + w.inv.GetItemName( item ) + " - " + abilities.Size() + " abilities<br>";
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tmsg = msg + abilities[i] + "  ";
\t\tif( ( i + 1 ) % 3 == 0 )
\t\t\tmsg = msg + "<br>";
\t}

\ttheGame.GetGuiManager().ShowNotification( msg, 30000 );
}

// Проверяет САМУ ТАБЛИЦУ ЯРЛЫКОВ: для каждого нашего кода спрашивает у игры, какой
// это комплект. Ноль означает, что ярлык записан с опечаткой или такого комплекта в
// этой сборке нет. Одна команда вместо захода в игру на каждую догадку.
exec function sbtsets()
{
\tvar w : W3PlayerWitcher;
\tvar msg : string;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tfor( i = 1; i <= 19; i += 1 )
\t{
\t\tmsg = msg + i + "=" + (int)w.SBT_SetTypeForCode( i ) + " ";
\t\tif( i == 8 || i == 13 )
\t\t\tmsg = msg + "<br>";
\t}

\ttheGame.GetGuiManager().ShowNotification( msg, 25000 );
}

// Shows the real state slot by slot, so a puzzle becomes data.
exec function sbtdiag()
{
\tvar w : W3PlayerWitcher;
\tvar slots : array< EEquipmentSlots >;
\tvar item : SItemUniqueId;
\tvar msg : string;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tslots = w.SBT_Slots();
\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( w.GetItemEquippedOnSlot( slots[i], item ) )
\t\t{
\t\t\tmsg = msg + "slot" + i + ": stamp=" + w.SBT_GetCode( item );
\t\t\tmsg = msg + " type=" + (int)w.CheckSetType( item );
\t\t\tmsg = msg + " isSet=" + w.inv.IsItemSetItem( item ) + "<br>";
\t\t}
\t\telse
\t\t{
\t\t\tmsg = msg + "slot" + i + ": empty<br>";
\t\t}
\t}

\ttheGame.GetGuiManager().ShowNotification( msg, 20000 );
}

exec function sbtinfo()
{
\tvar w : W3PlayerWitcher;
\tvar items : array< SItemUniqueId >;
\tvar i, stamped : int;
\tvar msg : string;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tw.inv.GetAllItems( items );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( w.SBT_GetCode( items[i] ) > 0 )
\t\t\tstamped += 1;
\t}

\tmsg = "SBT v4  stamped:" + stamped;
\tmsg = msg + "  restoredOnLoad:" + w.SBT_didRestore;
\tmsg = msg + "<br>Gryphon:" + w.GetSetPartsEquipped( EIST_Gryphon );
\tmsg = msg + "  Wolf:" + w.GetSetPartsEquipped( EIST_Wolf );
\tmsg = msg + "  Bear:" + w.GetSetPartsEquipped( EIST_Bear );
\tmsg = msg + "  Cat:" + w.GetSetPartsEquipped( EIST_Lynx );
\tmsg = msg + "<br>need minor:" + theGame.params.ITEMS_REQUIRED_FOR_MINOR_SET_BONUS;
\tmsg = msg + "  major:" + theGame.params.ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS;

\ttheGame.GetGuiManager().ShowNotification( msg, 12000 );
}
"""


def say(s=""):
    print(s, flush=True)


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq witcher3.exe"],
                             capture_output=True, text=True, timeout=25).stdout
        return "witcher3.exe" in out.lower()
    except Exception:
        return False


say("=" * 66)
say("  modSetBonusTransfer — ядро")
say("=" * 66)

if "\\t" in WS:
    raise SystemExit("в коде остались буквальные обратные слэши — не записываю")

if game_running():
    say("   игра запущена — .ws подхватится при следующем старте")

target = DIST if VANILLA else MOD
d = os.path.join(target, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "SetBonusTransfer.ws")
data = WS.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
say("   [ok] SetBonusTransfer.ws  %d Б  UTF-16 LE + BOM  (табуляций: %d)"
    % (len(data), WS.count("\t")))
say("   [ok] класс окна инвентаря: %s" % MENU_CLASS)

if VANILLA:
    say()
    say("   ВАНИЛЬНАЯ СБОРКА — в игру НЕ поставлена, лежит здесь:")
    say("     %s" % DIST)
    say()
    say("   ⚠️ В ЭТОЙ установке её проверить НЕЛЬЗЯ: тут стоит Redux, класса")
    say("      CR4InventoryMenu в нём нет, мод не скомпилируется.")
    say("      Проверять только на чистой игре без W3EE.")
    say()
    say("   Предметы к ней собираются как обычно — карточки от сборки не зависят.")
    sys.exit(0)

# регистрация
ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read().decode("utf-8", "replace")
if not os.path.exists(ms + ".bak_setbonus"):
    shutil.copyfile(ms, ms + ".bak_setbonus")
if "[modSetBonusTransfer]" in raw:
    say("   [--] уже прописан в mods.settings")
else:
    raw = raw.rstrip("\r\n") + "\r\n[modSetBonusTransfer]\r\nEnabled=1\r\nPriority=%d\r\n" % PRIORITY
    open(ms, "wb").write(raw.encode("utf-8"))
    say("   [ok] прописан в mods.settings, Priority=%d" % PRIORITY)

say()
say("  КОДЫ КОМПЛЕКТОВ")
for code, name, tag, human in SETS:
    say("     %d  %-9s %-12s %s" % (code, name, tag, human))

say()
say("  ПРОВЕРКА В ИГРЕ — теперь на НАСТОЯЩЕЙ комплектной броне")
say("     Наденьте волчий (или любой школьный) комплект целиком.")
say("     1. sbtinfo()      -> 'SBT v3' и Wolf:4")
say("     2. sbtset(2)      -> 'stamped 4, skipped 0'")
say("     3. sbtinfo()      -> ГЛАВНОЕ: Gryphon:4 И Wolf:0")
say("        волчий счётчик должен ОБНУЛИТЬСЯ, а не остаться 4")
say("     4. Окно умений    -> появился бонус комплекта Грифона")
say("     5. Сохраниться, выйти в меню, загрузиться")
say("     6. sbtinfo()      -> restoredOnLoad:true, Gryphon по-прежнему 4")
say("     7. Снять и надеть кирасу -> Gryphon 4 -> 3 -> 4")
say("     8. sbtclear()     -> Gryphon:0, а Wolf ВЕРНУЛСЯ в 4")
