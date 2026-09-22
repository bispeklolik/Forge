# -*- coding: utf-8 -*-
"""
КУЗНИЦА, ядро (этапы 1-2) — мод modForgeLab.

Этап 1 (проверен в игре): свойства переносятся; уникальный эффект реликта — бафф
(топор выдал облако Эмменталя по ffxon(10)).

Этап 2 (это ядро): ЖЕРТВА и ДЕТАЛИ.
  frgsplit('Имя')            разобрать вещь ИЗ СУМКИ на детали, вещь уничтожается,
                             цена 1 монета (настройкой станет на этапе окна)
  frgparts()                 список деталей в сумке
  frgapply('Имя', слот, вид) применить деталь на надетую вещь; деталь тратится
  fstat/fbag/fcopy/fadd/fdel/ffxon/ffxoff — лаборатория этапа 1, остаётся

ВИДЫ ДЕТАЛЕЙ (число FRG_Part на копии предмета-донора):
  1 облик     жетон на этап 3 (применение пока не открыто)
  2 урон      стопки autogen_fixed_*_dmg; счётчики хранятся ЧИСЛАМИ (FRG_St/FRG_Sv),
              потому что свежая копия донора роллит СВОИ стопки — числа честнее
  3 проценты  все не-autogen свойства; деталь = копия донора, свойства с её карточки
              ≈ донорским (задокументированное допущение: экземплярные наросты
              поверх карточки в деталь процентов не попадают)
  4 эффект    код баффа (FRG_Fx), взят по ярлыку КАРТОЧКИ донора

ПРАВИЛА: мечи перекрёстно (сталь↔серебро, слоты 4/5); проценты можно и на броню
в свой слот; эффект — только на меч БЕЗ собственного эффекта; квестовое не
разбирается. Эффект живёт баффом ОБНАЖЁННОГО меча (как у самой Redux): обёртка
HandleRelicAbilities сидит в воронке холстера, FRG_FxRefresh держит ровно один
живой бафф, OnSpawned возвращает его после загрузки только мечу в руке.

⚠️ .ws в UTF-16 LE + BOM, ТАБЫ, БЕЗ кириллицы.
"""
import os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines_data import (LINES, CUT, TOKEN_ITEM, LINE_LIMIT_BASE, LINE_LIMIT_MAX,
                        TEMPER, DMG_MARKS, FLAT, flat_ability, stat_text,
                        ARMOR, armor_ability, armor_res_ability,
                        ARMOR_LINES, ARMOR_TIER_PENALTY)

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
MOD = os.path.join(GAME, "mods", "modForgeLab")
PRIORITY = 20

WS = """// modForgeLab - forge core, stages 1-2. Console commands only.
//
// STAGE 1 (proven in game): instance abilities transfer; a relic's unique
// effect is a BUFF - the axe produced Emmental's gas cloud via ffxon(10).
//
// STAGE 2 (this): SACRIFICE and PARTS. An item from the bag is split into part
// tokens (copies of the donor marked with numbers), the original is destroyed.
// Parts are applied to worn items and are consumed.
//
// PART KINDS (FRG_Part modifier on the token):
//   1 look    stage 3 placeholder
//   2 damage  autogen_fixed_* stacks, stored as COUNTS (FRG_St / FRG_Sv):
//             a fresh copy of the donor rolls ITS OWN stacks, numbers are honest
//   3 percents non-autogen abilities; token IS a copy of the donor, so its card
//             abilities ~= the donor's (instance-only extras are not captured)
//   4 effect  buff code (FRG_Fx) taken from the donor CARD tag
//
// RULES: swords cross-transfer (slots 4/5, steel<->silver); percents may also
// go armour->same slot; effect only onto a sword WITHOUT its own effect; quest
// items refuse to split. The effect buff belongs to the DRAWN sword, the way
// W3EE does it: a wrap of HandleRelicAbilities rides the holster funnel,
// FRG_FxRefresh keeps exactly one buff alive, OnSpawned re-arms the blade in
// hand after a load (and stamps the tag-gated charms back onto both blades).
//
// SLOTS  0 armor | 1 boots | 2 gloves | 3 trousers | 4 steel | 5 silver

@addMethod( W3PlayerWitcher ) function FRG_Slot( slot : int, out item : SItemUniqueId ) : bool
{
\tvar slots : array< EEquipmentSlots >;

\tslots.PushBack( EES_Armor );
\tslots.PushBack( EES_Boots );
\tslots.PushBack( EES_Gloves );
\tslots.PushBack( EES_Pants );
\tslots.PushBack( EES_SteelSword );
\tslots.PushBack( EES_SilverSword );

\tif( slot < 0 || slot >= slots.Size() )
\t\treturn false;

\treturn GetItemEquippedOnSlot( slots[slot], item );
}

// Finds a WORK TARGET by card name: the bag first, then whatever is worn.
// Engraving, upgrades, marks and naming all modify a LIVING instance - the
// player naturally keeps the blade equipped, and that must just work.
@addMethod( W3PlayerWitcher ) function FRG_FindForWork( wanted : name, out item : SItemUniqueId ) : bool
{
\tvar slots : array< EEquipmentSlots >;
\tvar worn : SItemUniqueId;
\tvar i : int;

\tif( FRG_FindInBag( wanted, item ) )
\t\treturn true;
\tfor( i = 0; i <= 5; i += 1 )
\t{
\t\tif( FRG_Slot( i, worn ) && inv.GetItemName( worn ) == wanted )
\t\t{
\t\t\titem = worn;
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

@addMethod( W3PlayerWitcher ) function FRG_FindInBag( donor : name, out item : SItemUniqueId ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar i : int;

\titems = inv.GetItemsByName( donor );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\t// FRG_Part == 0 keeps tokens out: they are copies of the donor, and a
\t\t// second frgsplit would otherwise sacrifice a TOKEN instead of the item.
\t\tif( inv.IsIdValid( items[i] ) && !IsItemEquipped( items[i] )
\t\t\t&& inv.GetItemModifierInt( items[i], 'FRG_Part', 0 ) == 0 )
\t\t{
\t\t\titem = items[i];
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

// The forge accepts a blank the player is WEARING: it is unequipped and
// used. Without this a blank tried on for size read as "not in the bag".
@addMethod( W3PlayerWitcher ) function FRG_TakeForForge( donor : name, out item : SItemUniqueId ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar i : int;

\tif( FRG_FindInBag( donor, item ) )
\t\treturn true;
\titems = inv.GetItemsByName( donor );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( !inv.IsIdValid( items[i] )
\t\t\t|| inv.GetItemModifierInt( items[i], 'FRG_Part', 0 ) != 0 )
\t\t\tcontinue;
\t\tif( IsItemEquipped( items[i] ) )
\t\t\tUnequipItem( items[i] );
\t\titem = items[i];
\t\treturn true;
\t}
\treturn false;
}

// Finds a PART token in the bag: same donor name AND the requested kind.
@addMethod( W3PlayerWitcher ) function FRG_FindPart( donor : name, kind : int, out item : SItemUniqueId ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar i : int;

\titems = inv.GetItemsByName( donor );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\t// !IsItemEquipped is vital: the token is a COPY of the donor and shares its
\t\t// name, so a donor-named item worn right now could be picked as the token
\t\t// and then destroyed by RemoveItem at the end of the transfer.
\t\tif( inv.IsIdValid( items[i] ) && !IsItemEquipped( items[i] )
\t\t\t&& inv.GetItemModifierInt( items[i], 'FRG_Part', 0 ) == kind )
\t\t{
\t\t\titem = items[i];
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

@addMethod( W3PlayerWitcher ) function FRG_Describe( item : SItemUniqueId ) : string
{
\tvar abilities, seen : array< name >;
\tvar counts : array< int >;
\tvar msg : string;
\tvar i, j : int;
\tvar found : bool;

\tinv.GetItemAbilities( item, abilities );

\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tfound = false;
\t\tfor( j = 0; j < seen.Size(); j += 1 )
\t\t{
\t\t\tif( seen[j] == abilities[i] )
\t\t\t{
\t\t\t\tcounts[j] += 1;
\t\t\t\tfound = true;
\t\t\t\tbreak;
\t\t\t}
\t\t}
\t\tif( !found )
\t\t{
\t\t\tseen.PushBack( abilities[i] );
\t\t\tcounts.PushBack( 1 );
\t\t}
\t}

\tmsg = "" + inv.GetItemName( item ) + " - " + abilities.Size() + " abilities, "
\t\t+ seen.Size() + " distinct<br>";
\tfor( i = 0; i < seen.Size(); i += 1 )
\t{
\t\tmsg = msg + seen[i];
\t\tif( counts[i] > 1 )
\t\t\tmsg = msg + " x" + counts[i];
\t\tmsg = msg + "<br>";
\t}
\treturn msg;
}

// ------------------------------------------------------------ effects ---

@addMethod( W3PlayerWitcher ) function FRG_FxType( code : int ) : EEffectType
{
\tswitch( code )
\t{
\t\tcase 1:\treturn EET_SwordCritVigor;
\t\tcase 2:\treturn EET_SwordRendBlast;
\t\tcase 3:\treturn EET_SwordInjuryHeal;
\t\tcase 4:\treturn EET_SwordDancing;
\t\tcase 5:\treturn EET_SwordQuen;
\t\tcase 6:\treturn EET_SwordWraithbane;
\t\tcase 7:\treturn EET_SwordBloodFrenzy;
\t\tcase 8:\treturn EET_SwordKillBuff;
\t\tcase 9:\treturn EET_SwordBehead;
\t\tcase 10:\treturn EET_SwordGas;
\t\tcase 11:\treturn EET_SwordSignDancer;
\t\tcase 12:\treturn EET_SwordReachoftheDamned;
\t\tcase 13:\treturn EET_SwordDarkCurse;
\t\tcase 14:\treturn EET_SwordDesperateAct;
\t\tcase 15:\treturn EET_SwordRedTear;
\t}
\treturn EET_Undefined;
}

// Effect code of an item CARD (definition tags), 0 if none.
@addMethod( W3PlayerWitcher ) function FRG_FxCodeOf( itemName : name ) : int
{
\tvar dm : CDefinitionsManagerAccessor;

\tdm = theGame.GetDefinitionsManager();
\tif( dm.ItemHasTag( itemName, 'SwordCritVigorEffect' ) )\t\treturn 1;
\tif( dm.ItemHasTag( itemName, 'SwordRendBlastEffect' ) )\t\treturn 2;
\tif( dm.ItemHasTag( itemName, 'SwordInjuryHealEffect' ) )\treturn 3;
\tif( dm.ItemHasTag( itemName, 'SwordDancingEffect' ) )\t\treturn 4;
\tif( dm.ItemHasTag( itemName, 'SwordQuenEffect' ) )\t\t\treturn 5;
\tif( dm.ItemHasTag( itemName, 'SwordWraithbaneEffect' ) )\treturn 6;
\tif( dm.ItemHasTag( itemName, 'SwordBloodFrenzyEffect' ) )\treturn 7;
\tif( dm.ItemHasTag( itemName, 'SwordKillBuffEffect' ) )\t\treturn 8;
\tif( dm.ItemHasTag( itemName, 'SwordBeheadEffect' ) )\t\treturn 9;
\tif( dm.ItemHasTag( itemName, 'SwordGasEffect' ) )\t\t\treturn 10;
\tif( dm.ItemHasTag( itemName, 'SwordSignDancerEffect' ) )\treturn 11;
\tif( dm.ItemHasTag( itemName, 'SwordReachoftheDamnedEffect' ) )\treturn 12;
\tif( dm.ItemHasTag( itemName, 'SwordDarkCurseEffect' ) )\t\treturn 13;
\tif( dm.ItemHasTag( itemName, 'SwordDesperateActEffect' ) )\treturn 14;
\tif( dm.ItemHasTag( itemName, 'SwordRedTearEffect' ) )\t\treturn 15;
\treturn 0;
}

// Effect code -> the CARD tag it came from. Mirror of FRG_FxCodeOf.
@addMethod( W3PlayerWitcher ) function FRG_FxTag( code : int ) : name
{
\tswitch( code )
\t{
\t\tcase 1:\treturn 'SwordCritVigorEffect';
\t\tcase 2:\treturn 'SwordRendBlastEffect';
\t\tcase 3:\treturn 'SwordInjuryHealEffect';
\t\tcase 4:\treturn 'SwordDancingEffect';
\t\tcase 5:\treturn 'SwordQuenEffect';
\t\tcase 6:\treturn 'SwordWraithbaneEffect';
\t\tcase 7:\treturn 'SwordBloodFrenzyEffect';
\t\tcase 8:\treturn 'SwordKillBuffEffect';
\t\tcase 9:\treturn 'SwordBeheadEffect';
\t\tcase 10:\treturn 'SwordGasEffect';
\t\tcase 11:\treturn 'SwordSignDancerEffect';
\t\tcase 12:\treturn 'SwordReachoftheDamnedEffect';
\t\tcase 13:\treturn 'SwordDarkCurseEffect';
\t\tcase 14:\treturn 'SwordDesperateActEffect';
\t\tcase 15:\treturn 'SwordRedTearEffect';
\t}
\treturn '';
}

// The red tooltip line for a transferred effect. W3EE's own text builder
// (GetRelicAbilityDescription) works off a card NAME, not an instance - so we
// hand it any card that carries the same effect tag and let it do the words,
// colors and parameter substitution itself. Zero duplicated text.
@addMethod( W3PlayerWitcher ) function FRG_FxRedLine( fx : int ) : string
{
\tvar dm : CDefinitionsManagerAccessor;
\tvar reps : array< name >;
\tvar tag : name;
\tvar s : string;
\tvar i : int;

\ttag = FRG_FxTag( fx );
\tif( tag == '' )
\t\treturn "";

\tdm = theGame.GetDefinitionsManager();
\treps = dm.GetItemsWithTag( tag );
\tfor( i = 0; i < reps.Size(); i += 1 )
\t{
\t\t// the builder answers "" for non-weapons, so probe until it speaks
\t\ts = Equipment().GetRelicAbilityDescription( reps[i] );
\t\tif( s != "" )
\t\t\treturn s;
\t}
\treturn "";
}

// Tooltip: an item wearing a transferred effect (FRG_Fx) gets the same red
// description line a genuine relic shows. Appended AFTER the original builder,
// reading the assembled text back off the flash object.
@wrapMethod( W3TooltipComponent ) function GetBaseItemData( item : SItemUniqueId, itemInvComponent : CInventoryComponent, optional isShopItem : bool, optional compareWithItem : SItemUniqueId, optional compareItemInv : CInventoryComponent ) : CScriptedFlashObject
{
\tvar o : CScriptedFlashObject;
\tvar w : W3PlayerWitcher;
\tvar line, cur : string;
\tvar fx : int;

\to = wrappedMethod( item, itemInvComponent, isShopItem, compareWithItem, compareItemInv );

\t// a LINE TOKEN describes its line right in the tooltip
\tif( itemInvComponent.GetItemModifierInt( item, 'FRG_Part', 0 ) == 5 )
\t{
\t\tfx = itemInvComponent.GetItemModifierInt( item, 'FRG_Line', 0 );
\t\tif( fx > 0 )
\t\t{
\t\t\tline = "<font color='#ca610c'>" + FRGL_Stats( fx );
\t\t\tif( FRGL_IsJunk( fx ) )
\t\t\t\tline = line + " " + GetLocStringByKeyExt( "frgu_b_junk" );
\t\t\tif( FRGL_IsRelic( fx ) )
\t\t\t\tline = line + " " + GetLocStringByKeyExt( "frgu_b_relic" );
\t\t\tline = line + "</font>";
\t\t\tcur = o.GetMemberFlashString( "Description" );
\t\t\tif( cur != "" )
\t\t\t\tline = line + "<br>" + cur;
\t\t\to.SetMemberFlashString( "Description", line );
\t\t}
\t\treturn o;
\t}

\t// the tooltip picture follows the mounted look too ("IconPath", capital I)
\tfx = itemInvComponent.GetItemModifierInt( item, 'FRG_Look', 0 );
\tw = GetWitcherPlayer();
\tif( fx > 0 && w )
\t{
\t\tline = w.FRG_LookRead( "frg_icon_", fx );
\t\tif( line != "" )
\t\t\to.SetMemberFlashString( "IconPath", line );
\t}

\t// the blade's NAME replaces the label INSIDE the rarity color tags
\tif( w && itemInvComponent.ItemHasTag( item, 'FRG_Forge' ) )
\t{
\t\tline = w.FRGN_NameOf( item );
\t\tif( line != "" )
\t\t{
\t\t\tcur = o.GetMemberFlashString( "ItemName" );
\t\t\tfx = StrFindFirst( cur, ">" );
\t\t\tif( fx >= 0 && StrFindFirst( cur, "<font" ) == 0 )
\t\t\t\to.SetMemberFlashString( "ItemName", StrLeft( cur, fx + 1 ) + line + "</font>" );
\t\t\telse
\t\t\t\to.SetMemberFlashString( "ItemName", line );
\t\t}
\t}

\tfx = itemInvComponent.GetItemModifierInt( item, 'FRG_Fx', 0 );
\tif( fx > 0 && w )
\t{
\t\tline = w.FRG_FxRedLine( fx );
\t\tif( line != "" )
\t\t{
\t\t\tcur = o.GetMemberFlashString( "Description" );
\t\t\tif( cur != "" )
\t\t\t\tline = line + "<br>" + cur;
\t\t\to.SetMemberFlashString( "Description", line );
\t\t}
\t}
\treturn o;
}

// ------------------------------------------------- charm: ONE blade at a time
// W3EE keeps exactly ONE charm buff alive - the one of the DRAWN sword.
// WeaponHolster.SetCurrentMeleWeapon (playerWeaponHolster.ws:70-94) takes the
// buff off the old blade (:80) and hangs it on the new one (:91); putting a
// second sword into a SLOT hangs nothing, because HandleRelicAbilities is
// never called with equip=true from anywhere else (the only other caller is
// playerWitcher.ws:7152, and that one passes false). Hanging a buff per SLOT
// was our own invention, and it is why the silver blade's cloud kept firing
// while the player was fighting with steel.
@addMethod( W3PlayerWitcher ) function FRG_FxHeldSlot() : int
{
\tif( GetCurrentMeleeWeaponType() == PW_Steel )
\t\treturn 4;
\tif( GetCurrentMeleeWeaponType() == PW_Silver )
\t\treturn 5;
\treturn -1;
}

// The ONLY place outside the W3EE funnel allowed to write charm buffs: wipes
// every charm buff carrying our source and hangs back the single one the
// blade IN HAND deserves. Idempotent - safe to call as often as we like, and
// it also sweeps buffs that stuck to old saves.
@addMethod( W3PlayerWitcher ) function FRG_FxRefresh()
{
\tvar held : SItemUniqueId;
\tvar fx, k, i : int;

\tfor( i = 1; i <= 15; i += 1 )
\t\tRemoveBuff( FRG_FxType( i ), false, "RelicWeaponBuff" );

\tk = FRG_FxHeldSlot();
\tif( k < 0 || !FRG_Slot( k, held ) )
\t\treturn;\t// nothing drawn - the holster will hang it on unsheathe

\tfx = inv.GetItemModifierInt( held, 'FRG_Fx', 0 );
\tif( fx <= 0 )
\t\tfx = FRG_FxCodeOf( inv.GetItemName( held ) );\t// the blade's own charm
\tif( fx > 0 )
\t\tAddEffectDefault( FRG_FxType( fx ), this, "RelicWeaponBuff", false );
}

// Two charms are NOT gated by the buff alone - W3EE reads a TAG off the blade
// in hand: 'SwordDancingEffect' in playerWitcher.ws:3555 (the quick/heavy
// alternation bonus, the +15% is counted in damageManagerProcessor.ws:1474)
// 'SwordRendBlastEffect' in damageManagerProcessor.ws:2816 (the dismembering
// half of RendBlast). A number on the instance cannot satisfy that gate, so
// for those two the tag itself is stamped ON THE INSTANCE, exactly the way a
// genuine relic carries it on its card.
@addMethod( W3PlayerWitcher ) function FRG_FxTagged( code : int ) : bool
{
\treturn code == 2 || code == 4;
}

// Brings one blade's instance tags in line with its FRG_Fx: our tag on, tags
// of charms it no longer carries off. A tag that comes from the CARD is the
// blade's own and is never stripped - only what WE stamped.
@addMethod( W3PlayerWitcher ) function FRG_FxStamp( item : SItemUniqueId )
{
\tvar tag : name;
\tvar fx, i : int;

\tif( !inv.IsIdValid( item ) )
\t\treturn;

\tfx = inv.GetItemModifierInt( item, 'FRG_Fx', 0 );
\tfor( i = 1; i <= 15; i += 1 )
\t{
\t\tif( !FRG_FxTagged( i ) || i == fx )
\t\t\tcontinue;
\t\ttag = FRG_FxTag( i );
\t\tif( inv.ItemHasTag( item, tag ) && FRG_FxCodeOf( inv.GetItemName( item ) ) != i )
\t\t\tinv.RemoveItemTag( item, tag );
\t}
\tif( fx > 0 && FRG_FxTagged( fx ) && !inv.ItemHasTag( item, FRG_FxTag( fx ) ) )
\t\tinv.AddItemTag( item, FRG_FxTag( fx ) );
}

// The transferred effect lives as a buff and must follow equip state. W3EE has
// exactly one funnel for that - the same one it uses for genuine relics.
@wrapMethod( W3EEEquipmentHandler ) function HandleRelicAbilities( witcher : W3PlayerWitcher, item : SItemUniqueId, equip : bool )
{
\tvar fx, lookSlot, native : int;
\tvar cat : name;
\tvar fxCarrier : SItemUniqueId;

\twrappedMethod( witcher, item, equip );

\t// A sword swap tears down the item entity the fake look hangs on. Drop
\t// the fake on unequip; on equip re-mount after the game settles.
\tcat = witcher.inv.GetItemCategory( item );
\tlookSlot = -1;
\tif( cat == 'steelsword' )
\t\tlookSlot = 4;
\tif( cat == 'silversword' )
\t\tlookSlot = 5;
\tif( lookSlot >= 0 && witcher.inv.GetItemModifierInt( item, 'FRG_Look', 0 ) > 0 )
\t{
\t\tif( equip )
\t\t\twitcher.AddTimer( 'FRG_LookRestore', 0.5, false );
\t\telse
\t\t\twitcher.FRG_DropLookEnt( lookSlot );
\t}
\t// ⛔ Снятие носителя ПЕРЕЕХАЛО в свой хук на UnequipItemFromSlot
\t// (17.09). Здесь оно срабатывало за 80 строк ДО того, как игра
\t// уберёт вещь и очистит слот: мы дёргали предмет из слота, для
\t// игры ещё занятого, и картинка собиралась битой.

\tif( !witcher )
\t\treturn;

\tfx = witcher.inv.GetItemModifierInt( item, 'FRG_Fx', 0 );
\tif( fx <= 0 )
\t\treturn;

\t// OUR charm REPLACES the blade's own (user 13.09). The native one is a
\t// card tag and cannot be erased, but the original call above has just
\t// hung its buff - so we take that one down and hang ours instead.
\tnative = witcher.FRG_FxCodeOf( witcher.inv.GetItemName( item ) );
\tif( native > 0 && native != fx )
\t\twitcher.RemoveBuff( witcher.FRG_FxType( native ), false, "RelicWeaponBuff" );

\t// remove-then-add, always: for a TAGGED charm (2, 4) the original call
\t// above has just hung the very same buff off our instance tag, and two
\t// AddEffectDefault of one type+source must not stack.
\twitcher.RemoveBuff( witcher.FRG_FxType( fx ), false, "RelicWeaponBuff" );
\tif( equip )
\t\twitcher.AddEffectDefault( witcher.FRG_FxType( fx ), witcher, "RelicWeaponBuff", false );
}

// Buffs do not survive a load; the numbers on the items do. Re-arm on spawn -
// for the blade IN HAND only. The old two-slot loop armed BOTH swords at once
// and left the sheathed one's charm firing forever (GD report 17.09): holster
// only ever takes down the buff of the blade written in its own saved
// currentWeaponID, so the second one had nobody to remove it.
@wrapMethod( W3PlayerWitcher ) function OnSpawned( spawnData : SEntitySpawnData )
{
\tvar item : SItemUniqueId;
\tvar s : int;

\twrappedMethod( spawnData );

\tfor( s = 4; s <= 5; s += 1 )
\t{
\t\tif( FRG_Slot( s, item ) )
\t\t\tFRG_FxStamp( item );
\t}
\tFRG_FxRefresh();

\tFRG_GrantSchematics();
\tFRG_MigrateForged();
\tFRG_ReclaimLost();

\t// Item entities are not ready right at spawn - AMM waits 2 seconds too.
\tAddTimer( 'FRG_LookRestore', 2.0, false );
}

// Diagrams are taught on EVERY spawn, found by TAG so the DLC stays optional.
// No count guard: AddCraftingSchematic is idempotent (it rejects duplicates
// itself, playerWitcher.ws:4536), and a size-based guard already misfired once
// when one diagram replaced another and the total stayed the same - the new
// ForgeBlade schematic was silently never taught.
@addMethod( W3PlayerWitcher ) function FRG_GrantSchematics()
{
\tvar schems : array< name >;
\tvar i : int;

\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'FRG_Schem' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t\tAddCraftingSchematic( schems[i], true, true );

\t// the "native look" mark: an eternal pointer for the look square of the
\t// armour reskin recipes. The ring has no empty position (the vanilla walker
\t// steps over the placeholder - nothing of that name is in the bag), so
\t// going back to the native look needs a THING to scroll to (user 13.09).
\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'FRG_Native' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t{
\t\tif( inv.GetItemQuantityByName( schems[i] ) <= 0 )
\t\t\tinv.AddAnItem( schems[i], 1 );
\t}

\t// the four mark stamps are eternal pointers - handed out once
\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'FRG_Stamp' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t{
\t\tif( inv.GetItemQuantityByName( schems[i] ) <= 0 )
\t\t\tinv.AddAnItem( schems[i], 1 );
\t}
\t// blade CHARACTERS are NOT handed out (GD call 25.08: "too strong, they
\t// should be found and taken off real weapons"). They stay in the registry
\t// at full Redux strength, but every one of them costs a sacrifice.
\t// flaw marks: a price list, not loot - the player picks WHAT to pay with.
\t// Handed out FROM THE REGISTRY (not by tag): DLC tag indexing proved
\t// unreliable here, while FRGF_TokCard is generated from our own data.
\ti = 1;
\twhile( i <= FRGF_Count() )
\t{
\t\tif( inv.GetItemQuantityByName( FRGF_TokCard( FRGF_IdAt( i ) ) ) <= 0 )
\t\t\tinv.AddAnItem( FRGF_TokCard( FRGF_IdAt( i ) ), 1 );
\t\ti += 1;
\t}
\t// naming words too - the maker's vocabulary
\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'FRG_Word1' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t{
\t\tif( inv.GetItemQuantityByName( schems[i] ) <= 0 )
\t\t\tinv.AddAnItem( schems[i], 1 );
\t}
\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'FRG_Word2' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t{
\t\tif( inv.GetItemQuantityByName( schems[i] ) <= 0 )
\t\t\tinv.AddAnItem( schems[i], 1 );
\t}
}

// Token format version. Tokens minted before the six damage counters existed
// carry no FRG_Ver at all, and GetItemModifierInt cannot tell "absent" from
// "zero" - so an old token would silently transfer a damage of nothing and wipe
// the target instead. Bumping this number retires every older token loudly.
function FRG_TokenVer() : int
{
\treturn 2;
}

// Strip one ability (verified) and lay down the donor's count. Returns the count
// that ACTUALLY ended up on the item - not what was asked for. Only the recount
// catches both silent outcomes: too few (removal failed, copies nailed to the
// card) and too many (the target's card carries more than the donor had). The
// caller reports the real numbers instead of claiming success blindly.
@addMethod( W3PlayerWitcher ) function FRG_ReplaceAb( item : SItemUniqueId, ab : name, want : int ) : int
{
\tvar left, add, i : int;

\tFRG_StripAb( item, ab );
\tleft = FRG_CountAb( item, ab );
\tadd = want - left;
\tfor( i = 0; i < add; i += 1 )
\t\tinv.AddItemCraftedAbility( item, ab, true );
\treturn FRG_CountAb( item, ab );
}

// ------------------------------------------------------------- look ----

// Where a transferred look lives:
//   on the item : FRG_Look = K (int modifier, survives saves)
//   in FactsDB  : frg_look_K_len = N, frg_look_K_0..N-1 = character codes of
//                 the donor's equip-template DEPOT PATH. Facts live inside the
//                 SAVE, so playthroughs never bleed into each other and a mod
//                 reinstall loses nothing.
//   at runtime  : FRG_LookEnts[slot] - the fake entity, never saved, rebuilt
//                 by a timer after every load (AMM's exact technique).
// The look token is a reusable APPLICATOR: it is NOT consumed and holds no
// state - selling or losing it never breaks a mounted look.

@addField( W3PlayerWitcher )
var FRG_LookEnts : array< CEntity >;

@addMethod( W3PlayerWitcher ) function FRG_LookAlphabet() : string
{
\tvar s : string;
\tvar i : int;

\tfor( i = 32; i <= 126; i += 1 )
\t\ts += StrChar( i );
\treturn s;
}

// Packs a depot path into facts, one code per character. StrFindFirst against
// the printable-ASCII alphabet is the char->code map: WitcherScript has
// StrChar (code->char) but no reverse.
@addMethod( W3PlayerWitcher ) function FRG_LookPack( prefix : string, key : int, path : string ) : bool
{
\tvar alpha, ch : string;
\tvar i, n, code : int;

\talpha = FRG_LookAlphabet();
\tn = StrLen( path );
\tif( n <= 0 )
\t\treturn false;
\tfor( i = 0; i < n; i += 1 )
\t{
\t\tch = StrMid( path, i, 1 );
\t\tcode = StrFindFirst( alpha, ch );
\t\tif( code < 0 )
\t\t\treturn false;
\t\tFactsSet( prefix + key + "_" + i, 32 + code );
\t}
\tFactsSet( prefix + key + "_len", n );
\treturn true;
}

@addMethod( W3PlayerWitcher ) function FRG_LookRead( prefix : string, key : int ) : string
{
\tvar path : string;
\tvar i, n, code : int;

\tif( key <= 0 )
\t\treturn "";
\tn = FactsQuerySum( prefix + key + "_len" );
\tif( n <= 0 )
\t\treturn "";
\tfor( i = 0; i < n; i += 1 )
\t{
\t\tcode = FactsQuerySum( prefix + key + "_" + i );
\t\tif( code < 32 || code > 126 )
\t\t\treturn "";
\t\tpath += StrChar( code );
\t}
\treturn path;
}

@addMethod( W3PlayerWitcher ) function FRG_LookErase( prefix : string, key : int )
{
\tvar i, n : int;

\tif( key <= 0 )
\t\treturn;
\tn = FactsQuerySum( prefix + key + "_len" );
\tfor( i = 0; i < n; i += 1 )
\t\tFactsRemove( prefix + key + "_" + i );
\tFactsRemove( prefix + key + "_len" );
}

// Erases BOTH stored paths of a look key: the entity template and the icon.
@addMethod( W3PlayerWitcher ) function FRG_LookEraseAll( key : int )
{
\tFRG_LookErase( "frg_look_", key );
\tFRG_LookErase( "frg_icon_", key );
}

// Destroys one fake without touching visibility. Needed when the REAL entity
// is being torn down anyway (unequip, bomb aiming) - there is nothing to
// unhide, and Destroy on a NULL handle is safe (AMM calls it unchecked).
@addMethod( W3PlayerWitcher ) function FRG_DropLookEnt( slot : int )
{
\tif( slot >= 0 && slot < FRG_LookEnts.Size() )
\t\tFRG_LookEnts[slot].Destroy();
}

@addMethod( W3PlayerWitcher ) function FRG_DropLookEnts()
{
\tvar i : int;

\tfor( i = 0; i < FRG_LookEnts.Size(); i += 1 )
\t\tFRG_LookEnts[i].Destroy();
}

// Dresses the REAL sword in the donor's model: the real mesh is switched off,
// a fresh entity of the donor's template is attached to the SWORD'S entity -
// not to Geralt - so it rides scabbard->hand->scabbard by itself. AMM's exact
// technique (SwordsChange), including the unchecked Destroy of the previous
// fake.
@addMethod( W3PlayerWitcher ) function FRG_ApplyLookVisual( slot : int ) : bool
{
\tvar item : SItemUniqueId;
\tvar ent : CEntity;
\tvar comp : CAppearanceComponent;
\tvar tpl : CEntityTemplate;
\tvar path : string;
\tvar names : array< name >;

\tif( slot < 4 || slot > 5 )
\t\treturn false;
\tif( !FRG_Slot( slot, item ) )
\t\treturn false;
\tpath = FRG_LookRead( "frg_look_", inv.GetItemModifierInt( item, 'FRG_Look', 0 ) );
\tif( path == "" )
\t\treturn false;
\t// ⛔ ПРАВИЛЬНЫЙ ПРИЁМ (22.09, по разведке). Меняем облик у САМОГО надетого
\t// меча через его CAppearanceComponent — предмет остаётся в слоте, поэтому
\t// позиция ножен, крюк сталь/серебро и анимации РОДНЫЕ. Двойник-сущность
\t// (заходы 1-4) всегда садился по своему металлу — тупик. Рецепт:
\t// modSetBonusTransfer.sbtlook + ванильный лук (GetItemEntityUnsafe(bow).ApplyAppearance).
\tent = inv.GetItemEntityUnsafe( item );
\tif( !ent )
\t\treturn false;
\tcomp = (CAppearanceComponent)ent.GetComponentByClassName( 'CAppearanceComponent' );
\tif( !comp )
\t\treturn false;
\ttpl = (CEntityTemplate)LoadResource( path, true );
\tif( !tpl )
\t\treturn false;
\tGetAppearanceNames2( path, names );
\tif( names.Size() <= 0 )
\t\treturn false;
\tcomp.IncludeAppearanceTemplate( tpl );
\tcomp.ApplyAppearance( NameToString( names[0] ) );
\treturn true;
}

// Спрятать/показать ВСЮ модель вещи. Одной детали мало: доспех собран
// из нескольких мешей (торс, рукава, пояс, ткань), и пряча только
// первый, мы получали чужой облик ПОВЕРХ родного (жалоба ГД 15.09).
// ⛔ ПОКАЗ И ГАШЕНИЕ РАЗВЕДЕНЫ (15.09, после регрессии с голым торсом).
// Гасить надо ШИРОКО — иначе остаётся ткань (юбка длинных доспехов).
// Показывать широко НЕЛЬЗЯ: у надетой брони в тот же перебор попадают
// меши ТЕЛА, которые игра прячет под доспех, и мы их включали — торс
// лез через любую броню, в том числе нетронутую, и не лечился
// переодеванием, потому что флаг сидит на теле, а не на вещи.
function FRG_MeshShow( ent : CEntity )
{
\tvar comps : array< CComponent >;
\tvar i : int;

\tif( !ent )
\t\treturn;
\t// только МЕШИ и только для клинков: у меча сущность своя, тела
\t// в ней нет. Броня возвращает свой вид переэкипировкой.
\tcomps = ent.GetComponentsByClassName( 'CMeshComponent' );
\tfor( i = 0; i < comps.Size(); i += 1 )
\t\t((CMeshComponent)comps[i]).SetVisible( true );
}

function FRG_MeshVis( ent : CEntity, on : bool )
{
\tvar comps : array< CComponent >;
\tvar dc : CDrawableComponent;
\tvar i : int;

\tif( !ent )
\t\treturn;
\t// НЕ 'CMeshComponent': юбка и подол длинных доспехов - это ТКАНЬ
\t// (CClothComponent, APEX), мех и волосы - CFurComponent. Общий
\t// предок всех троих - CDrawableComponent, и SetVisible объявлен
\t// именно на нём (engine/components.ws), а запрос по классу ищет
\t// по предку. Так ваниль гасит надетую конскую сбрую вместе с
\t// тканевой попоной, и так же гасит надетый предмет itemEntity.
\tcomps = ent.GetComponentsByClassName( 'CDrawableComponent' );
\tfor( i = 0; i < comps.Size(); i += 1 )
\t{
\t\tdc = (CDrawableComponent)comps[i];
\t\tif( dc && dc.GetName() != "shadow_capsule" )
\t\t\tdc.SetVisible( on );
\t}
}

@addMethod( W3PlayerWitcher ) function FRG_ClearLookVisual( slot : int )
{
\tvar item : SItemUniqueId;
\tvar ent : CEntity;
\tvar comp : CAppearanceComponent;
\tvar path : string;
\tvar names : array< name >;

\tif( !FRG_Slot( slot, item ) )
\t\treturn;
\tent = inv.GetItemEntityUnsafe( item );
\tif( !ent )
\t\treturn;
\tcomp = (CAppearanceComponent)ent.GetComponentByClassName( 'CAppearanceComponent' );
\tif( !comp )
\t\treturn;
\t// вернуть РОДНОЙ облик = облик собственного equip_template меча
\tpath = theGame.GetDefinitionsManager().GetItemEquipTemplate( inv.GetItemName( item ) );
\tif( path == "" )
\t\treturn;
\tGetAppearanceNames2( path, names );
\tif( names.Size() > 0 )
\t\tcomp.ApplyAppearance( NameToString( names[0] ) );
}

// Показать НАСТОЯЩИЕ клинки обоих слотов: затычка на те доли секунды,
// пока игра пересоздаёт сущность меча и фейк ещё не перемонтирован.
@addMethod( W3PlayerWitcher ) function FRG_ShowRealBlades()
{
\tvar item : SItemUniqueId;
\tvar ent : CEntity;
\tvar comp : CComponent;
\tvar s : int;

\tfor( s = 4; s <= 5; s += 1 )
\t{
\t\tif( !FRG_Slot( s, item ) )
\t\t\tcontinue;
\t\tif( inv.GetItemModifierInt( item, 'FRG_Look', 0 ) <= 0 )
\t\t\tcontinue;
\t\tFRG_MeshShow( inv.GetItemEntityUnsafe( item ) );
\t}
}

@addMethod( W3PlayerWitcher ) function FRG_RefreshAllLooks()
{
\tvar s : int;

\tfor( s = 4; s <= 5; s += 1 )
\t\tFRG_ApplyLookVisual( s );
\t// armour looks are OFF (13.09) - whatever is left of them is swept
\tFRG_ArmLookRefresh();
}

// ЗАХОД 2 (21.09): держим двойник-облик клинка НА ПОЗИЦИИ реального меча.
// Стальная модель сама висит на стальной точке ножен, поэтому облик на
// мече другого металла уезжает; сторож каждый тик дотягивает его до ent
// (реальный меч всегда в правильной точке — и в ножнах, и в руке).
@addMethod( W3PlayerWitcher )
timer function FRG_BladeLookGuard( dt : float, id : int )
{
\tvar s : int;
\tvar item : SItemUniqueId;
\tvar ent : CEntity;
\tvar busy : bool;

\tfor( s = 4; s <= 5; s += 1 )
\t{
\t\tif( !FRG_Slot( s, item ) )
\t\t\tcontinue;
\t\tif( inv.GetItemModifierInt( item, 'FRG_Look', 0 ) <= 0 )
\t\t\tcontinue;
\t\tif( s >= FRG_LookEnts.Size() )
\t\t\tcontinue;
\t\tif( !FRG_LookEnts[s] )
\t\t\tcontinue;
\t\tent = inv.GetItemEntityUnsafe( item );
\t\tif( !ent )
\t\t\tcontinue;
\t\tbusy = true;
\t\t// ЗАХОД 4 (21.09): двойник САМ цепляется к крюку своего металла, и цепка
\t\t// перебивает телепорт (заходы 2-3 не сдвинули). Рвём его цепку и только
\t\t// потом тащим на позицию реального меча.
\t\tif( FRG_LookEnts[s].HasAttachment() )
\t\t\tFRG_LookEnts[s].BreakAttachment();
\t\tFRG_LookEnts[s].TeleportWithRotation( ent.GetWorldPosition(), ent.GetWorldRotation() );
\t}
\tif( !busy )
\t\tRemoveTimer( 'FRG_BladeLookGuard' );
}

// The carrier bound to a piece, if any (by the shared number).
@addMethod( W3PlayerWitcher ) function FRG_ArmLookCarrier( key : int, out carrier : SItemUniqueId ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar i : int;

\tif( key <= 0 )
\t\treturn false;
\titems = inv.GetItemsByTag( 'FRG_LookItem' );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( inv.GetItemModifierInt( items[i], 'FRG_LookFor', 0 ) == key )
\t\t{
\t\t\tcarrier = items[i];
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

// Put a look on a piece: spawn the carrier, bind the two by a number. An
// older look on the same piece is dropped first. The dye the piece wears
// cannot be copied (a colour needs a dye ITEM to be laid) - the player
// dyes once more, and from then on both are dyed together.
@addMethod( W3PlayerWitcher ) function FRG_ArmLookWear( piece : SItemUniqueId, card : name ) : bool
{
\tvar made : array< SItemUniqueId >;
\tvar carrier : SItemUniqueId;
\tvar key, slot : int;

\tif( !inv.IsIdValid( piece ) )
\t\treturn false;
\tif( inv.GetItemModifierInt( piece, 'FRG_ArmLook', 0 ) > 0 )
\t\tFRG_ArmLookStrip( piece );

\tmade = inv.AddAnItem( card, 1, true, true );
\tif( made.Size() <= 0 )
\t\treturn false;
\tcarrier = made[0];
\tkey = FactsQuerySum( "FRG_ArmLookSeq" ) + 1;
\tFactsSet( "FRG_ArmLookSeq", key );
\t// scenery, not gear: never sold, dropped, shown or studied
\tinv.AddItemTag( carrier, 'FRG_LookItem' );
\tinv.AddItemTag( carrier, 'NoDrop' );
\tinv.AddItemTag( carrier, 'NoShow' );
\tinv.SetItemModifierInt( carrier, 'FRG_LookFor', key );
\tinv.SetItemModifierInt( piece, 'FRG_ArmLook', key );

\tslot = FRGW_ArmSlotOf( inv.GetItemCategory( piece ) );
\tif( slot >= 0 && GetItemSlot( piece ) != EES_InvalidSlot )
\t\tFRG_ArmLookApply( slot );
\treturn true;
}

// Take the look off: the carrier is unmounted and destroyed, the piece is
// mounted again if it is worn.
@addMethod( W3PlayerWitcher ) function FRG_ArmLookStrip( piece : SItemUniqueId )
{
\tvar carrier : SItemUniqueId;
\tvar ent : CEntity;
\tvar comp : CComponent;
\tvar key : int;

\tkey = inv.GetItemModifierInt( piece, 'FRG_ArmLook', 0 );
\tif( FRG_ArmLookCarrier( key, carrier ) )
\t{
\t\tinv.UnmountItem( carrier, true );
\t\tinv.RemoveItem( carrier, 1 );
\t}
\tinv.SetItemModifierInt( piece, 'FRG_ArmLook', 0 );

\t// ⛔ НЕ включать видимость руками: под бронёй скрыты меши тела, и
\t// широкий показ поднимал их вместе с вещью. Родная модель
\t// возвращается пересозданием вещи — штатной переэкипировкой.
\tFRG_ArmReEquip();
}

// Show the carrier instead of the worn piece of one body slot.
@addMethod( W3PlayerWitcher ) function FRG_ArmLookApply( slot : int ) : bool
{
\tvar worn, carrier : SItemUniqueId;
\tvar ent : CEntity;

\tif( slot < 0 || slot > 3 )
\t\treturn false;
\tif( !FRG_Slot( slot, worn ) )
\t\treturn false;
\tif( !FRG_ArmLookCarrier( inv.GetItemModifierInt( worn, 'FRG_ArmLook', 0 ), carrier ) )
\t\treturn false;

\t// ⛔ THE REAL PIECE STAYS MOUNTED. Body-part hiding rides on it, and
\t// destroying its entity let Geralt's bare torso through every armour
\t// (user 13.09). Leave the real thing in place, hide its mesh only.
\tif( !inv.IsItemMounted( worn ) )
\t\tinv.MountItem( worn, false, true );

\t// ⛔ И НОСИТЕЛЬ ТОЖЕ ОСТАЁТСЯ НА МЕСТЕ (16.09, «торс лезет не сразу»).
\t// Голое тело — это обычные ПРЕДМЕТЫ, и прячет их не флаг рендера, а
\t// то, что они не смонтированы; игра пересобирает эту картину на
\t// КАЖДОМ событии монтирования в слоте. Мы снимали носитель каждый
\t// прогон, а настоящую вещь перемонтировать не имеем права — значит
\t// события, которое убрало бы тело обратно под доспех, не случалось
\t// никогда. Поэтому носитель трогаем ровно тогда, когда он не на месте.
\tent = inv.GetItemEntityUnsafe( carrier );
\tif( inv.IsItemMounted( carrier ) && !ent )
\t\tinv.UnmountItem( carrier, true );
\tif( !inv.IsItemMounted( carrier ) )
\t{
\t\tif( !inv.MountItem( carrier, false, true ) )
\t\t\treturn false;
\t}

\t// ВСЕ детали родной вещи, иначе рукава, пояс и ЮБКА длинных доспехов
\t// лезут сквозь новый облик (ГД 15.09). Гашение не трогаем — оно
\t// подтверждено рабочим.
\tent = inv.GetItemEntityUnsafe( worn );
\tif( !ent )
\t\treturn false;
\tFRG_MeshVis( ent, false );

\t// Гашение живёт РОВНО до следующей пересборки мешей вещи, а её
\t// делает движок сам и без события в скриптах. Дальше держит сторож.
\tRemoveTimer( 'FRG_ArmLookGuard' );
\tAddTimer( 'FRG_ArmLookGuard', 0.25, true );
\treturn true;
}

// ⛔ ПОЧЕМУ СТОРОЖ, А НЕ ОДИН ПРОХОД. SetVisible — флаг НА КОМПОНЕНТЕ, а
// не на вещи. Меши надетой брони приходят не из карточки: карточка — это
// CItemEntity БЕЗ собственных мешей, с CAppearanceComponent и включённым
// шаблоном. Как только движок пересоберёт набор (смена соседнего слота —
// вариант брони считается по category="gloves" — стриминг, катсцена,
// конь, покраска), компоненты создаются ЗАНОВО и приходят ВИДИМЫМИ, а
// наше гашение лежит на мёртвых. События в скриптах у пересборки нет.
// Кожа тут не «часть тела», а ОТДЕЛЬНЫЙ МЕШ ВНУТРИ САМОЙ ВЕЩИ: Рысь lvl1 —
// t_01_mg__body_lynx_lvl1, Медведь lvl1 — a_01_mg__body_bear_lvl1, рубаха —
// t_01_mg__body_shirt, офирский — ag_01_ma__body_ofir. Всплывшая родная
// вещь прячется под объёмом облика, а её кожа лезет наружу — это и есть
// плечо с предплечьем на скриншоте ГД 17.09.
@addMethod( W3PlayerWitcher ) function FRG_ArmLookHold() : bool
{
\tvar worn, carrier : SItemUniqueId;
\tvar wornEnt, carrierEnt : CEntity;
\tvar busy : bool;
\tvar s : int;

\tfor( s = 0; s <= 3; s += 1 )
\t{
\t\tif( !FRG_Slot( s, worn ) )
\t\t\tcontinue;
\t\tif( !FRG_ArmLookCarrier( inv.GetItemModifierInt( worn, 'FRG_ArmLook', 0 ), carrier ) )
\t\t\tcontinue;
\t\tbusy = true;

\t\t// ⛔ Гасим родное ТОЛЬКО когда носитель РЕАЛЬНО стоит на теле.
\t\t// Нет носителя — пусть лучше видна настоящая вещь, чем пустое
\t\t// место: голый торс мы уже проходили (13.09).
\t\tif( !inv.IsItemMounted( carrier ) )
\t\t\tcontinue;
\t\tcarrierEnt = inv.GetItemEntityUnsafe( carrier );
\t\tif( !carrierEnt )
\t\t\tcontinue;
\t\twornEnt = inv.GetItemEntityUnsafe( worn );
\t\tif( !wornEnt )
\t\t\tcontinue;
\t\tFRG_MeshVis( wornEnt, false );
\t}
\t// ⛔ Сторож трогает РОВНО видимость: ничего не монтирует, не снимает
\t// и не создаёт. Структуру правит только FRG_ArmLookRefresh, поэтому
\t// ни сирот, ни «голого торса навсегда» сторож породить не может.
\treturn busy;
}

@addMethod( W3PlayerWitcher )
timer function FRG_ArmLookGuard( deltaTime : float, id : int )
{
\tif( !FRG_ArmLookHold() )
\t\tRemoveTimer( 'FRG_ArmLookGuard' );
}

// Подмести СИРОТ (носитель, чья вещь продана или лишилась облика) и
// доложить недостающее. Ничего, что уже стоит на месте, не снимается.
@addMethod( W3PlayerWitcher ) function FRG_ArmLookRefresh()
{
\tvar carriers, items : array< SItemUniqueId >;
\tvar worn : SItemUniqueId;
\tvar ent : CEntity;
\tvar i, j, key, s : int;
\tvar owned, retry, onBody : bool;

\tcarriers = inv.GetItemsByTag( 'FRG_LookItem' );
\tif( carriers.Size() <= 0 )
\t\treturn;

\t// entities do not survive a load: everything is rebuilt from the numbers.
\tinv.GetAllItems( items );
\tfor( i = 0; i < carriers.Size(); i += 1 )
\t{
\t\tkey = inv.GetItemModifierInt( carriers[i], 'FRG_LookFor', 0 );
\t\towned = false;
\t\tonBody = false;
\t\tfor( j = 0; j < items.Size(); j += 1 )
\t\t{
\t\t\t// key > 0 обязателен: у вещи БЕЗ облика модификатор тоже 0, и
\t\t\t// носитель с нечитаемым ключом считался бы нужным вечно
\t\t\tif( key > 0 && inv.GetItemModifierInt( items[j], 'FRG_ArmLook', 0 ) == key )
\t\t\t{
\t\t\t\towned = true;
\t\t\t\tonBody = GetItemSlot( items[j] ) != EES_InvalidSlot;
\t\t\t\tbreak;
\t\t\t}
\t\t}
\t\t// ⛔ СНИМАЕМ ТОЛЬКО СИРОТУ. Прежний безусловный снос всех носителей
\t\t// и был источником голого торса: он крутился на каждое выхватывание
\t\t// меча, каждый бросок бомбы и каждое закрытие инвентаря, всякий раз
\t\t// возвращая телесные предметы наружу.
\t\tif( !owned )
\t\t{
\t\t\tinv.UnmountItem( carriers[i], true );
\t\t\tinv.RemoveItem( carriers[i], 1 );
\t\t\tcontinue;
\t\t}
\t\t// ⛔ ВЕЩЬ УШЛА В СУМКУ — носитель снимаем, но НЕ удаляем: облик
\t\t// живёт на вещи, а висеть на теле поверх следующей вещи носитель
\t\t// не должен. Этого случая функция не разбирала вообще.
\t\tif( !onBody && inv.IsItemMounted( carriers[i] ) )
\t\t\tinv.UnmountItem( carriers[i], true );
\t}

\tfor( s = 0; s <= 3; s += 1 )
\t{
\t\tif( !FRG_Slot( s, worn ) )
\t\t\tcontinue;
\t\t// ⛔ ВЕЩЬ БЕЗ ОБЛИКА — НЕ НАШЕ ДЕЛО (ГД 17.09: снял доспех с
\t\t// обликом, и клиппинг полез на ВАНИЛЬНЫХ вещах). Монтирование
\t\t// руками мы уже опознали как источник голого тела — нельзя
\t\t// применять его ко всему гардеробу.
\t\tif( inv.GetItemModifierInt( worn, 'FRG_ArmLook', 0 ) <= 0 )
\t\t\tcontinue;
\t\tif( !inv.IsItemMounted( worn ) )
\t\t\tinv.MountItem( worn, false, true );
\t}
\tfor( s = 0; s <= 3; s += 1 )
\t{
\t\tif( !FRG_Slot( s, worn ) )
\t\t\tcontinue;
\t\tif( inv.GetItemModifierInt( worn, 'FRG_ArmLook', 0 ) <= 0 )
\t\t\tcontinue;
\t\tif( FRG_ArmLookApply( s ) )
\t\t\tcontinue;
\t\t// провал ровно одного вида — сущность вещи ещё собирается: один
\t\t// повтор. Если носитель просто не встал (бой, конь, катсцена) —
\t\t// повтора НЕТ, вечного таймера не будет.
\t\tent = inv.GetItemEntityUnsafe( worn );
\t\tif( !ent )
\t\t\tretry = true;
\t}
\tif( retry )
\t\tAddTimer( 'FRG_LookRestore', 0.3, false );
}

// Re-equips every worn armour piece the PROPER way. Unmounting by hand left
// the game believing a piece was worn while its entity was gone, so the bare
// body kept showing; taking it off and putting it back on rebuilds both the
// entity and the body-part hiding.
@addMethod( W3PlayerWitcher ) function FRG_ArmReEquip()
{
\tvar worn : SItemUniqueId;
\tvar slots : array< EEquipmentSlots >;
\tvar i : int;

\tslots.PushBack( EES_Armor );
\tslots.PushBack( EES_Boots );
\tslots.PushBack( EES_Gloves );
\tslots.PushBack( EES_Pants );
\tfor( i = 0; i < slots.Size(); i += 1 )
\t{
\t\tif( !GetItemEquippedOnSlot( slots[i], worn ) )
\t\t\tcontinue;
\t\t// отказ снять вещь — не пытаться надеть её обратно: игра уходит
\t\t// в обмен слота с самим собой
\t\tif( !UnequipItemFromSlot( slots[i], true ) )
\t\t\tcontinue;
\t\tEquipItemInGivenSlot( worn, slots[i], false );
\t}
}

// Hand fix for a save that still shows the bare body through armour.
exec function frgarmfix()
{
\tvar w : W3PlayerWitcher;

\tw = GetWitcherPlayer();
\tif( !w )
\t\treturn;
\t// порядок важен: сперва пересоздать вещи штатной переэкипировкой
\t// (игра сама вернёт скрытие тела), и только потом класть облики
\tw.FRG_ArmReEquip();
\tw.FRG_ArmLookRefresh();
\ttheGame.GetGuiManager().ShowNotification( "FRG: armour looks swept, gear re-equipped", 9000 );
}

// Putting a piece on: the game mounts it itself, asynchronously - swap the
// carrier in a moment later, the same delay the sword look uses.
// ⛔ СНЯТИЕ СИММЕТРИЧНО НАДЕВАНИЮ: всё ПОСЛЕ wrappedMethod, когда слот
// уже пуст и вещь снята. Картинку пересобирает штатный проход.
@wrapMethod( W3PlayerWitcher ) function UnequipItemFromSlot( slot : EEquipmentSlots, optional reequipped : bool ) : bool
{
\tvar piece, carrier : SItemUniqueId;
\tvar hadLook, ok : bool;
\tvar lookKey : int;

\tlookKey = 0;
\tif( GetItemEquippedOnSlot( slot, piece ) )
\t{
\t\tlookKey = inv.GetItemModifierInt( piece, 'FRG_ArmLook', 0 );
\t\thadLook = FRGW_ArmSlotOf( inv.GetItemCategory( piece ) ) >= 0 && lookKey > 0;
\t}
\tok = wrappedMethod( slot, reequipped );
\t// A blade leaving its slot drops a buff BY TYPE+SOURCE, not by item: pull
\t// the silver sword while the steel one in hand wears the same charm and
\t// the live buff went down with it. Re-state the truth, it is idempotent.
\tif( ok && ( slot == EES_SteelSword || slot == EES_SilverSword ) )
\t\tFRG_FxRefresh();
\tif( !ok || !hadLook )
\t\treturn ok;
\tif( FRG_ArmLookCarrier( lookKey, carrier ) )
\t\tinv.UnmountItem( carrier, true );
\tRemoveTimer( 'FRG_ArmLookGuard' );
\t// при переодевании игра тут же наденет другое — пересборку сделает
\t// обёртка надевания, второй таймер не нужен
\tif( !reequipped )
\t\tAddTimer( 'FRG_LookRestore', 0.3, false );
\treturn ok;
}

@wrapMethod( W3PlayerWitcher ) function EquipItemInGivenSlot( item : SItemUniqueId, slot : EEquipmentSlots, ignoreMounting : bool, optional toHand : bool ) : bool
{
\tvar ok : bool;

\tok = wrappedMethod( item, slot, ignoreMounting, toHand );
\tif( ok && inv.GetItemModifierInt( item, 'FRG_ArmLook', 0 ) > 0 )
\t\tAddTimer( 'FRG_LookRestore', 0.5, false );
\treturn ok;
}

@addMethod( W3PlayerWitcher )
timer function FRG_LookRestore( deltaTime : float, id : int )
{
\tFRG_RefreshAllLooks();
}

// Bomb/crossbow aiming makes the game REBUILD the sword entity on the back;
// the fake would keep hanging on the dead one. AMM ships the same fix
// (ThrowBombFix): drop the fakes when aiming starts, remount when it ends.
@wrapMethod( CThrowable ) function StartAiming()
{
\tvar w : W3PlayerWitcher;

\twrappedMethod();
\tw = GetWitcherPlayer();
\tif( w )
\t\tw.FRG_DropLookEnts();
}

@wrapMethod( CThrowable ) function StopAiming( flag : bool )
{
\tvar w : W3PlayerWitcher;

\twrappedMethod( flag );
\tw = GetWitcherPlayer();
\tif( w )
\t\tw.AddTimer( 'FRG_LookRestore', 0.5, false );
}

// Sheathing remounts the sword entity and the fake falls off while the real
// mesh stays hidden - the scabbard shows EMPTINESS (caught by the user in
// game). Re-mount the fake after both grab and put; the timer gives the game
// a beat to finish remounting. Event wrappers must return a flag (known rake).
@wrapMethod( CWitcherSword ) function OnGrab()
{
\tvar w : W3PlayerWitcher;
\tvar r : bool;

\tr = wrappedMethod();
\tw = GetWitcherPlayer();
\tif( w )
\t{
\t\t// drawing REBUILDS the sword entity, and the fake dies with the old
\t\t// one - the blade vanished for a moment (user 14.09). Show the real
\t\t// mesh meanwhile: it is still there, only hidden.
\t\tw.FRG_ShowRealBlades();
\t\tw.AddTimer( 'FRG_LookRestore', 0.1, false );
\t}
\treturn r;
}

@wrapMethod( CWitcherSword ) function OnPut()
{
\tvar w : W3PlayerWitcher;
\tvar r : bool;

\tr = wrappedMethod();
\tw = GetWitcherPlayer();
\tif( w )
\t{
\t\tw.FRG_ShowRealBlades();
\t\tw.AddTimer( 'FRG_LookRestore', 0.1, false );
\t}
\treturn r;
}

// The inventory GRID icon: the cell builder takes the INSTANCE, so an item
// wearing a look gets the donor's picture. One wrap on the base class covers
// the bag grid, the paperdoll, chests and shops - every subclass calls super.
// (The item card is untouchable; this repaints the flash layer only.)
@wrapMethod( W3GuiBaseInventoryComponent )
function SetInventoryFlashObjectForItem( item : SItemUniqueId, out flashObject : CScriptedFlashObject ) : void
{
\tvar w : W3PlayerWitcher;
\tvar key : int;
\tvar icon : string;

\twrappedMethod( item, flashObject );

\tw = GetWitcherPlayer();
\tkey = _inv.GetItemModifierInt( item, 'FRG_Look', 0 );
\tif( key > 0 && w )
\t{
\t\ticon = w.FRG_LookRead( "frg_icon_", key );
\t\tif( icon != "" )
\t\t\tflashObject.SetMemberFlashString( "iconPath", icon );
\t}

\t// the blade's own NAME (naming recipe / console) rides the same wrap
\tif( w && _inv.ItemHasTag( item, 'FRG_Forge' ) )
\t{
\t\ticon = w.FRGN_NameOf( item );
\t\tif( icon != "" )
\t\t\tflashObject.SetMemberFlashString( "itemName", icon );
\t}
}

// ------------------------------------------------------------- split ---

// Counts one ability on an instance.
@addMethod( W3PlayerWitcher ) function FRG_CountAb( item : SItemUniqueId, ab : name ) : int
{
\tvar abilities : array< name >;
\tvar i, n : int;

\tinv.GetItemAbilities( item, abilities );
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tif( abilities[i] == ab )
\t\t\tn += 1;
\t}
\treturn n;
}

// Removes copies of one ability and VERIFIES each removal, the way W3EE's own
// GetItemBasePrice does. Definition (card) abilities are ENGINE-LOCKED: neither
// remover touches them, W3EE knows it and re-checks after every removal - so do
// we. Returns how many were removed; whatever survives is nailed to the card.
@addMethod( W3PlayerWitcher ) function FRG_StripAb( item : SItemUniqueId, ab : name ) : int
{
\tvar before, now, removed, guard : int;

\tremoved = 0;
\tguard = 0;
\tbefore = FRG_CountAb( item, ab );
\twhile( before > 0 && guard < 400 )
\t{
\t\tinv.RemoveItemCraftedAbility( item, ab );
\t\tnow = FRG_CountAb( item, ab );
\t\tif( now == before )
\t\t{
\t\t\tinv.RemoveItemBaseAbility( item, ab );
\t\t\tnow = FRG_CountAb( item, ab );
\t\t}
\t\tif( now == before )
\t\t\treturn removed;

\t\tremoved += before - now;
\t\tbefore = now;
\t\tguard += 1;
\t}
\treturn removed;
}

exec function frgsplit( donor : name )
{
\tvar w : W3PlayerWitcher;
\tvar dm : CDefinitionsManagerAccessor;
\tvar src, tok : SItemUniqueId;
\tvar made : array< SItemUniqueId >;
\tvar abilities : array< name >;
\tvar st, sv, stB, stD, svB, svD, fx, i, parts, lid, lk : int;
\tvar seenL : array< int >;
\tvar tokName : name;
\tvar hasPct : bool;
\tvar msg : string;

\tw = GetWitcherPlayer();
\tif( !w ) return;
\tdm = theGame.GetDefinitionsManager();

\tif( !w.FRG_FindInBag( donor, src ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: item not found in the BAG", 8000 );
\t\treturn;
\t}
\tif( dm.ItemHasTag( donor, 'Quest' ) || dm.ItemHasTag( donor, 'NoDrop' ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: quest items refuse the forge", 8000 );
\t\treturn;
\t}
\tif( w.GetMoney() < 1 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: even this forge wants 1 coin", 8000 );
\t\treturn;
\t}

\t// Read the instance BEFORE anything is destroyed.
\tst = w.FRG_CountAb( src, 'autogen_fixed_steel_dmg' );
\tsv = w.FRG_CountAb( src, 'autogen_fixed_silver_dmg' );
\tstB = w.FRG_CountAb( src, 'autogen_steel_base' );
\tstD = w.FRG_CountAb( src, 'autogen_steel_dmg' );
\tsvB = w.FRG_CountAb( src, 'autogen_silver_base' );
\tsvD = w.FRG_CountAb( src, 'autogen_silver_dmg' );
\tfx = w.FRG_FxCodeOf( donor );
\tw.inv.GetItemAbilities( src, abilities );
\thasPct = false;
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tif( !StrContains( NameToString( abilities[i] ), "autogen" ) )
\t\t{
\t\t\thasPct = true;
\t\t\tbreak;
\t\t}
\t}

\t// The sacrifice happens first: tokens are fresh copies of the same card, and
\t// destroying the original afterwards could hit a token by name. IDs saved
\t// before creation keep it honest anyway, but order kills the ambiguity.
\tw.inv.RemoveItem( src, 1 );
\tw.RemoveMoney( 1 );
\tparts = 0;

\tmsg = "FRG split " + donor + ":<br>";

\t// shape token: its own card (window-friendly), the donor's template and
\t// icon are packed into save facts under a key carried by the token.
\tif( FRGW_FindTokCard( 'FRG_ShapeTok', "FRG Shape " + NameToString( donor ), tokName ) )
\t{
\t\tmade = w.inv.AddAnItem( tokName, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tlk = FactsQuerySum( "FRG_LookSeq" ) + 1;
\t\t\tFactsSet( "FRG_LookSeq", lk );
\t\t\tw.FRG_LookPack( "frg_look_", lk, dm.GetItemEquipTemplate( donor ) );
\t\t\tw.FRG_LookPack( "frg_icon_", lk, dm.GetItemIconPath( donor ) );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Look', lk );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tmsg = msg + "shape token<br>";
\t\t\tparts += 1;
\t\t}
\t}

\tif( ( st > 0 || sv > 0 )
\t\t&& FRGW_FindTokCard( 'FRG_DmgTok', "FRG Dmg " + NameToString( donor ), tokName ) )
\t{
\t\tmade = w.inv.AddAnItem( tokName, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 2 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_St', st );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Sv', sv );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_StB', stB );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_StD', stD );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_SvB', svB );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_SvD', svD );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\t// Read the numbers BACK OFF THE TOKEN. Printing the local st/sv would
\t\t\t// look right even if the modifiers never stuck, and the failure would
\t\t\t// only surface two steps later as a silent zero transfer.
\t\t\tmsg = msg + "damage token (steel x" + w.inv.GetItemModifierInt( made[0], 'FRG_St', 0 )
\t\t\t\t+ ", silver x" + w.inv.GetItemModifierInt( made[0], 'FRG_Sv', 0 )
\t\t\t\t+ ", base " + w.inv.GetItemModifierInt( made[0], 'FRG_StB', 0 )
\t\t\t\t+ "/" + w.inv.GetItemModifierInt( made[0], 'FRG_StD', 0 )
\t\t\t\t+ "/" + w.inv.GetItemModifierInt( made[0], 'FRG_SvB', 0 )
\t\t\t\t+ "/" + w.inv.GetItemModifierInt( made[0], 'FRG_SvD', 0 ) + ")<br>";
\t\t\tparts += 1;
\t\t}
\t}

\tif( hasPct )
\t{
\t\tmade = w.inv.AddAnItem( donor, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 3 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tmsg = msg + "percents token<br>";
\t\t\tparts += 1;
\t\t}
\t}

\tif( fx > 0 )
\t{
\t\tmade = w.inv.AddAnItem( FRGFx_TokCard( fx ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 4 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Fx', fx );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tmsg = msg + "effect token (fx " + fx + ")<br>";
\t\t\tparts += 1;
\t\t}
\t}

\t// line tokens: one per DISTINCT Redux pool ability found on the instance
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tlid = FRGL_FromAbility( abilities[i] );
\t\tif( lid <= 0 || seenL.Contains( lid ) )
\t\t\tcontinue;
\t\tseenL.PushBack( lid );
\t\tmade = w.inv.AddAnItem( FRGL_TokCard( lid ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Line', lid );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tmsg = msg + "line token: " + FRGL_Title( lid ) + "<br>";
\t\t\tparts += 1;
\t\t}
\t}

\t// CUT lines of the donor's card profile (schools and relics, v1.1)
\tfor( lid = 1; lid <= FRGL_Count(); lid += 1 )
\t{
\t\tif( FRGL_CutDonor( lid ) != donor )
\t\t\tcontinue;
\t\tmade = w.inv.AddAnItem( FRGL_TokCard( lid ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Line', lid );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tmsg = msg + "cut line: " + FRGL_Stats( lid ) + "<br>";
\t\t\tparts += 1;
\t\t}
\t}

\tmsg = msg + parts + " parts, the original is gone, 1 coin taken.<br>";
\tmsg = msg + "TOKENS look exactly like the item - frgparts() tells them apart.";
\ttheGame.GetGuiManager().ShowNotification( msg, 20000 );
}

exec function frgparts()
{
\tvar w : W3PlayerWitcher;
\tvar items : array< SItemUniqueId >;
\tvar msg : string;
\tvar i, kind, n : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tw.inv.GetAllItems( items );
\tmsg = "FRG parts in the bag:<br>";
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( !w.inv.IsIdValid( items[i] ) )
\t\t\tcontinue;
\t\tkind = w.inv.GetItemModifierInt( items[i], 'FRG_Part', 0 );
\t\tif( kind <= 0 )
\t\t\tcontinue;

\t\tmsg = msg + w.inv.GetItemName( items[i] ) + "  kind:" + kind;
\t\tif( kind == 2 )
\t\t\tmsg = msg + "  (st x" + w.inv.GetItemModifierInt( items[i], 'FRG_St', 0 )
\t\t\t\t+ ", sv x" + w.inv.GetItemModifierInt( items[i], 'FRG_Sv', 0 ) + ")";
\t\tif( kind == 4 )
\t\t\tmsg = msg + "  (fx " + w.inv.GetItemModifierInt( items[i], 'FRG_Fx', 0 ) + ")";
\t\tif( kind == 5 )
\t\t\tmsg = msg + "  line: " + FRGL_Title( w.inv.GetItemModifierInt( items[i], 'FRG_Line', 0 ) );
\t\tif( w.inv.GetItemModifierInt( items[i], 'FRG_Ver', 0 ) < FRG_TokenVer() )
\t\t\tmsg = msg + "  [OLD BUILD - unusable, split the donor again]";
\t\tmsg = msg + "<br>";
\t\tn += 1;
\t}
\tif( n == 0 )
\t\tmsg = msg + "none";
\ttheGame.GetGuiManager().ShowNotification( msg, 25000 );
}

// kind: 2 damage | 3 percents | 4 effect. Look (1) opens at stage 3.
// DYES (user 11.09: "witcher armour can still be dyed - keep that"). The
// dye screen colours the WORN piece; what the world shows is the carrier,
// so the same dye is laid on the carrier first, while the dye item still
// exists. Removal goes through the same door with a remover dye.
@wrapMethod( WmkCR4InventoryMenu ) function ApplyDye( itemId : SItemUniqueId, targetSlot : int ) : void
{
\tvar w : W3PlayerWitcher;
\tvar worn, carrier : SItemUniqueId;

\tw = GetWitcherPlayer();
\tif( w && w.GetItemEquippedOnSlot( targetSlot, worn )
\t\t&& w.FRG_ArmLookCarrier( w.inv.GetItemModifierInt( worn, 'FRG_ArmLook', 0 ), carrier ) )
\t\tw.inv.ColorItem( carrier, itemId );
\twrappedMethod( itemId, targetSlot );
}

// take an armour look off by console: 0 armor | 1 boots | 2 gloves | 3 pants
exec function frgarmlook0( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar worn : SItemUniqueId;

\tw = GetWitcherPlayer();
\tif( !w || !w.FRG_Slot( slot, worn ) )
\t\treturn;
\tw.FRG_ArmLookStrip( worn );
\ttheGame.GetGuiManager().ShowNotification( "FRG: the piece wears its own face again", 8000 );
}

exec function frglook0( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar dst : SItemUniqueId;
\tvar k : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tk = w.inv.GetItemModifierInt( dst, 'FRG_Look', 0 );
\tif( k <= 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: no look is mounted on this item", 8000 );
\t\treturn;
\t}
\tw.FRG_ClearLookVisual( slot );
\tw.FRG_LookEraseAll( k );
\tw.inv.SetItemModifierInt( dst, 'FRG_Look', 0 );
\ttheGame.GetGuiManager().ShowNotification( w.inv.GetItemName( dst ) + " wears its own face again", 10000 );
}

exec function frgapply( donor : name, slot : int, kind : int )
{
\tvar w : W3PlayerWitcher;
\tvar tok, dst : SItemUniqueId;
\tvar abilities : array< name >;
\tvar toAdd : array< name >;
\tvar st, sv, fx, i, removedN, lockedN : int;
\tvar stB, stD, svB, svD : int;
\tvar gSt, gSv, gStB, gStD, gSvB, gSvD : int;
\tvar rep : string;
\tvar an : name;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( kind < 1 || kind > 4 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: kind is 1 look, 2 damage, 3 percents, 4 effect", 8000 );
\t\treturn;
\t}
\tif( !w.FRG_FindPart( donor, kind, tok ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: no such part token in the BAG", 8000 );
\t\treturn;
\t}
\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}

\t// damage and effect go onto swords only; percents anywhere in its own slot
\tif( ( kind == 2 || kind == 4 ) && slot < 4 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this part fits swords (slots 4-5)", 8000 );
\t\treturn;
\t}

\t// A token from an older build carries no counters, and GetItemModifierInt
\t// answers 0 both for "absent" and for "the donor really had none" - so an old
\t// damage token would strip the target and lay down nothing. Refuse loudly and
\t// do NOT eat the token.
\tif( w.inv.GetItemModifierInt( tok, 'FRG_Ver', 0 ) < FRG_TokenVer() )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this token is from an OLDER build and "
\t\t\t+ "carries no counters - applying it would ERASE the target. Drop it and split "
\t\t\t+ "the donor again: frgsplit('" + donor + "')", 20000 );
\t\treturn;
\t}

\tif( kind == 1 )
\t{
\t\tif( slot < 4 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: armour looks arrive with stage B - swords first (slots 4-5)", 8000 );
\t\t\treturn;
\t\t}
\t\tan = w.inv.GetItemCategory( tok );
\t\tif( an != 'steelsword' && an != 'silversword' )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: only a sword-family look fits a sword", 8000 );
\t\t\treturn;
\t\t}
\t\tif( w.inv.GetItemModifierInt( dst, 'FRG_Look', 0 ) > 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this item already wears a look - frglook0(" + slot + ") first", 10000 );
\t\t\treturn;
\t\t}
\t\trep = theGame.GetDefinitionsManager().GetItemEquipTemplate( donor );
\t\tif( rep == "" )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the donor has no equip template - nothing to wear", 10000 );
\t\t\treturn;
\t\t}

\t\ti = FactsQuerySum( "FRG_LookSeq" ) + 1;
\t\tFactsSet( "FRG_LookSeq", i );
\t\tif( !w.FRG_LookPack( "frg_look_", i, rep ) )
\t\t{
\t\t\tw.FRG_LookEraseAll( i );
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: could not store the template path - nothing changed", 10000 );
\t\t\treturn;
\t\t}
\t\t// the donor's inventory icon rides along - a second packed path, same codec.
\t\t// Non-critical: an unpacked icon just leaves the blank's own picture.
\t\trep = theGame.GetDefinitionsManager().GetItemIconPath( donor );
\t\tif( rep != "" )
\t\t\tw.FRG_LookPack( "frg_icon_", i, rep );

\t\tw.inv.SetItemModifierInt( dst, 'FRG_Look', i );
\t\tif( w.FRG_ApplyLookVisual( slot ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( w.inv.GetItemName( dst ) + " now wears the look of " + donor
\t\t\t\t+ ".<br>The look token is a reusable applicator, it is NOT consumed.<br>Undo: frglook0(" + slot + ")", 15000 );
\t\t}
\t\telse
\t\t{
\t\t\tw.FRG_LookEraseAll( i );
\t\t\tw.inv.SetItemModifierInt( dst, 'FRG_Look', 0 );
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the donor template failed to load - nothing changed", 10000 );
\t\t}
\t\treturn;
\t}

\tif( kind == 2 )
\t{
\t\t// Full damage transfer: the fixed stacks AND the autogen base/dmg pair.
\t\t// Base lives per item level, so leaving the target's own base made a
\t\t// high-level axe hit HARDER than the donor - caught by the user.
\t\tst  = w.inv.GetItemModifierInt( tok, 'FRG_St',  0 );
\t\tsv  = w.inv.GetItemModifierInt( tok, 'FRG_Sv',  0 );
\t\tstB = w.inv.GetItemModifierInt( tok, 'FRG_StB', 0 );
\t\tstD = w.inv.GetItemModifierInt( tok, 'FRG_StD', 0 );
\t\tsvB = w.inv.GetItemModifierInt( tok, 'FRG_SvB', 0 );
\t\tsvD = w.inv.GetItemModifierInt( tok, 'FRG_SvD', 0 );

\t\t// A damage token is only ever minted when st or sv is above zero, so both
\t\t// at zero can only mean the counters never stuck. Invariant, not a guess.
\t\tif( st <= 0 && sv <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this damage token carries NO counters "
\t\t\t\t+ "- nothing to transfer. Drop it and split the donor again.", 20000 );
\t\t\treturn;
\t\t}

\t\tgSt  = w.FRG_ReplaceAb( dst, 'autogen_fixed_steel_dmg',  st  );
\t\tgSv  = w.FRG_ReplaceAb( dst, 'autogen_fixed_silver_dmg', sv  );
\t\tgStB = w.FRG_ReplaceAb( dst, 'autogen_steel_base',  stB );
\t\tgStD = w.FRG_ReplaceAb( dst, 'autogen_steel_dmg',   stD );
\t\tgSvB = w.FRG_ReplaceAb( dst, 'autogen_silver_base', svB );
\t\tgSvD = w.FRG_ReplaceAb( dst, 'autogen_silver_dmg',  svD );

\t\t// The report prints GOT/WANTED for every counter. The old one claimed
\t\t// success unconditionally, which is how a fully idle transfer passed for
\t\t// a working one.
\t\trep = "FRG damage -> " + w.inv.GetItemName( dst ) + "<br>"
\t\t\t+ "steel " + gSt + "/" + st + ", silver " + gSv + "/" + sv + "<br>"
\t\t\t+ "base " + gStB + "/" + stB + " " + gStD + "/" + stD
\t\t\t+ " " + gSvB + "/" + svB + " " + gSvD + "/" + svD + "<br>";

\t\tif( gSt == st && gSv == sv && gStB == stB && gStD == stD && gSvB == svB && gSvD == svD )
\t\t{
\t\t\tw.inv.RemoveItem( tok, 1 );
\t\t\trep = rep + "ALL MATCH - token spent.";
\t\t}
\t\telse
\t\t{
\t\t\trep = rep + "PARTIAL - counts above the wanted number are copies NAILED to the "
\t\t\t\t+ "target's card and cannot be removed. Token KEPT.";
\t\t}
\t\ttheGame.GetGuiManager().ShowNotification( rep, 20000 );
\t\treturn;
\t}

\tif( kind == 3 )
\t{
\t\t// Wipe what CAN be wiped. Card-born abilities are engine-locked (proven
\t\t// by W3EE's own price code), so the target's card percents stay and the
\t\t// report says so instead of pretending.
\t\tremovedN = 0;
\t\tw.inv.GetItemAbilities( dst, abilities );
\t\tfor( i = 0; i < abilities.Size(); i += 1 )
\t\t{
\t\t\tif( !StrContains( NameToString( abilities[i] ), "autogen" ) )
\t\t\t\tremovedN += w.FRG_StripAb( dst, abilities[i] );
\t\t}
\t\tw.inv.GetItemAbilities( dst, abilities );
\t\tlockedN = 0;
\t\tfor( i = 0; i < abilities.Size(); i += 1 )
\t\t{
\t\t\tif( !StrContains( NameToString( abilities[i] ), "autogen" ) )
\t\t\t\tlockedN += 1;
\t\t}
\t\t// ...and pour in the token's non-autogen abilities, counts preserved
\t\tw.inv.GetItemAbilities( tok, abilities );
\t\tfor( i = 0; i < abilities.Size(); i += 1 )
\t\t{
\t\t\tif( !StrContains( NameToString( abilities[i] ), "autogen" ) )
\t\t\t\ttoAdd.PushBack( abilities[i] );
\t\t}
\t\tfor( i = 0; i < toAdd.Size(); i += 1 )
\t\t\tw.inv.AddItemCraftedAbility( dst, toAdd[i], true );

\t\tw.inv.RemoveItem( tok, 1 );
\t\ttheGame.GetGuiManager().ShowNotification( "FRG percents on " + w.inv.GetItemName( dst )
\t\t\t+ ": +" + toAdd.Size() + " from donor, -" + removedN + " wiped, "
\t\t\t+ lockedN + " nailed to the card (engine)", 15000 );
\t\treturn;
\t}

\t// kind == 4, the effect
\tif( w.FRG_FxCodeOf( w.inv.GetItemName( dst ) ) > 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target already has its own effect", 9000 );
\t\treturn;
\t}
\tif( w.inv.GetItemModifierInt( dst, 'FRG_Fx', 0 ) > 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target already carries a transferred effect", 9000 );
\t\treturn;
\t}

\tfx = w.inv.GetItemModifierInt( tok, 'FRG_Fx', 0 );
\tw.inv.SetItemModifierInt( dst, 'FRG_Fx', fx );
\tw.FRG_FxStamp( dst );
\t// never hang the buff blindly: only the blade IN HAND carries one
\tw.FRG_FxRefresh();

\tw.inv.RemoveItem( tok, 1 );
\ttheGame.GetGuiManager().ShowNotification( "FRG: effect " + fx + " lives on "
\t\t+ w.inv.GetItemName( dst ) + " now", 12000 );
}

// Free-text naming (enthusiast channel): printable Latin only - the fact
// codec stores ASCII 32..126. The Naming recipe is the localized main road.
exec function frgname( slot : int, text : string )
{
\tvar w : W3PlayerWitcher;
\tvar dst : SItemUniqueId;
\tvar k : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tif( !w.inv.ItemHasTag( dst, 'FRG_Forge' ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: only a FORGED blade takes a name", 9000 );
\t\treturn;
\t}
\tif( StrLen( text ) < 2 || StrLen( text ) > 28 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the name wants 2..28 characters", 9000 );
\t\treturn;
\t}
\tk = FactsQuerySum( "FRG_LookSeq" ) + 1;
\tFactsSet( "FRG_LookSeq", k );
\tif( !w.FRG_LookPack( "frg_name_", k, text ) )
\t{
\t\tw.FRG_LookErase( "frg_name_", k );
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: only printable LATIN fits this store - the Naming recipe gives localized names", 12000 );
\t\treturn;
\t}
\tw.FRG_LookErase( "frg_name_", w.inv.GetItemModifierInt( dst, 'FRG_Name', 0 ) );
\tw.inv.SetItemModifierInt( dst, 'FRG_Name', k );
\ttheGame.GetGuiManager().ShowNotification( "FRG: the blade is named - " + text, 10000 );
}

exec function frgname0( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar dst : SItemUniqueId;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tw.FRG_LookErase( "frg_name_", w.inv.GetItemModifierInt( dst, 'FRG_Name', 0 ) );
\tw.inv.SetItemModifierInt( dst, 'FRG_Name', 0 );
\tw.inv.SetItemModifierInt( dst, 'FRG_Nm1', 0 );
\tw.inv.SetItemModifierInt( dst, 'FRG_Nm2', 0 );
\ttheGame.GetGuiManager().ShowNotification( "FRG: the blade wears its card name again", 9000 );
}

// ------------------------------------------------- stage 1 lab, kept ---

exec function fstat( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: slot is empty (0..5)", 6000 );
\t\treturn;
\t}
\ttheGame.GetGuiManager().ShowNotification( w.FRG_Describe( item ), 30000 );
}

exec function fbag( donor : name )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_FindInBag( donor, item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: no such item in the BAG", 8000 );
\t\treturn;
\t}
\ttheGame.GetGuiManager().ShowNotification( w.FRG_Describe( item ), 30000 );
}

exec function fcopy( donor : name, slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar src, dst : SItemUniqueId;
\tvar abilities : array< name >;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_FindInBag( donor, src ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: donor not found in the BAG", 8000 );
\t\treturn;
\t}
\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}

\tw.inv.GetItemAbilities( src, abilities );
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t\tw.inv.AddItemCraftedAbility( dst, abilities[i], true );

\ttheGame.GetGuiManager().ShowNotification( "FRG: copied " + abilities.Size()
\t\t+ " abilities onto " + w.inv.GetItemName( dst ), 12000 );
}

exec function fadd( slot : int, ability : name, optional n : int )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;
\tif( n < 1 ) n = 1;

\tif( !w.FRG_Slot( slot, item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tfor( i = 0; i < n; i += 1 )
\t\tw.inv.AddItemCraftedAbility( item, ability, true );

\ttheGame.GetGuiManager().ShowNotification( "FRG: +" + n + " " + ability, 9000 );
}

exec function fdel( slot : int, ability : name, optional n : int )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;
\tif( n < 1 ) n = 1;

\tif( !w.FRG_Slot( slot, item ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tfor( i = 0; i < n; i += 1 )
\t\tw.inv.RemoveItemCraftedAbility( item, ability );

\ttheGame.GetGuiManager().ShowNotification( "FRG: -" + n + " " + ability, 9000 );
}

exec function ffxon( code : int )
{
\tvar w : W3PlayerWitcher;
\tvar fx : EEffectType;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tfx = w.FRG_FxType( code );
\tif( fx == EET_Undefined )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: fx code must be 1..15", 8000 );
\t\treturn;
\t}

\tw.AddEffectDefault( fx, w, "RelicWeaponBuff", false );
\ttheGame.GetGuiManager().ShowNotification( "FRG: fx buff ON (" + code + ")", 9000 );
}

exec function ffxoff( code : int )
{
\tvar w : W3PlayerWitcher;
\tvar fx : EEffectType;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tfx = w.FRG_FxType( code );
\tif( fx == EET_Undefined )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: fx code must be 1..15", 8000 );
\t\treturn;
\t}

\tw.RemoveBuff( fx, false, "RelicWeaponBuff" );
\ttheGame.GetGuiManager().ShowNotification( "FRG: fx buff OFF (" + code + ")", 9000 );
}

// Charm diagnostics: what the game thinks is IN HAND, what number and tag each
// blade carries, and how many charm buffs are actually alive. Exactly one may
// be alive, and only while a sword is drawn.
exec function frgfx()
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar msg : string;
\tvar s, fx, i, live : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tmsg = "held slot (4 steel | 5 silver | -1 sheathed): " + w.FRG_FxHeldSlot() + "<br>";
\tfor( s = 4; s <= 5; s += 1 )
\t{
\t\tif( !w.FRG_Slot( s, item ) )
\t\t{
\t\t\tmsg = msg + "slot " + s + ": empty<br>";
\t\t\tcontinue;
\t\t}
\t\tfx = w.inv.GetItemModifierInt( item, 'FRG_Fx', 0 );
\t\tmsg = msg + "slot " + s + ": " + w.inv.GetItemName( item ) + " FRG_Fx=" + fx
\t\t\t+ " card=" + w.FRG_FxCodeOf( w.inv.GetItemName( item ) );
\t\tif( fx > 0 && w.FRG_FxTagged( fx ) )
\t\t{
\t\t\tif( w.inv.ItemHasTag( item, w.FRG_FxTag( fx ) ) )
\t\t\t\tmsg = msg + " tag=YES";
\t\t\telse
\t\t\t\tmsg = msg + " tag=NO";
\t\t}
\t\tmsg = msg + "<br>";
\t}
\tlive = 0;
\tfor( i = 1; i <= 15; i += 1 )
\t{
\t\tif( w.HasBuff( w.FRG_FxType( i ) ) )
\t\t{
\t\t\tlive += 1;
\t\t\tmsg = msg + "buff alive: code " + i + "<br>";
\t\t}
\t}
\tmsg = msg + "charm buffs alive: " + live;
\ttheGame.GetGuiManager().ShowNotification( msg, 20000 );
}

// Diagnoses the whole path a schematic travels to reach the crafting window:
// card tag -> taught to the player -> present in the XML custom definition.
exec function frgui()
{
\tvar w : W3PlayerWitcher;
\tvar dm : CDefinitionsManagerAccessor;
\tvar known, tagged : array< name >;
\tvar main : SCustomNode;
\tvar tmp : name;
\tvar msg : string;
\tvar i, hits : int;
\tvar taught : bool;

\tw = GetWitcherPlayer();
\tif( !w ) return;
\tdm = theGame.GetDefinitionsManager();

\ttagged = dm.GetItemsWithTag( 'FRG_Schem' );
\tmsg = "FRG_Schem cards: " + tagged.Size() + "<br>";

\tknown = w.GetCraftingSchematicsNames();
\ttaught = false;
\tfor( i = 0; i < known.Size(); i += 1 )
\t{
\t\tif( known[i] == 'FRG ForgeBlade schematic' )
\t\t\ttaught = true;
\t}
\tmsg = msg + "player knows " + known.Size() + " schematics, ForgeBlade taught: " + taught + "<br>";

\tmain = dm.GetCustomDefinition( 'crafting_schematics' );
\thits = 0;
\tfor( i = 0; i < main.subNodes.Size(); i += 1 )
\t{
\t\tdm.GetCustomNodeAttributeValueName( main.subNodes[i], 'name_name', tmp );
\t\tif( tmp == 'FRG ForgeBlade schematic' )
\t\t\thits += 1;
\t}
\tmsg = msg + "XML custom def entries named ForgeBlade: " + hits + " (of " + main.subNodes.Size() + " total)";
\ttheGame.GetGuiManager().ShowNotification( msg, 25000 );
}

// ------------------------------------------------------ forge window ---
// Stage 4: the blade constructor inside the vanilla blacksmith crafting
// window. Proven by recon: the window tells items apart ONLY by card names,
// so every pick is its own card; per-instance data (the look key, damage
// counters) rides on the minted token and is read back at craft time.

function FRGW_IsPlaceholder( n : name ) : bool
{
\treturn n == 'frg_slot_shape' || n == 'frg_slot_damage'
\t\t|| n == 'frg_slot_line' || n == 'frg_slot_effect'
\t\t|| n == 'frg_slot_blade' || n == 'frg_slot_blank'
\t\t|| n == 'frg_slot_flaw' || n == 'frg_slot_stamp' || n == 'frg_slot_word1'
\t\t|| n == 'frg_slot_word2' || n == 'frg_slot_shape_a'
\t\t|| n == 'frg_slot_shape_p' || n == 'frg_slot_shape_g'
\t\t|| n == 'frg_slot_shape_b' || n == 'frg_slot_def_a'
\t\t|| n == 'frg_slot_def_p' || n == 'frg_slot_def_g'
\t\t|| n == 'frg_slot_def_b'
\t\t|| n == 'frg_slot_blank_s' || n == 'frg_slot_shape_s'
\t\t|| n == 'frg_slot_meas_w' || n == 'frg_slot_meas_s'
\t\t|| n == 'frg_slot_meas_a' || n == 'frg_slot_meas_p'
\t\t|| n == 'frg_slot_meas_g' || n == 'frg_slot_meas_b';
}

function FRGW_AxisTag( n : name ) : name
{
\tswitch( n )
\t{
\t\tcase 'frg_slot_shape':\treturn 'FRG_ShapeTok';
\t\tcase 'frg_slot_damage':\treturn 'FRG_DmgTok';
\t\tcase 'frg_slot_line':\treturn 'FRG_LineTok';
\t\tcase 'frg_slot_effect':\treturn 'FRG_FxTok';
\t\t// blanks AND forged blades carry FRG_Blank - both take engraving
\t\tcase 'frg_slot_blade':\treturn 'FRG_Blank';
\t\t// RAW blanks only (steel/silver) - the forging slot
\t\tcase 'frg_slot_blank':\treturn 'FRG_BlankRaw';
\t\t// sidearm forging: its own blank and shape axes (class = the blank)
\t\tcase 'frg_slot_blank_s':\treturn 'FRG_BlankRawS';
\t\tcase 'frg_slot_shape_s':\treturn 'FRG_ShapeTokS';
\t\t// studying: the ring walks the player's BAG, not the card pool -
\t\t// the tag is only a marker, one per kind of gear
\t\tcase 'frg_slot_meas_w':\treturn 'FRG_MeasTokW';
\t\tcase 'frg_slot_meas_s':\treturn 'FRG_MeasTokS';
\t\tcase 'frg_slot_meas_a':\treturn 'FRG_MeasTokA';
\t\tcase 'frg_slot_meas_p':\treturn 'FRG_MeasTokP';
\t\tcase 'frg_slot_meas_g':\treturn 'FRG_MeasTokG';
\t\tcase 'frg_slot_meas_b':\treturn 'FRG_MeasTokB';
\t\t// mark stamps: four eternal pointers, one pure plus each
\t\t// the optional fourth slot of forging: flaw marks
\t\tcase 'frg_slot_flaw':\treturn 'FRG_FlawTok';
\t\tcase 'frg_slot_stamp':\treturn 'FRG_Stamp';
\t\t// naming words: the blade's name, two localized halves
\t\tcase 'frg_slot_word1':\treturn 'FRG_Word1';
\t\tcase 'frg_slot_word2':\treturn 'FRG_Word2';
\t\t// armour shapes: one axis per body slot
\t\tcase 'frg_slot_shape_a':\treturn 'FRG_ShapeTokA';
\t\tcase 'frg_slot_shape_p':\treturn 'FRG_ShapeTokP';
\t\tcase 'frg_slot_shape_g':\treturn 'FRG_ShapeTokG';
\t\tcase 'frg_slot_shape_b':\treturn 'FRG_ShapeTokB';
\t\t// armour PROTECTION: whose defense and weight class the piece gets
\t\tcase 'frg_slot_def_a':\treturn 'FRG_DefTokA';
\t\tcase 'frg_slot_def_p':\treturn 'FRG_DefTokP';
\t\tcase 'frg_slot_def_g':\treturn 'FRG_DefTokG';
\t\tcase 'frg_slot_def_b':\treturn 'FRG_DefTokB';
\t}
\treturn '';
}

function FRGW_DefTagFor( cat : name ) : name
{
\tswitch( cat )
\t{
\t\tcase 'armor':\treturn 'FRG_DefTokA';
\t\tcase 'pants':\treturn 'FRG_DefTokP';
\t\tcase 'gloves':\treturn 'FRG_DefTokG';
\t\tcase 'boots':\treturn 'FRG_DefTokB';
\t}
\treturn '';
}

// donor half of a forged card's name (both prefixes: native and cross-metal)
function FRGW_DonorOfForged( n : name ) : string
{
\tvar t : string;

\tt = NameToString( n );
\tif( StrFindFirst( t, "FRG CrossForged " ) == 0 )
\t\treturn StrAfterFirst( t, "FRG CrossForged " );
\tif( StrFindFirst( t, "FRG Forged " ) == 0 )
\t\treturn StrAfterFirst( t, "FRG Forged " );
\treturn t;
}

// THE BLANK DECIDES THE METAL (user's call 22.08): pick the forged card of
// the donor whose category matches the blank - the cross-metal twin when
// needed. Falls back to the native card (armour has no twins).
function FRGW_ForgedFor( donor : string, cat : name, out card : name ) : bool
{
\tvar nm : name;

\tif( FRGW_FindTokCard( 'FRG_Forge', "FRG Forged " + donor, nm )
\t\t&& theGame.GetDefinitionsManager().GetItemCategory( nm ) == cat )
\t{
\t\tcard = nm;
\t\treturn true;
\t}
\tif( FRGW_FindTokCard( 'FRG_Forge', "FRG CrossForged " + donor, nm )
\t\t&& theGame.GetDefinitionsManager().GetItemCategory( nm ) == cat )
\t{
\t\tcard = nm;
\t\treturn true;
\t}
\tif( FRGW_FindTokCard( 'FRG_Forge', "FRG Forged " + donor, nm ) )
\t{
\t\tcard = nm;
\t\treturn true;
\t}
\treturn false;
}

// weight class id -> the engine's armour weight tag
function FRGW_WeightTagOf( wt : int ) : name
{
\tswitch( wt )
\t{
\t\tcase 1:\treturn 'LightArmor';
\t\tcase 2:\treturn 'MediumArmor';
\t\tcase 3:\treturn 'HeavyArmor';
\t}
\treturn '';
}

// which RESISTANCE-token tag serves an armour slot (user's call 05.09)
function FRGW_ResTagFor( cat : name ) : name
{
\tswitch( cat )
\t{
\t\tcase 'armor':\treturn 'FRG_ResTokA';
\t\tcase 'pants':\treturn 'FRG_ResTokP';
\t\tcase 'gloves':\treturn 'FRG_ResTokG';
\t\tcase 'boots':\treturn 'FRG_ResTokB';
\t}
\treturn '';
}

// a blade worth enchanting: forged here, relic quality, or a witcher
// school sword (their names all carry "School"). Keeps the enchant ring
// short and meaningful (user's call 07.09).
function FRGW_IsWorthyBlade( w : W3PlayerWitcher, id : SItemUniqueId ) : bool
{
\tvar nm : string;

\tif( !w.inv.IsIdValid( id ) )
\t\treturn false;
\tif( w.inv.ItemHasTag( id, 'FRG_Forge' ) )
\t\treturn true;
\t// relics count too (user 13.09): quality 4 is a relic in Redux, 5 is
\t// witcher gear - both are worth a red line
\tif( w.inv.GetItemQuality( id ) >= 4 )
\t\treturn true;
\tnm = NameToString( w.inv.GetItemName( id ) );
\treturn StrContains( nm, "School" ) || StrContains( nm, "Serpent" )
\t\t|| StrContains( nm, "Viper" );
}

// which kind of gear a STUDY axis shows (one axis per kind, so gloves
// never turn up in the boots recipe - user's call 07.09)
function FRGW_StudyFits( tag : name, cat : name ) : bool
{
\tswitch( tag )
\t{
\t\tcase 'FRG_MeasTokW':
\t\t\t// a sidearm is a weapon too - no separate recipe for it (07.09)
\t\t\treturn cat == 'steelsword' || cat == 'silversword'
\t\t\t\t|| cat == 'secondary' || cat == 'blunt1h' || cat == 'staff2h'
\t\t\t\t|| cat == 'spear2h' || cat == 'axe1h' || cat == 'axe2h'
\t\t\t\t|| cat == 'cleaver1h' || cat == 'hammer2h' || cat == 'halberd2h';
\t\tcase 'FRG_MeasTokA':\treturn cat == 'armor';
\t\tcase 'FRG_MeasTokP':\treturn cat == 'pants';
\t\tcase 'FRG_MeasTokG':\treturn cat == 'gloves';
\t\tcase 'FRG_MeasTokB':\treturn cat == 'boots';
\t\tcase 'FRG_MeasTokS':
\t\t\treturn cat == 'secondary' || cat == 'blunt1h' || cat == 'staff2h'
\t\t\t\t|| cat == 'spear2h' || cat == 'axe1h' || cat == 'axe2h'
\t\t\t\t|| cat == 'cleaver1h' || cat == 'hammer2h' || cat == 'halberd2h';
\t}
\treturn false;
}

function FRGW_IsStudyTag( tag : name ) : bool
{
\treturn tag == 'FRG_MeasTokW' || tag == 'FRG_MeasTokS' || tag == 'FRG_MeasTokA'
\t\t|| tag == 'FRG_MeasTokP' || tag == 'FRG_MeasTokG' || tag == 'FRG_MeasTokB';
}

// which items a WORK recipe accepts in its first slot: blade recipes take
// blades, armour recipes take armour - the FRG_Blank tag alone is not enough
function FRGW_FitsWorkSlot( schem : name, cat : name ) : bool
{
\t// a piece changing its look: only that kind of piece walks the ring
\tif( FRGW_IsArmorReskin( schem ) )
\t\treturn cat == FRGW_ReskinCatOf( schem );
\tif( FRGW_IsArmorSchem( schem ) )
\t\treturn cat == 'armor' || cat == 'pants' || cat == 'gloves' || cat == 'boots';
\tif( schem == 'FRG Enchant schematic' || schem == 'FRG Reskin schematic' )
\t\treturn cat == 'steelsword' || cat == 'silversword';   // + гард ниже
\t// ⛔ РЕЦЕПТ КУЗНЕЦА — ЗНАЧИТ КЛИНКИ (ГД 18.09: «что там забыли
\t// штаны?»). Свойства, клеймо и наречение стоят у кузнеца, и в их
\t// кольце нечего делать ни броне, ни штанам.
\treturn cat == 'steelsword' || cat == 'silversword'
\t\t|| cat == 'secondary' || cat == 'blunt1h' || cat == 'staff2h'
\t\t|| cat == 'spear2h' || cat == 'axe1h' || cat == 'axe2h'
\t\t|| cat == 'cleaver1h' || cat == 'hammer2h' || cat == 'halberd2h';
}

// can this item be measured at all? (a worn category, not our own gear)
function FRGW_IsMeasurable( cat : name ) : bool
{
\treturn cat == 'steelsword' || cat == 'silversword' || cat == 'armor'
\t\t|| cat == 'pants' || cat == 'gloves' || cat == 'boots'
\t\t|| cat == 'secondary' || cat == 'blunt1h' || cat == 'staff2h'
\t\t|| cat == 'spear2h' || cat == 'axe1h' || cat == 'axe2h'
\t\t|| cat == 'cleaver1h' || cat == 'hammer2h' || cat == 'halberd2h';
}

// which shape-token tag serves a donor category (blades share one axis)
function FRGW_ShapeTagFor( cat : name ) : name
{
\tswitch( cat )
\t{
\t\tcase 'armor':\treturn 'FRG_ShapeTokA';
\t\tcase 'pants':\treturn 'FRG_ShapeTokP';
\t\tcase 'gloves':\treturn 'FRG_ShapeTokG';
\t\tcase 'boots':\treturn 'FRG_ShapeTokB';
\t\t// sidearms: spears, axes, maces, staves - one shared sidearm axis
\t\tcase 'secondary':
\t\tcase 'blunt1h':
\t\tcase 'staff2h':
\t\tcase 'spear2h':
\t\tcase 'axe1h':
\t\tcase 'axe2h':
\t\tcase 'cleaver1h':
\t\tcase 'hammer2h':
\t\tcase 'halberd2h':
\t\t\treturn 'FRG_ShapeTokS';
\t}
\treturn 'FRG_ShapeTok';
}

// word card name -> its id: the digit sits at the tail (frg_word1_7)
function FRGN_OfWordCard( tok : name, half : int ) : int
{
\tvar txt, pre : string;

\ttxt = NameToString( tok );
\tpre = "frg_word" + half + "_";
\tif( StrFindFirst( txt, pre ) != 0 )
\t\treturn 0;
\treturn StringToInt( StrAfterFirst( txt, pre ), 0 );
}

// The blade's chosen name, composed from localization at read time - the
// Russian game sees a Russian name. Empty string = no name given.
function FRGN_Compose( n1 : int, n2 : int ) : string
{
\tif( n1 <= 0 || n2 <= 0 )
\t\treturn "";
\treturn GetLocStringByKeyExt( "frgn1_" + n1 ) + " " + GetLocStringByKeyExt( "frgn2_" + n2 );
}

// Display name of an item: the free-text name (console channel, facts) wins,
// then the two-word composed name, else "".
@addMethod( W3PlayerWitcher ) function FRGN_NameOf( item : SItemUniqueId ) : string
{
\tvar k : int;
\tvar s : string;

\tk = inv.GetItemModifierInt( item, 'FRG_Name', 0 );
\tif( k > 0 )
\t{
\t\ts = FRG_LookRead( "frg_name_", k );
\t\tif( s != "" )
\t\t\treturn s;
\t}
\treturn FRGN_Compose( inv.GetItemModifierInt( item, 'FRG_Nm1', 0 ),
\t\tinv.GetItemModifierInt( item, 'FRG_Nm2', 0 ) );
}

// stamp card name -> temper id (1..4): the digit sits at the tail
function FRGT_OfStampCard( tok : name ) : int
{
\tvar txt : string;

\ttxt = NameToString( tok );
\tif( StrFindFirst( txt, "FRG Stamp " ) != 0 )
\t\treturn 0;
\treturn StringToInt( StrAfterFirst( txt, "FRG Stamp " ), 0 );
}

// ---------------------------------------------------- the blade's path ---
// Tier lives as a NUMBER on the instance (FRG_Tier); the FRG_Q2..Q4 abilities
// carry ONLY quality (+1 each) - the damage floor and the name color follow
// the game's own quality formula. Legacy forged blades (pre-tier builds)
// carry no FRG_Tier and read as relic; FRG_MigrateForged stamps them.
function FRGP_QAbility( tier : int ) : name
{
\tswitch( tier )
\t{
\t\tcase 2:\treturn 'FRG_Q2';
\t\tcase 3:\treturn 'FRG_Q3';
\t\tcase 4:\treturn 'FRG_Q4';
\t}
\treturn '';
}

// autogen stack deficit of a tier - the game's own quality penalty
function FRGP_Deficit( tier : int ) : int
{
\tswitch( tier )
\t{
\t\tcase 1:\treturn 7;
\t\tcase 2:\treturn 5;
\t\tcase 3:\treturn 3;
\t}
\treturn 0;
}

@addMethod( W3PlayerWitcher ) function FRGP_TierOf( item : SItemUniqueId ) : int
{
\tvar t : int;

\tif( !inv.ItemHasTag( item, 'FRG_Forge' ) )
\t\treturn 0;
\tt = inv.GetItemModifierInt( item, 'FRG_Tier', 0 );
\tif( t <= 0 )
\t\tt = 4;\t// legacy forged blade: born a relic
\tif( t > 4 )
\t\tt = 4;
\treturn t;
}

// Pours the donor's damage TARGET (counters stored on the blade at forging)
// up to the current tier: fixed stacks minus the tier's deficit, base fully.
// The engine never pours DOWN, so upgrades only ever add - by design.
@addMethod( W3PlayerWitcher ) function FRGP_PourTier( item : SItemUniqueId )
{
\tvar st, sv, d : int;
\tvar cat : name;

\tcat = inv.GetItemCategory( item );
\tif( cat != 'steelsword' && cat != 'silversword' )
\t{
\t\t// armour: the donor's card ARMOR ability is constant; the tier tax is
\t\t// a removable -15/-10/-5% armor ability, lifted as the piece climbs
\t\tfor( d = 1; d <= 3; d += 1 )
\t\t\tFRG_StripAb( item, FRGAP_Ability( d ) );
\t\td = FRGP_TierOf( item );
\t\tif( d >= 1 && d <= 3 )
\t\t\tinv.AddItemCraftedAbility( item, FRGAP_Ability( d ), false );
\t\treturn;
\t}

\tst = inv.GetItemModifierInt( item, 'FRG_St', 0 );
\tsv = inv.GetItemModifierInt( item, 'FRG_Sv', 0 );
\tif( st <= 0 && sv <= 0 )
\t\treturn;\t// no target stored (legacy blade) - nothing to pour
\td = FRGP_Deficit( FRGP_TierOf( item ) );
\tif( st > 0 )
\t\tFRG_ReplaceAb( item, 'autogen_fixed_steel_dmg', Max( 0, st - d ) );
\tif( sv > 0 )
\t\tFRG_ReplaceAb( item, 'autogen_fixed_silver_dmg', Max( 0, sv - d ) );
\tFRG_ReplaceAb( item, 'autogen_steel_base', inv.GetItemModifierInt( item, 'FRG_StB', 0 ) );
\tFRG_ReplaceAb( item, 'autogen_steel_dmg', inv.GetItemModifierInt( item, 'FRG_StD', 0 ) );
\tFRG_ReplaceAb( item, 'autogen_silver_base', inv.GetItemModifierInt( item, 'FRG_SvB', 0 ) );
\tFRG_ReplaceAb( item, 'autogen_silver_dmg', inv.GetItemModifierInt( item, 'FRG_SvD', 0 ) );
}

// Legacy forged blades made before tiers: the card ability now grants
// quality 1, so without help they would drop from Relic to Common on load.
// Stamp them tier 4 and hand them the three Q-abilities once.
@addMethod( W3PlayerWitcher ) function FRG_MigrateForged()
{
\tvar slotGuard : int;
\tvar items : array< SItemUniqueId >;
\tvar i, t : int;
\tvar migAb : name;

\tinv.GetAllItems( items );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( !inv.IsIdValid( items[i] ) || !inv.ItemHasTag( items[i], 'FRG_Forge' ) )
\t\t\tcontinue;
\t\t// a look carrier is scenery - no quality, no sockets, no pour
\t\tif( inv.ItemHasTag( items[i], 'FRG_LookItem' ) )
\t\t\tcontinue;
\t\t// instance tags do not survive a save: the weight class is stored as
\t\t// a NUMBER and the tag is re-applied on every spawn (set-mod pattern)
\t\tt = inv.GetItemModifierInt( items[i], 'FRG_Weight', 0 );
\t\tif( t > 0 && !inv.ItemHasTag( items[i], FRGW_WeightTagOf( t ) ) )
\t\t\tinv.AddItemTag( items[i], FRGW_WeightTagOf( t ) );
\t\t// stages are gone: EVERY forged piece is normalized to relic -
\t\t// quality abilities, full pour, flat add-ons, rune sockets
\t\tfor( t = 2; t <= 4; t += 1 )
\t\t{
\t\t\tif( FRG_CountAb( items[i], FRGP_QAbility( t ) ) <= 0 )
\t\t\t\tinv.AddItemCraftedAbility( items[i], FRGP_QAbility( t ), false );
\t\t}
\t\tinv.SetItemModifierInt( items[i], 'FRG_Tier', 4 );
\t\tFRGP_PourTier( items[i] );
\t\tmigAb = FRGFD_AbilityByText( FRGW_DonorOfForged( inv.GetItemName( items[i] ) ) );
\t\tif( migAb != '' && FRG_CountAb( items[i], migAb ) <= 0 )
\t\t\tinv.AddItemCraftedAbility( items[i], migAb, false );
\t\t// the engine may refuse more sockets (armour often does): a plain
\t\t// while() here hung the whole game (user 05.09) - bail out instead
\t\tslotGuard = inv.GetItemEnhancementSlotsCount( items[i] );
\t\twhile( slotGuard < 3 )
\t\t{
\t\t\tinv.AddSlot( items[i] );
\t\t\tif( inv.GetItemEnhancementSlotsCount( items[i] ) <= slotGuard )
\t\t\t\tbreak;
\t\t\tslotGuard = inv.GetItemEnhancementSlotsCount( items[i] );
\t\t}
\t}
}

// family-normalized donor: strip "NGP " and "_crafted" so a witness token
// matches the CUT line of any family member ("X" / "X_crafted" / "NGP X")
function FRG_DonorBase( txt : string ) : string
{
\tif( StrFindFirst( txt, "NGP " ) == 0 )
\t\ttxt = StrAfterFirst( txt, "NGP " );
\tif( StrLen( txt ) > 8 && StrFindLast( txt, "_crafted" ) == StrLen( txt ) - 8 )
\t\ttxt = StrLeft( txt, StrLen( txt ) - 8 );
\treturn txt;
}

// Reclaim knowledge lost to the chunk-router bug: while it hid part of the
// registry, disassembly minted shape/damage/def tokens but not the donor's
// PROPERTY lines. Those tokens witness a past disassembly - re-mint every
// missing CUT line of a witnessed donor. Idempotent ("already studied" guard).
@addMethod( W3PlayerWitcher ) function FRG_ReclaimLost()
{
\tvar items, made : array< SItemUniqueId >;
\tvar wit : array< string >;
\tvar nm, base : string;
\tvar resNm : name;
\tvar i, lid, minted : int;

\tinv.GetAllItems( items );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( !inv.IsIdValid( items[i] ) )
\t\t\tcontinue;
\t\tnm = NameToString( inv.GetItemName( items[i] ) );
\t\tif( StrFindFirst( nm, "FRG Shape " ) == 0 )
\t\t\tbase = FRG_DonorBase( StrAfterFirst( nm, "FRG Shape " ) );
\t\telse if( StrFindFirst( nm, "FRG Dmg " ) == 0 )
\t\t\tbase = FRG_DonorBase( StrAfterFirst( nm, "FRG Dmg " ) );
\t\telse if( StrFindFirst( nm, "FRG Def " ) == 0 )
\t\t\tbase = FRG_DonorBase( StrAfterFirst( nm, "FRG Def " ) );
\t\telse
\t\t\tcontinue;
\t\tif( !wit.Contains( base ) )
\t\t\twit.PushBack( base );
\t}
\t// the backbone is ONE thing again (user 15.09): in Redux the armour
\t// value and the resistances are inseparable - heavy armour means
\t// slow steps, big protection AND big resistances. Their stats ride
\t// the PROTECTION token now, so sweep the stale ones out of the bag.
\tminted = 0;
\tinv.GetAllItems( items );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( !inv.IsIdValid( items[i] ) )
\t\t\tcontinue;
\t\tnm = NameToString( inv.GetItemName( items[i] ) );
\t\tif( StrFindFirst( nm, "FRG Res " ) != 0 )
\t\t\tcontinue;
\t\tinv.RemoveItem( items[i], inv.GetItemQuantity( items[i] ) );
\t\tminted += 1;
\t}
\tif( minted > 0 )
\t\ttheGame.GetGuiManager().ShowNotification( "Forge: protection and resistances are one token again - " + minted + " stale tokens cleared", 10000 );

\tif( wit.Size() <= 0 )
\t\treturn;

\tminted = 0;
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tlid = FRGL_IdAt( i );
\t\tbase = FRG_DonorBase( NameToString( FRGL_CutDonor( lid ) ) );
\t\tif( base == "" || !wit.Contains( base ) )
\t\t\tcontinue;
\t\tif( inv.GetItemQuantityByName( FRGL_TokCard( lid ) ) > 0 )
\t\t\tcontinue;
\t\tmade = inv.AddAnItem( FRGL_TokCard( lid ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Line', lid );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}
\tif( minted > 0 )
\t\ttheGame.GetGuiManager().ShowNotification(
\t\t\t"Forge: reclaimed lost knowledge - " + minted, 11000 );
}

function FRGFx_TokCard( fx : int ) : name
{
\tswitch( fx )
\t{
\t\tcase 1:\treturn 'frg_effect_1';
\t\tcase 2:\treturn 'frg_effect_2';
\t\tcase 3:\treturn 'frg_effect_3';
\t\tcase 4:\treturn 'frg_effect_4';
\t\tcase 5:\treturn 'frg_effect_5';
\t\tcase 6:\treturn 'frg_effect_6';
\t\tcase 7:\treturn 'frg_effect_7';
\t\tcase 8:\treturn 'frg_effect_8';
\t\tcase 9:\treturn 'frg_effect_9';
\t\tcase 10:\treturn 'frg_effect_10';
\t\tcase 11:\treturn 'frg_effect_11';
\t\tcase 12:\treturn 'frg_effect_12';
\t\tcase 13:\treturn 'frg_effect_13';
\t\tcase 14:\treturn 'frg_effect_14';
\t\tcase 15:\treturn 'frg_effect_15';
\t}
\treturn '';
}

function FRGFx_OfTokCard( tok : name ) : int
{
\tvar i : int;

\tfor( i = 1; i <= 15; i += 1 )
\t{
\t\tif( FRGFx_TokCard( i ) == tok )
\t\t\treturn i;
\t}
\treturn 0;
}

function FRGL_OfTokCard( tok : name ) : int
{
\tvar i, id : int;

\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tid = FRGL_IdAt( i );
\t\tif( FRGL_TokCard( id ) == tok )
\t\t\treturn id;
\t}
\treturn 0;
}

// name-from-string is impossible in this build (no StringToName), so the
// per-donor token card is FOUND by comparing strings over the tag pool.
function FRGW_FindTokCard( tag : name, wantText : string, out tok : name ) : bool
{
\tvar all : array< name >;
\tvar i : int;

\tall = theGame.GetDefinitionsManager().GetItemsWithTag( tag );
\tfor( i = 0; i < all.Size(); i += 1 )
\t{
\t\tif( NameToString( all[i] ) == wantText )
\t\t{
\t\t\ttok = all[i];
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

// One minting routine for the DISASSEMBLE tab: works for donors (shape, dmg,
// rolled pool lines, card-tag effect) and for forged blades coming back apart
// (their FRG_L_* abilities and FRG_Fx modifier feed the same paths; the shape
// token is re-minted from the forged card itself - it carries the donor's
// template and icon).
@addMethod( W3PlayerWitcher ) function FRG_MintTokens( donor : name, isForged : bool,
\tst : int, sv : int, stB : int, stD : int, svB : int, svD : int, fx : int,
\tabilities : array< name >, optional silent : bool ) : int
{
\tvar made : array< SItemUniqueId >;
\tvar seenL : array< int >;
\tvar tokName, pathSrc : name;
\tvar want : string;
\tvar i, lid, lk, minted, known : int;

\tminted = 0;
\tpathSrc = donor;
\twant = NameToString( donor );
\tif( isForged )
\t\twant = FRGW_DonorOfForged( donor );
\t// NG+ trophies are separate "NGP X" cards: knowledge falls as the BASE item
\tif( StrFindFirst( want, "NGP " ) == 0 )
\t\twant = StrAfterFirst( want, "NGP " );

\t// Tokens are KNOWLEDGE (eternal, user's call): a duplicate is never
\t// minted - "already studied". Each guard checks the bag by card name.
\t// shape: for a donor - its own name; for a forged blade - the donor half
\t// of the forged card's name; template/icon paths come from pathSrc card.
\t// Armour shapes live on per-slot axis tags (FRGW_ShapeTagFor).
\tif( FRGW_FindTokCard( FRGW_ShapeTagFor( theGame.GetDefinitionsManager().GetItemCategory( pathSrc ) ),
\t\t\t"FRG Shape " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t{
\t\tmade = inv.AddAnItem( tokName, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tlk = FactsQuerySum( "FRG_LookSeq" ) + 1;
\t\t\tFactsSet( "FRG_LookSeq", lk );
\t\t\tFRG_LookPack( "frg_look_", lk, theGame.GetDefinitionsManager().GetItemEquipTemplate( pathSrc ) );
\t\t\tFRG_LookPack( "frg_icon_", lk, theGame.GetDefinitionsManager().GetItemIconPath( pathSrc ) );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Look', lk );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}

\tif( ( st > 0 || sv > 0 )
\t\t&& FRGW_FindTokCard( 'FRG_DmgTok', "FRG Dmg " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t{
\t\tmade = inv.AddAnItem( tokName, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Part', 2 );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_St', st );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Sv', sv );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_StB', stB );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_StD', stD );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_SvB', svB );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_SvD', svD );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}

\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tlid = FRGL_FromAbility( abilities[i] );
\t\tif( lid <= 0 || seenL.Contains( lid ) )
\t\t\tcontinue;
\t\tseenL.PushBack( lid );
\t\tif( inv.GetItemQuantityByName( FRGL_TokCard( lid ) ) > 0 )
\t\t{
\t\t\tknown += 1;
\t\t\tcontinue;
\t\t}
\t\tmade = inv.AddAnItem( FRGL_TokCard( lid ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Line', lid );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}

\t// armour donors mint a PROTECTION token too (armor value + weight class)
\tif( FRGAD_AbilityByText( want ) != ''
\t\t&& FRGW_FindTokCard( FRGW_DefTagFor( theGame.GetDefinitionsManager().GetItemCategory( pathSrc ) ),
\t\t\t"FRG Def " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t{
\t\tmade = inv.AddAnItem( tokName, 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}

\tif( fx > 0 && inv.GetItemQuantityByName( FRGFx_TokCard( fx ) ) <= 0 )
\t{
\t\tmade = inv.AddAnItem( FRGFx_TokCard( fx ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Part', 4 );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Fx', fx );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}

\t// CUT lines of the donor's own card profile (schools and relics, v1.1);
\t// the whole family answers: "X" / "X_crafted" / "NGP X"
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tlid = FRGL_IdAt( i );
\t\tif( !FRGL_MatchDonor( lid, donor ) )
\t\t\tcontinue;
\t\tif( inv.GetItemQuantityByName( FRGL_TokCard( lid ) ) > 0 )
\t\t{
\t\t\tknown += 1;
\t\t\tcontinue;
\t\t}
\t\tmade = inv.AddAnItem( FRGL_TokCard( lid ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Line', lid );
\t\t\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t\tminted += 1;
\t\t}
\t}
\tif( !silent && ( minted > 0 || known > 0 ) )
\t\ttheGame.GetGuiManager().ShowNotification( "Forge: new knowledge " + minted
\t\t\t+ ", already in your book " + known, 11000 );
\treturn minted;
}

// LOOK-ONLY donor mods (user's call 03.09): their own items must never be
// buyable - the Baron's quartermaster, the Kaer Trolde armorer and the
// Toussaint archmaster would sell them otherwise. The shop WINDOW hides
// them; Elihal sells the shape tokens instead.
function FRGV_ShopBan( n : name ) : bool
{
\treturn n == 'Frayed Armor' || n == 'Frayed Gloves'
\t\t|| n == 'NGP Frayed Armor' || n == 'NGP Frayed Gloves'
\t\t|| n == 'vagabondarmor' || n == 'NGP vagabondarmor'
\t\t|| n == 'Raven Armor Schematic' || n == 'Raven Pants Schematic'
\t\t|| n == 'Raven Gloves Schematic' || n == 'Raven Boots Schematic';
}

// The tier ladder, NG+ included: an "NGP X" card climbs the very same
// ladder as plain "X", so the prefix is cut before the lookup.
function FRGX_PrevAny( donor : name ) : name
{
\tvar txt : string;
\tvar prev : name;

\ttxt = NameToString( donor );
\tprev = FRGX_PrevOf( txt );
\tif( prev != '' )
\t\treturn prev;
\tif( StrFindFirst( txt, "NGP " ) != 0 )
\t\treturn '';
\treturn FRGX_PrevOf( StrAfterFirst( txt, "NGP " ) );
}

// Hand the previous tier over: for an NG+ donor try its NG+ twin first.
@addMethod( W3PlayerWitcher ) function FRG_GivePrevTier( donor : name ) : name
{
\tvar prev : name;
\tvar made : array< SItemUniqueId >;

\t// NG+ pairs live in the map itself (gen_prev.py), so no name juggling
\tprev = FRGX_PrevAny( donor );
\tif( prev == '' )
\t\treturn '';
\tmade = inv.AddAnItem( prev, 1 );
\tif( made.Size() <= 0 )
\t\treturn '';
\treturn prev;
}

// The dismantle screen lists what the item breaks into. The previous tier
// belongs on that list: the player must SEE it before pressing the button
// (user's call 05.09 - "the previous tier does not drop"; it did, silently).
@wrapMethod( W3GuiDisassembleInventoryComponent ) function SetInventoryFlashObjectForItem( item : SItemUniqueId, out flashObject : CScriptedFlashObject ) : void
{
\tvar prevName : name;
\tvar parts : array< SItemParts >;
\tvar arr : CScriptedFlashArray;
\tvar obj : CScriptedFlashObject;
\tvar i : int;

\twrappedMethod( item, flashObject );

\tif( !_inv.IsIdValid( item ) )
\t\treturn;
\tprevName = FRGX_PrevAny( _inv.GetItemName( item ) );
\tif( prevName == '' )
\t\treturn;

\tparts = _inv.GetItemRecyclingParts( item );
\tarr = flashObject.CreateFlashArray();
\tfor( i = 0; i < parts.Size(); i += 1 )
\t{
\t\tobj = flashObject.CreateFlashObject();
\t\tobj.SetMemberFlashString( "name", GetLocStringByKeyExt( _inv.GetItemLocalizedNameByName( parts[i].itemName ) ) );
\t\tobj.SetMemberFlashString( "iconPath", _inv.GetItemIconPathByName( parts[i].itemName ) );
\t\tobj.SetMemberFlashInt( "quantity", 1 );
\t\tarr.PushBackFlashObject( obj );
\t}
\tobj = flashObject.CreateFlashObject();
\tobj.SetMemberFlashString( "name", GetLocStringByKeyExt( _inv.GetItemLocalizedNameByName( prevName ) ) );
\tobj.SetMemberFlashString( "iconPath", _inv.GetItemIconPathByName( prevName ) );
\tobj.SetMemberFlashInt( "quantity", 1 );
\tarr.PushBackFlashObject( obj );
\tflashObject.SetMemberFlashArray( "partList", arr );
}

@wrapMethod( W3GuiBaseInventoryComponent ) function ShouldShowItem( item : SItemUniqueId ) : bool
{
\tvar nm : name;

\tif( (W3GuiShopInventoryComponent)this )
\t{
\t\tnm = _inv.GetItemName( item );
\t\tif( FRGV_ShopBan( nm ) )
\t\t\treturn false;
\t\t// A look already studied is not for sale twice: the tailor's rack
\t\t// shows only what the player still lacks (user's call 05.09).
\t\tif( StrFindFirst( NameToString( nm ), "FRG Shape " ) == 0
\t\t\t&& thePlayer.inv.GetItemQuantityByName( nm ) > 0 )
\t\t\treturn false;
\t}
\treturn wrappedMethod( item );
}

// ---------------------------------------------------------- shop stock ---
// Витрина торговца раскатывается ОДИН раз, при первом спавне NPC, и живёт
// в сейве; перезапаса товара в игре нет вовсе. Вдобавок из пула
// _EP2_store_archmaster игра берёт лишь 100 позиций, а одних гарантированных
// записей W3EE там 128 — наши жетоны не попали бы в выборку и на новой игре.
// Поэтому выкладываем товар сами, из своего лут-определения.
// Метка «долито» — факт сейва С РЕВИЗИЕЙ состава (её пишет build_blanks в
// stock_rev.json): добавили жетоны — сменилась ревизия — уже встреченный
// торговец получит новые при следующем открытии лавки (18.09, облики TW2).
function FRGV_StockKey( ent : CEntity, out lootDef : name ) : string
{
\tif( !ent )
\t\treturn "";
\t// гроссмейстер Туссента (Лафарг): лавка висит на slavko_atimstein
\tif( ent.HasTag( 'slavko_atimstein' ) || ent.HasTag( 'Archmaster' ) )
\t{
\t\tlootDef = '_FRG_stock_gm';
\t\treturn "FRG_Stockd_gm_@@FRG_REV_GM@@";
\t}
\t// Элихаль, Новиград: метка из сцены его лавки (merchantTag = elihal)
\tif( ent.HasTag( 'elihal' ) )
\t{
\t\tlootDef = '_FRG_stock_elihal';
\t\treturn "FRG_Stockd_elihal_@@FRG_REV_EL@@";
\t}
\treturn "";
}

function FRGV_RestockShop( inv : CInventoryComponent, force : bool ) : bool
{
\tvar lootDef : name;
\tvar key : string;
\tvar looks : array< name >;
\tvar i, added : int;

\tif( !inv )
\t\treturn false;
\tkey = FRGV_StockKey( inv.GetEntity(), lootDef );
\tif( key == "" )
\t\treturn false;
\tif( !force && FactsQuerySum( key ) > 0 )
\t\treturn false;
\t// ⛔ ПРЯМАЯ ВЫДАЧА (20.09). AddItemsFromLootDefinition из 414 записей клал
\t// лишь часть (проверено: frgstock(1) добавлял «несколько»). Выдаём каждый
\t// жетон по имени; кого нет — добавляем ровно один. Двойников не будет.
\tlooks = FRGV_ShopLooks( lootDef );
\tfor( i = 0; i < looks.Size(); i += 1 )
\t{
\t\tif( inv.GetItemQuantityByName( looks[i] ) <= 0 )
\t\t{
\t\t\tinv.AddAnItem( looks[i], 1, true, true );
\t\t\tadded += 1;
\t\t}
\t}
\tFactsSet( key, 1 );
\treturn true;
}

// Полные списки жетонов витрин печёт build_lab.py из stock_list.json.
@@FRG_SHOPLOOKS@@

@wrapMethod( W3GuiBaseInventoryComponent ) function Initialize( inv : CInventoryComponent )
{
\tif( (W3GuiShopInventoryComponent)this )
\t\tFRGV_RestockShop( inv, false );
\twrappedMethod( inv );
}

// Долив руками: встать рядом с торговцем (гроссмейстер или Элихаль) и
// позвать. force = 1 повторяет выкладку, даже когда метка этой ревизии уже
// стоит; двойников не будет — прибавка к тому, что уже лежало, срезается.
exec function frgstock( optional force : int )
{
\tvar npc : CNewNPC;
\tvar nSeen, nDone : int;

\tnpc = theGame.GetNPCByTag( 'slavko_atimstein' );
\tif( npc )
\t{
\t\tnSeen += 1;
\t\tif( FRGV_RestockShop( npc.GetInventory(), force > 0 ) )
\t\t\tnDone += 1;
\t}
\tnpc = theGame.GetNPCByTag( 'elihal' );
\tif( npc )
\t{
\t\tnSeen += 1;
\t\tif( FRGV_RestockShop( npc.GetInventory(), force > 0 ) )
\t\t\tnDone += 1;
\t}
\tif( nSeen == 0 )
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: neither the archmaster nor Elihal is around - stand next to one", 8000 );
\telse if( nDone > 0 )
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: stock topped up", 8000 );
\telse
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: already stocked - use frgstock(1) to force", 8000 );
}

// Mint just the shape token of one item card (a twin of the shape branch
// in FRG_MintTokens): the LOOK alone, damage and lines stay with dismantle.
@addMethod( W3PlayerWitcher ) function FRG_LearnLook( donor : name, cat : name ) : name
{
\tvar tokName : name;
\tvar made : array< SItemUniqueId >;
\tvar want : string;
\tvar lk : int;

\twant = NameToString( donor );
\tif( StrFindFirst( want, "NGP " ) == 0 )
\t\twant = StrAfterFirst( want, "NGP " );
\tif( !FRGW_FindTokCard( FRGW_ShapeTagFor( cat ), "FRG Shape " + want, tokName ) )
\t\treturn '';
\tif( inv.GetItemQuantityByName( tokName ) > 0 )
\t\treturn '';
\tmade = inv.AddAnItem( tokName, 1 );
\tif( made.Size() <= 0 )
\t\treturn '';
\tlk = FactsQuerySum( "FRG_LookSeq" ) + 1;
\tFactsSet( "FRG_LookSeq", lk );
\tFRG_LookPack( "frg_look_", lk, theGame.GetDefinitionsManager().GetItemEquipTemplate( donor ) );
\tFRG_LookPack( "frg_icon_", lk, theGame.GetDefinitionsManager().GetItemIconPath( donor ) );
\tinv.SetItemModifierInt( made[0], 'FRG_Look', lk );
\tinv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\treturn donor;
}

// "Take a pattern": the look of one equipped slot (empty slot - nothing)
@addMethod( W3PlayerWitcher ) function FRG_CopySlotLook( slot : EEquipmentSlots ) : name
{
\tvar id : SItemUniqueId;

\tif( !GetItemEquippedOnSlot( slot, id ) || !inv.IsIdValid( id ) )
\t\treturn '';
\treturn FRG_LearnLook( inv.GetItemName( id ), inv.GetItemCategory( id ) );
}

// Sidearms (spears, axes, maces) carry no recycling_parts, so the vanilla
// filter hides them from the dismantle tab. The forge wants them shown:
// sacrificing a spear teaches its shape (user's call 01.09).
@wrapMethod( W3GuiDisassembleInventoryComponent ) function ShouldShowItem( item : SItemUniqueId ) : bool
{
\tvar tags2 : array< name >;

\tif( wrappedMethod( item ) )
\t\treturn true;
\tif( GetWitcherPlayer().IsItemEquipped( item ) && !IsHorse() )
\t\treturn false;
\tif( !_inv.ItemHasTag( item, 'SecondaryWeapon' ) || _inv.IsItemQuest( item ) )
\t\treturn false;
\t_inv.GetItemTags( item, tags2 );
\tif( tags2.Contains( theGame.params.TAG_DONT_SHOW )
\t\t|| tags2.Contains( theGame.params.TAG_DONT_SHOW_ONLY_IN_PLAYERS ) )
\t\treturn false;
\treturn true;
}

// How much knowledge is still left in an item (0 = studied whole). Keeps
// the measuring ring free of items that have nothing more to give.
@addMethod( W3PlayerWitcher ) function FRG_MeasureLeft( item : SItemUniqueId ) : int
{
\tvar tokName, donor : name;
\tvar want : string;
\tvar i, lid, left : int;
\tvar abilities : array< name >;

\tif( !inv.IsIdValid( item ) )
\t\treturn 0;
\tdonor = inv.GetItemName( item );
\twant = NameToString( donor );
\tif( StrFindFirst( want, "NGP " ) == 0 )
\t\twant = StrAfterFirst( want, "NGP " );
\tleft = 0;
\tif( FRGW_FindTokCard( FRGW_ShapeTagFor( inv.GetItemCategory( item ) ), "FRG Shape " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t\tleft += 1;
\tif( FRGW_FindTokCard( 'FRG_DmgTok', "FRG Dmg " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t\tleft += 1;
\tif( FRGAD_AbilityByText( want ) != ''
\t\t&& FRGW_FindTokCard( FRGW_DefTagFor( inv.GetItemCategory( item ) ), "FRG Def " + want, tokName )
\t\t&& inv.GetItemQuantityByName( tokName ) <= 0 )
\t\tleft += 1;
\tinv.GetItemAbilities( item, abilities );
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tlid = FRGL_IdAt( i );
\t\tif( !FRGL_MatchDonor( lid, donor ) )
\t\t\tcontinue;
\t\tif( inv.GetItemQuantityByName( FRGL_TokCard( lid ) ) <= 0 )
\t\t\tleft += 1;
\t}
\treturn left;
}

// Move everything that makes a blade what it is onto another card: its
// crafted properties, damage counters, red line, tier, quality, flaw and
// name, plus its runes (handed back to the bag - sockets are not carried).
@addMethod( W3PlayerWitcher ) function FRG_CarryOver( from : SItemUniqueId, to : SItemUniqueId ) : bool
{
\tvar abilities, runes : array< name >;
\tvar i, k, slots : int;

\tif( !inv.IsIdValid( from ) || !inv.IsIdValid( to ) )
\t\treturn false;

\t// properties: only OUR registry abilities travel - vanilla card stats
\t// belong to the card itself
\tinv.GetItemAbilities( from, abilities );
\tfor( i = 0; i < abilities.Size(); i += 1 )
\t{
\t\tif( FRGL_FromAbility( abilities[i] ) > 0 )
\t\t\tinv.AddItemCraftedAbility( to, abilities[i], false );
\t}
\t// the flaw mark, if the blade was born with one
\tfor( i = 1; i <= FRGF_Count(); i += 1 )
\t{
\t\tk = FRGF_IdAt( i );
\t\tif( FRG_CountAb( from, FRGF_Ability( k ) ) > 0 )
\t\t\tinv.AddItemCraftedAbility( to, FRGF_Ability( k ), false );
\t}
\tfor( i = 1; i <= 4; i += 1 )
\t{
\t\tif( FRG_CountAb( from, FRGD_Ability( i ) ) > 0 )
\t\t\tinv.AddItemCraftedAbility( to, FRGD_Ability( i ), false );
\t\tif( FRG_CountAb( from, FRGT_Ability( i ) ) > 0 )
\t\t\tinv.AddItemCraftedAbility( to, FRGT_Ability( i ), false );
\t}
\t// numbers on the instance: damage pour, effect, tier, flaw, name
\tinv.SetItemModifierInt( to, 'FRG_St', inv.GetItemModifierInt( from, 'FRG_St', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_Sv', inv.GetItemModifierInt( from, 'FRG_Sv', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_StB', inv.GetItemModifierInt( from, 'FRG_StB', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_StD', inv.GetItemModifierInt( from, 'FRG_StD', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_SvB', inv.GetItemModifierInt( from, 'FRG_SvB', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_SvD', inv.GetItemModifierInt( from, 'FRG_SvD', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_Fx', inv.GetItemModifierInt( from, 'FRG_Fx', 0 ) );
\tFRG_FxStamp( to );\t// tag-gated charms (2, 4) travel with the tag, not the number
\tinv.SetItemModifierInt( to, 'FRG_Flaw', inv.GetItemModifierInt( from, 'FRG_Flaw', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_Nm1', inv.GetItemModifierInt( from, 'FRG_Nm1', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_Nm2', inv.GetItemModifierInt( from, 'FRG_Nm2', 0 ) );
\tinv.SetItemModifierInt( to, 'FRG_Tier', 4 );
\tinv.SetItemModifierInt( to, 'ItemQualityModified', 1 );
\tfor( i = 2; i <= 4; i += 1 )
\t{
\t\tif( FRG_CountAb( to, FRGP_QAbility( i ) ) <= 0 )
\t\t\tinv.AddItemCraftedAbility( to, FRGP_QAbility( i ), false );
\t}
\tFRGP_PourTier( to );

\t// runes go back to the bag: sockets of the new card start empty
\tinv.GetItemEnhancementItems( from, runes );
\tfor( i = 0; i < runes.Size(); i += 1 )
\t\tinv.AddAnItem( runes[i], 1 );
\tslots = inv.GetItemEnhancementSlotsCount( from );
\tk = inv.GetItemEnhancementSlotsCount( to );
\twhile( k < slots )
\t{
\t\tinv.AddSlot( to );
\t\tif( inv.GetItemEnhancementSlotsCount( to ) <= k )
\t\t\tbreak;
\t\tk = inv.GetItemEnhancementSlotsCount( to );
\t}
\treturn true;
}

// TAKE MEASUREMENTS: read an item exactly like a dismantle would and mint
// its knowledge - but leave the item ITSELF untouched (user's call 07.09:
// "copy the sword's tokens without destroying it, free for now").
@addMethod( W3PlayerWitcher ) function FRG_MeasureItem( item : SItemUniqueId ) : int
{
\tvar abilities : array< name >;
\tvar donor : name;
\tvar st, sv, stB, stD, svB, svD, fx : int;

\tif( !inv.IsIdValid( item ) )
\t\treturn 0;
\tdonor = inv.GetItemName( item );
\tinv.GetItemAbilities( item, abilities );
\tst = FRG_CountAb( item, 'autogen_fixed_steel_dmg' );
\tsv = FRG_CountAb( item, 'autogen_fixed_silver_dmg' );
\tstB = FRG_CountAb( item, 'autogen_steel_base' );
\tstD = FRG_CountAb( item, 'autogen_steel_dmg' );
\tsvB = FRG_CountAb( item, 'autogen_silver_base' );
\tsvD = FRG_CountAb( item, 'autogen_silver_dmg' );
\tfx = inv.GetItemModifierInt( item, 'FRG_Fx', 0 );
\tif( fx <= 0 )
\t\tfx = FRG_FxCodeOf( donor );
\treturn FRG_MintTokens( donor, inv.ItemHasTag( item, 'FRG_Forge' ),
\t\tst, sv, stB, stD, svB, svD, fx, abilities );
}

// The DISASSEMBLE tab at a craftsman: the instance is read BEFORE the vanilla
// teardown, tokens are minted AFTER it - and only if the item really died.
@wrapMethod( CR4BlacksmithMenu ) function OnDisassembleItem( item : SItemUniqueId, price : int )
{
\tvar w : W3PlayerWitcher;
\tvar abilities : array< name >;
\tvar donor : name;
\tvar st, sv, stB, stD, svB, svD, fx, minted : int;
\tvar isForged, ret : bool;
\tvar parts2 : array< SItemParts >;
\tvar prevName : name;
\tvar made2 : array< SItemUniqueId >;

\tw = GetWitcherPlayer();
\tif( w && _inv.IsIdValid( item ) )
\t{
\t\tdonor = _inv.GetItemName( item );
\t\tisForged = _inv.ItemHasTag( item, 'FRG_Forge' );
\t\t_inv.GetItemAbilities( item, abilities );
\t\tst = w.FRG_CountAb( item, 'autogen_fixed_steel_dmg' );
\t\tsv = w.FRG_CountAb( item, 'autogen_fixed_silver_dmg' );
\t\tstB = w.FRG_CountAb( item, 'autogen_steel_base' );
\t\tstD = w.FRG_CountAb( item, 'autogen_steel_dmg' );
\t\tsvB = w.FRG_CountAb( item, 'autogen_silver_base' );
\t\tsvD = w.FRG_CountAb( item, 'autogen_silver_dmg' );
\t\tfx = _inv.GetItemModifierInt( item, 'FRG_Fx', 0 );
\t\tif( fx <= 0 )
\t\t\tfx = w.FRG_FxCodeOf( donor );
\t}

\tret = wrappedMethod( item, price );

\t// a sidearm has no recycling parts - RecycleItem may leave it alive.
\t// Finish the sacrifice by hand; the minting below sees a dead item.
\tif( w && donor != '' && _inv.IsIdValid( item )
\t\t&& _inv.ItemHasTag( item, 'SecondaryWeapon' ) )
\t{
\t\tparts2 = _inv.GetItemRecyclingParts( item );
\t\tif( parts2.Size() <= 0 )
\t\t\t_inv.RemoveItem( item, 1 );
\t}

\tif( w && donor != '' && !_inv.IsIdValid( item ) )
\t{
\t\tminted = w.FRG_MintTokens( donor, isForged, st, sv, stB, stD, svB, svD, fx, abilities );
\t\t// the tier ladder: the upgrade was forged FROM the previous version
\t\t// of the item - dismantling frees it whole (user's call 02.09)
\t\tprevName = w.FRG_GivePrevTier( donor );
\t\tif( prevName != '' )
\t\t\ttheGame.GetGuiManager().ShowNotification( "The previous tier came off whole: " + GetLocStringByKeyExt( w.inv.GetItemLocalizedNameByName( prevName ) ), 9000 );
\t}
\treturn ret;
}

// Ingredient tooltip in the crafting window: our tokens explain themselves -
// a line token prints its pair, an effect token its red line, a damage token
// the counters off the player's own instance.
@wrapMethod( CR4CraftingMenu ) function GetTooltipData( item : int, compareItemType : int, out resultData : CScriptedFlashObject )
{
\tvar w : W3PlayerWitcher;
\tvar toks : array< SItemUniqueId >;
\tvar nm : name;
\tvar txt, base : string;
\tvar k : int;

\twrappedMethod( item, compareItemType, resultData );

\tw = GetWitcherPlayer();
\tif( !w )
\t\treturn;
\tif( item - 1 < 0 || item - 1 >= itemsNames.Size() )
\t\treturn;
\tnm = itemsNames[item - 1];
\ttxt = "";

\t// the hover header already prints the token's NAME - stats only here
\tk = FRGL_OfTokCard( nm );
\tif( k > 0 )
\t{
\t\t// the KIND goes first: at a glance you see relic / ordinary / junk
\t\ttxt = "";
\t\tif( FRGL_IsRelic( k ) )
\t\t\ttxt = GetLocStringByKeyExt( "frgu_b_relic" ) + " ";
\t\telse if( FRGL_IsJunk( k ) )
\t\t\ttxt = GetLocStringByKeyExt( "frgu_b_junk" ) + " ";
\t\telse
\t\t\ttxt = GetLocStringByKeyExt( "frgu_b_plain" ) + " ";
\t\ttxt = txt + FRGL_Stats( k );
\t}
\t// FLAW marks explain their price and what the price buys
\tk = FRGF_OfTokCard( nm );
\tif( k > 0 )
\t{
\t\ttxt = FRGF_Stats( k ) + "  ";
\t\tif( FRGF_Weight( k ) == 2 )
\t\t\ttxt = txt + GetLocStringByKeyExt( "frgu_s_flaw_heavy" );
\t\telse
\t\t\ttxt = txt + GetLocStringByKeyExt( "frgu_s_flaw_light" );
\t}
\tk = FRGFx_OfTokCard( nm );
\tif( k > 0 )
\t\ttxt = w.FRG_FxRedLine( k );
\tif( StrFindFirst( NameToString( nm ), "FRG Stamp " ) == 0 )
\t{
\t\tk = FRGT_OfStampCard( nm );
\t\tif( k > 0 )
\t\t\ttxt = FRGT_Stats( k ) + " " + GetLocStringByKeyExt( "frgu_mark_hint" );
\t}
\tif( StrFindFirst( NameToString( nm ), "FRG Dmg " ) == 0 )
\t{
\t\ttoks = w.inv.GetItemsByName( nm );
\t\tif( toks.Size() > 0 )
\t\t{
\t\t\ttxt = "" + w.inv.GetItemModifierInt( toks[0], 'FRG_St', 0 )
\t\t\t\t+ " / " + w.inv.GetItemModifierInt( toks[0], 'FRG_Sv', 0 );
\t\t\tbase = FRGFD_StatsByText( StrAfterFirst( NameToString( nm ), "FRG Dmg " ) );
\t\t\tif( base != "" )
\t\t\t\ttxt = txt + ", " + base;
\t\t\ttxt = txt + " " + GetLocStringByKeyExt( "frgu_awake" );
\t\t}
\t}
\tif( StrFindFirst( NameToString( nm ), "FRG Def " ) == 0 )
\t{
\t\tbase = StrAfterFirst( NameToString( nm ), "FRG Def " );
\t\ttxt = "+" + FRGAD_ValueByText( base ) + " ("
\t\t\t+ GetLocStringByKeyExt( "frgu_w" + FRGAD_WeightByText( base ) ) + ") "
\t\t\t+ GetLocStringByKeyExt( "frgu_awake" );
\t\t// armour and resistances are ONE thing in Redux (user 15.09):
\t\t// the token carries both, so the hover reads both
\t\tif( FRGAR_StatsByText( base ) != "" )
\t\t\ttxt = txt + ", " + FRGAR_StatsByText( base );
\t}

\tif( txt != "" )
\t{
\t\t// the compact ingredient hover renders only the name and the category
\t\t// line - so the stats REPLACE the useless "Misc" right there
\t\tresultData.SetMemberFlashString( "ItemType", "<font color='#ca610c'>" + txt + "</font>" );
\t\tbase = resultData.GetMemberFlashString( "Description" );
\t\tif( base != "" )
\t\t\ttxt = "<font color='#ca610c'>" + txt + "</font><br>" + base;
\t\telse
\t\t\ttxt = "<font color='#ca610c'>" + txt + "</font>";
\t\tresultData.SetMemberFlashString( "Description", txt );
\t}
}

// Equip/unequip done INSIDE the inventory rebuilds item entities and orphans
// the look fakes. Re-mount right after the menu closes. (The paperdoll render
// itself is a SEPARATE engine-built entity from item templates - a world-side
// fake can never show there; AMM shares this limitation. Target class is
// CR4InventoryMenu, the most-derived copy - W3EE overrides OnClosingMenu in
// wmkQuickSlotsInventory.ws:9, the documented WmkCR4InventoryMenu trap.)
@wrapMethod( CR4InventoryMenu ) function OnClosingMenu()
{
\tvar w : W3PlayerWitcher;

\tw = GetWitcherPlayer();
\tif( w )
\t\tw.AddTimer( 'FRG_LookRestore', 0.3, false );
\treturn wrappedMethod();
}

// the body slot a given armour recipe forges
function FRGW_ArmorCatOfSchem( n : name ) : name
{
\tswitch( n )
\t{
\t\tcase 'FRG ForgeArmor schematic':\treturn 'armor';
\t\tcase 'FRG ForgePants schematic':\treturn 'pants';
\t\tcase 'FRG ForgeGloves schematic':\treturn 'gloves';
\t\tcase 'FRG ForgeBoots schematic':\treturn 'boots';
\t}
\treturn '';
}

// changing the LOOK of an armour piece (stage B): one recipe per body slot
function FRGW_IsArmorReskin( n : name ) : bool
{
	return n == 'FRG ReskinA schematic' || n == 'FRG ReskinP schematic'
		|| n == 'FRG ReskinG schematic' || n == 'FRG ReskinB schematic';
}

function FRGW_ReskinCatOf( n : name ) : name
{
	switch( n )
	{
		case 'FRG ReskinA schematic':	return 'armor';
		case 'FRG ReskinP schematic':	return 'pants';
		case 'FRG ReskinG schematic':	return 'gloves';
		case 'FRG ReskinB schematic':	return 'boots';
	}
	return '';
}

// FRG_Slot index of a body-armour category (0 armor | 1 boots | 2 gloves | 3 pants)
function FRGW_ArmSlotOf( cat : name ) : int
{
	switch( cat )
	{
		case 'armor':	return 0;
		case 'boots':	return 1;
		case 'gloves':	return 2;
		case 'pants':	return 3;
	}
	return -1;
}

function FRGW_IsArmorSchem( n : name ) : bool
{
\treturn n == 'FRG ForgeArmor schematic' || n == 'FRG ForgePants schematic'
\t\t|| n == 'FRG ForgeGloves schematic' || n == 'FRG ForgeBoots schematic';
}

// Какая БОЛВАНКА куётся этой схемой. Заведён вместо трёх разрозненных
// сравнений: заготовок стало семь (четыре броневые получили свои
// заглушки-результаты 15.09), и перечислять их в четырёх местах — верный
// способ забыть одно. StringToName в этой сборке нет, поэтому switch.
function FRGW_BlankOfSchem( n : name ) : name
{
\tswitch( n )
\t{
\t\tcase 'FRG Blank Steel Sword schematic':\treturn 'FRG Blank Steel Sword';
\t\tcase 'FRG Blank Silver Sword schematic':\treturn 'FRG Blank Silver Sword';
\t\tcase 'FRG Blank Secondary schematic':\treturn 'FRG Blank Secondary';
\t\tcase 'FRG Blank Armor schematic':\treturn 'FRG Blank Armor';
\t\tcase 'FRG Blank Pants schematic':\treturn 'FRG Blank Pants';
\t\tcase 'FRG Blank Gloves schematic':\treturn 'FRG Blank Gloves';
\t\tcase 'FRG Blank Boots schematic':\treturn 'FRG Blank Boots';
\t}
\treturn '';
}

function FRGW_IsOurSchem( n : name ) : bool
{
\treturn n == 'FRG ForgeBlade schematic' || n == 'FRG Engrave schematic'
\t\t|| n == 'FRG Enchant schematic' || n == 'FRG Mark schematic'
\t\t|| n == 'FRG Name schematic' || n == 'FRG Upgrade2 schematic'
\t\t|| n == 'FRG Upgrade3 schematic' || n == 'FRG Upgrade4 schematic'
\t\t|| n == 'FRG ForgeArmor schematic' || n == 'FRG ForgePants schematic'
\t\t|| n == 'FRG ForgeGloves schematic' || n == 'FRG ForgeBoots schematic'
\t\t|| FRGW_BlankOfSchem( n ) != ''
\t\t|| n == 'FRG ForgeSide schematic'
\t\t|| n == 'FRG CopyLook schematic'
\t\t|| n == 'FRG Reskin schematic' || FRGW_IsArmorReskin( n )
\t\t|| StrFindFirst( NameToString( n ), "FRG Study " ) == 0;
}

// is this card one of OUR pick-tokens? (a slot's swapped-in value)
function FRGW_IsOurPick( n : name ) : bool
{
\tvar t : string;

\tt = NameToString( n );
\treturn StrFindFirst( t, "FRG Shape " ) == 0 || StrFindFirst( t, "FRG Dmg " ) == 0
\t\t|| StrFindFirst( t, "FRG Def " ) == 0 || StrFindFirst( t, "FRG Res " ) == 0
\t\t|| StrFindFirst( t, "FRG Forged " ) == 0
\t\t|| StrFindFirst( t, "FRG Blank " ) == 0 || StrFindFirst( t, "FRG Stamp " ) == 0
\t\t|| StrFindFirst( t, "frg_line_" ) == 0 || StrFindFirst( t, "frg_cut_" ) == 0
\t\t|| StrFindFirst( t, "frg_effect_" ) == 0 || StrFindFirst( t, "frg_word" ) == 0;
}

// OUR schematics get OUR validation: the vanilla check races the window's
// mutations and greys the button out for reasons of its own. Rules: an
// unpicked placeholder = not ready; any of our pick-tokens needs exactly ONE
// (they are eternal knowledge); plain materials go by the recipe quantity.
// A refusal still reports itself ("FRG why ...") - no more silent grey.
// the verdict lives on the PLAYER: W3CraftingManager is created privately
// inside the crafting menu (craftingMenu.ws:88) and nothing can reach it
@addField( W3PlayerWitcher )
var FRG_LastWhy : string;

// true только на время проверки, заказанной НАШИМ Craft: окно опрашивает
// каждый рецепт списка, и без этого вердикт кричал про чужие рецепты
@addField( W3PlayerWitcher )
var FRG_InCraft : bool;

@wrapMethod( W3CraftingManager ) function CanCraftSchematic( schematicName : name, checkMerchant : bool ) : ECraftingException
{
\tvar r : ECraftingException;
\tvar schem : SCraftingSchematic;
\tvar msg : string;
\tvar i, have, need : int;
\tvar bad : bool;
\tvar wit : W3PlayerWitcher;

\tr = wrappedMethod( schematicName, checkMerchant );
\tif( !FRGW_IsOurSchem( schematicName ) )
\t\treturn r;
\t// vanilla verdicts about the CRAFTSMAN and MONEY stand; only the
\t// ingredient math is ours
\tif( r != ECE_NoException && r != ECE_TooFewIngredients )
\t\treturn r;

\tGetSchematic( schematicName, schem );
\tbad = false;
\tmsg = "FRG why [" + schematicName + "]:";
\tfor( i = 0; i < schem.ingredients.Size(); i += 1 )
\t{
\t\tif( FRGW_IsPlaceholder( schem.ingredients[i].itemName ) )
\t\t{
\t\t\t// the property CONSTRUCTOR allows empty slots (only the item slot
\t\t\t// is mandatory); every other recipe demands a full pick
\t\t\tif( schematicName == 'FRG Engrave schematic' && i > 0 )
\t\t\t\tcontinue;
\t\t\t// forging: the FLAW slot is optional - a blade may be born clean
\t\t\tif( ( schematicName == 'FRG ForgeBlade schematic' || schematicName == 'FRG ForgeSide schematic' )
\t\t\t\t&& schem.ingredients[i].itemName == 'frg_slot_flaw' )
\t\t\t\tcontinue;
\t\t\t// armour: only the unique bonus square may stay empty
\t\t\tif( FRGW_IsArmorSchem( schematicName )
\t\t\t\t&& schem.ingredients[i].itemName == 'frg_slot_line' )
\t\t\t\tcontinue;
\t\t\t// STUDYING takes no materials and destroys nothing - the only
\t\t\t// thing it needs is a pick inside the recipe. Shouting "not
\t\t\t// enough components" at it in the list was a plain lie (user
\t\t\t// 08.09: five identical red rows). Craft still asks politely.
\t\t\tif( StrFindFirst( NameToString( schematicName ), "FRG Study " ) == 0 )
\t\t\t\tcontinue;
\t\t\t// armour look: an EMPTY look square means "give the native look back",
\t\t\t// so only the piece itself is mandatory
\t\t\tif( FRGW_IsArmorReskin( schematicName ) && i == 1 )
\t\t\t\tcontinue;
\t\t\tbad = true;
\t\t\tmsg = msg + " slot " + i + " not picked;";
\t\t\tcontinue;
\t\t}
\t\thave = Equipment().GetItemQuantityByNameForCrafting( schem.ingredients[i].itemName );
\t\tneed = schem.ingredients[i].quantity;
\t\tif( need < 1 )
\t\t\tneed = 1;
\t\tif( FRGW_IsOurPick( schem.ingredients[i].itemName ) )
\t\t\tneed = 1;
\t\t// the crafting count ignores WORN items (a blank tried on for size)
\t\t// and some flagged cards, while the window still draws 1/1 - ask the
\t\t// bag itself before refusing (user 05.09: "it says no components, and
\t\t// the same happened with swords"). Since 09.09 this covers EVERY
\t\t// picked slot, not just our tokens: the work slot takes the player's
\t\t// own gear, and gear is normally ON him.
\t\tif( have < need )
\t\t\thave = GetWitcherPlayer().inv.GetItemQuantityByName( schem.ingredients[i].itemName );
\t\tif( have < need )
\t\t{
\t\t\tbad = true;
\t\t\tmsg = msg + " " + schem.ingredients[i].itemName + " " + have + "/" + need + ";";
\t\t}
\t}
\tif( !bad )
\t\treturn ECE_NoException;
\twit = GetWitcherPlayer();
\tif( wit )
\t{
\t\t// the verdict is always REMEMBERED (frgwhy() prints it on demand),
\t\t// but shouted only when the player actually pressed Craft
\t\twit.FRG_LastWhy = msg;
\t\tif( wit.FRG_InCraft )
\t\t\ttheGame.GetGuiManager().ShowNotification( msg, 15000 );
\t}
\treturn ECE_TooFewIngredients;
}

// W3EE offers a bonus ability for crafted gear ("Sting", "Celerity",
// "Crush") and glues the picked one onto the result after Craft
// (craftingMenu.ws:1611). On OUR items that is a free extra property the
// player never asked for - the list is emptied for our schematics, and
// index 0 ('W3EE_Regular') means "nothing is glued" (user's call 07.09).
@wrapMethod( CR4CraftingMenu ) function SetupAbilitiesArray()
{
\tif( !FRGW_IsOurSchem( selectedSchematic.schemName ) )
\t{
\t\twrappedMethod();
\t\treturn;
\t}
\tabilitiesArray.Clear();
\tabilitiesArray.PushBack( 'W3EE_Regular' );
\tselectedAbilityIndex = 0;
\tm_craftingManager.SetAbilityName( 'W3EE_Regular' );
}

// The window recounts a swapped ingredient's quantity by its RARITY (x2 for
// common, x0.5 for relic, GetIngredientQuantity) - so a tier-1 Common blade
// suddenly "costs" TWO blades. Our axis slots always take exactly ONE.
@wrapMethod( CR4CraftingMenu ) function GetIngredientQuantity( ingredientName : name, ingredientIdx : int ) : int
{
\tvar orig : name;

\torig = m_schematicListOriginal[selectedSchematicIndex].ingredients[ingredientIdx].itemName;
\tif( FRGW_IsPlaceholder( orig ) )
\t\treturn 1;
\t// ...and the same for a FIXED slot of ours: the armour recipes name the
\t// blank outright, so the rarity rule ("common costs two") hit it and the
\t// window demanded a second blank - the sword fix never covered this.
\tif( FRGW_IsOurPick( orig ) || FRGW_IsOurPick( ingredientName ) )
\t\treturn 1;
\treturn wrappedMethod( ingredientName, ingredientIdx );
}

// ---------------------------------------------------- live summary ---
// The right panel builds the FUTURE item live (the Skyrim/Last Epoch
// lesson): every scroll of a slot recomposes the description - what is
// picked, what it gives, slots used, the price. Field "itemDescription".
@addMethod( CR4CraftingMenu ) function FRG_Summary( tag : name ) : string
{
\tvar schem : SCraftingSchematic;
\tvar w : W3PlayerWitcher;
\tvar s, nm, ln : string;
\tvar ing : name;
\tvar target : SItemUniqueId;
\tvar i, k, picked, lim : int;
\tvar hasTarget : bool;

\tw = GetWitcherPlayer();
\tif( !w )
\t\treturn "";
\tm_craftingManager.GetSchematic( tag, schem );
\tif( schem.schemName == '' )
\t\treturn "";

\ts = "<font color='#ca610c'>" + GetLocStringByKeyExt( "frgu_s_head" ) + "</font>";

\t// target line for rebuild-style recipes (first slot = the item)
\thasTarget = false;
\tif( tag == 'FRG Engrave schematic' || tag == 'FRG Enchant schematic'
\t\t|| tag == 'FRG Mark schematic' || tag == 'FRG Name schematic' )
\t{
\t\ting = schem.ingredients[0].itemName;
\t\tif( !FRGW_IsPlaceholder( ing ) && w.FRG_FindForWork( ing, target ) )
\t\t{
\t\t\thasTarget = true;
\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_target" ) + ": "
\t\t\t\t+ GetLocStringByKeyExt( _inv.GetItemLocalizedNameByName( ing ) );
\t\t}
\t}

\tpicked = 0;
\tfor( i = 1; i < schem.ingredients.Size(); i += 1 )
\t{
\t\ting = schem.ingredients[i].itemName;
\t\tif( FRGW_IsPlaceholder( ing ) )
\t\t\tcontinue;
\t\tln = "";
\t\tk = FRGL_OfTokCard( ing );
\t\tif( k > 0 )
\t\t{
\t\t\tln = "+ " + FRGL_Title( k ) + ": " + FRGL_Stats( k );
\t\t\tpicked += 1;
\t\t}
\t\telse if( FRGFx_OfTokCard( ing ) > 0 )
\t\t\tln = "+ " + w.FRG_FxRedLine( FRGFx_OfTokCard( ing ) );
\t\telse if( StrFindFirst( NameToString( ing ), "FRG Shape " ) == 0 )
\t\t\tln = GetLocStringByKeyExt( "frgu_s_look" ) + ": "
\t\t\t\t+ GetLocStringByKeyExt( _inv.GetItemLocalizedNameByName( ing ) );
\t\telse if( StrFindFirst( NameToString( ing ), "FRG Dmg " ) == 0 )
\t\t{
\t\t\tln = GetLocStringByKeyExt( "frgu_s_dmg" ) + ": "
\t\t\t\t+ GetLocStringByKeyExt( _inv.GetItemLocalizedNameByName( ing ) );
\t\t\tnm = FRGFD_StatsByText( StrAfterFirst( NameToString( ing ), "FRG Dmg " ) );
\t\t\tif( nm != "" )
\t\t\t\tln += " (" + nm + ")";
\t\t}
\t\telse if( StrFindFirst( NameToString( ing ), "FRG Def " ) == 0 )
\t\t{
\t\t\tnm = StrAfterFirst( NameToString( ing ), "FRG Def " );
\t\t\tln = GetLocStringByKeyExt( "frgu_s_def" ) + ": +" + FRGAD_ValueByText( nm )
\t\t\t\t+ " (" + GetLocStringByKeyExt( "frgu_w" + FRGAD_WeightByText( nm ) ) + ")";
\t\t}
\t\telse if( StrFindFirst( NameToString( ing ), "FRG Stamp " ) == 0 )
\t\t\tln = "+ " + FRGT_Stats( FRGT_OfStampCard( ing ) ) + " "
\t\t\t\t+ GetLocStringByKeyExt( "frgu_mark_hint" );
\t\tif( ln != "" )
\t\t\ts += "<br>" + ln;
\t}

\t// naming preview: the two words compose the future name
\tif( tag == 'FRG Name schematic' )
\t{
\t\ti = FRGN_OfWordCard( schem.ingredients[1].itemName, 1 );
\t\tk = FRGN_OfWordCard( schem.ingredients[2].itemName, 2 );
\t\tif( i > 0 && k > 0 )
\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_name" ) + ": <font color='#ca610c'>"
\t\t\t\t+ FRGN_Compose( i, k ) + "</font>";
\t}

\t// slots math for the property constructor
\tif( tag == 'FRG Engrave schematic' && hasTarget )
\t{
\t\t// показ = РЕАЛЬНЫЙ потолок реликтовых свойств (тот же, что запрещает
\t\t// крафт): база 2, тяжёлый порок даёт 3. Раньше показ брал тир реликта
\t\t// (=4) и врал «3/4» — обещал место, которого нет (ГД 21.09).
\t\tlim = w.FRGL_RelicLimit( target );
\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_slots" ) + ": " + picked + "/" + lim;
\t\tk = w.FRGF_On( target );
\t\tif( k > 0 )
\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_flaw" ) + ": " + FRGF_Title( k )
\t\t\t\t+ " (" + FRGF_Stats( k ) + ")";
\t}
\tif( tag == 'FRG ForgeBlade schematic' || tag == 'FRG ForgeSide schematic' )
\t{
\t\tif( schem.ingredients.Size() > 3 && !FRGW_IsPlaceholder( schem.ingredients[3].itemName ) )
\t\t{
\t\t\tk = FRGF_OfTokCard( schem.ingredients[3].itemName );
\t\t\tif( k > 0 )
\t\t\t{
\t\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_flaw" ) + ": " + FRGF_Title( k )
\t\t\t\t\t+ " (" + FRGF_Stats( k ) + ")";
\t\t\t\tif( FRGF_Weight( k ) == 2 )
\t\t\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_flaw_heavy" );
\t\t\t\telse
\t\t\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_flaw_light" );
\t\t\t}
\t\t}
\t\ting = schem.ingredients[0].itemName;
\t\tif( !FRGW_IsPlaceholder( ing ) )
\t\t{
\t\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_metal" ) + ": ";
\t\t\tif( theGame.GetDefinitionsManager().GetItemCategory( ing ) == 'silversword' )
\t\t\t\ts += GetLocStringByKeyExt( "frgu_s_silver" );
\t\t\telse
\t\t\t\ts += GetLocStringByKeyExt( "frgu_s_steel" );
\t\t}
\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_result" );
\t}
\tif( picked == 0 && !hasTarget )
\t\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_pickmore" );

\ts += "<br>" + GetLocStringByKeyExt( "frgu_s_price" ) + ": "
\t\t+ m_craftingManager.GetCraftingCost( tag );
\treturn s;
}

@wrapMethod( CR4CraftingMenu ) function ShowSelectedItemInfo( tag : name ) : void
{
\tvar o : CScriptedFlashObject;
\tvar schem : SCraftingSchematic;
\tvar txt, req, lvlColor : string;
\tvar r : ECraftingException;

\twrappedMethod( tag );

\tif( !FRGW_IsOurSchem( tag ) )
\t\treturn;
\ttxt = FRG_Summary( tag );
\tif( txt == "" )
\t\treturn;
\t// re-send the panel object with OUR live description (the vanilla one
\t// was already sent inside wrappedMethod - same binding, repainted)
\tm_craftingManager.GetSchematic( tag, schem );
\to = m_flashValueStorage.CreateTempFlashObject();
\t_playerInv.GetCraftedItemInfo( itemAdjustedName, o, shouldCompareItems );
\tr = m_craftingManager.CanCraftSchematic( tag, bCouldCraft );
\treq = GetLocStringByKeyExt( CraftsmanTypeToLocalizationKey( schem.requiredCraftsmanType ) );
\tif( r == ECE_TooLowCraftsmanLevel )
\t\tlvlColor = "<font color='#E34040'>";
\telse
\t\tlvlColor = "<font color='#949494'>";
\treq += " / " + lvlColor + GetLocStringByKeyExt( CraftsmanLevelToLocalizationKey( schem.requiredCraftsmanLevel ) ) + "</font>";
\to.SetMemberFlashString( "itemName", GetCurrentDisplayName() );
\to.SetMemberFlashString( "crafterRequirements", req );
\to.SetMemberFlashString( "itemDescription", txt );
\tm_flashValueStorage.SetFlashObject( "blacksmithing.menu.crafted.item.tooltip", o );
}

// Alchemy-window rule: a token standing in one slot of this schematic is
// not offered to another. Placeholders are never "taken" (the "clear the
// slot" option must survive), nor is the slot's own current value (the
// scroll walker starts from FindFirst of it).
@addMethod( CR4CraftingMenu ) function FRGW_TakenElsewhere( candidate : name, ingredient : int ) : bool
{
\tvar i : int;

\tif( FRGW_IsPlaceholder( candidate ) )
\t\treturn false;
\tif( candidate == itemsNames[ingredient] )
\t\treturn false;
\tfor( i = 0; i < itemsNames.Size(); i += 1 )
\t{
\t\tif( i != ingredient && itemsNames[i] == candidate )
\t\t\treturn true;
\t}
\treturn false;
}

// Property-slot verdict for the line axis: 0 = fine, 1 = duplicate (same card
// or a content TWIN already seated), 2 = no slot left for another plus. One
// registry pass; the budget mirrors the Craft gate (base + junk picks, +1 for
// the Dark Curse, hard cap 5) so the window refuses BEFORE the craft button.
@addMethod( CR4CraftingMenu ) function FRGW_LineDeny( candidate : name, ingredient : int ) : int
{
\tvar w : W3PlayerWitcher;
\tvar blankId : SItemUniqueId;
\tvar shapeTok, card : name;
\tvar takenKeys, takenVals : array< int >;
\tvar takenDoms, takenAxes : array< name >;
\tvar axA : name;
\tvar i, j, id, cid, ck, plus, junk, cap, sumA, k2, verdict : int;
\tvar haveTarget : bool;

\tif( FRGW_IsPlaceholder( candidate ) )
\t\treturn 0;
\tif( candidate == itemsNames[ingredient] )
\t\treturn 0;
\tw = GetWitcherPlayer();
\thaveTarget = false;
\tcap = 0;
\tshapeTok = selectedSchematic.ingredients[0].itemName;
\tif( !FRGW_IsPlaceholder( shapeTok ) && w.FRG_FindForWork( shapeTok, blankId ) )
\t{
\t\thaveTarget = true;
\t\tcap = w.FRGL_BaseSlots( blankId );
\t\tif( w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 ) == 13 )
\t\t\tcap += 1;
\t}
\tcid = 0;
\tplus = 0;
\tjunk = 0;
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tid = FRGL_IdAt( i );
\t\tcard = FRGL_TokCard( id );
\t\tif( card == candidate )
\t\t\tcid = id;
\t\tfor( j = 0; j < itemsNames.Size(); j += 1 )
\t\t{
\t\t\tif( j == ingredient || itemsNames[j] != card )
\t\t\t\tcontinue;
\t\t\tif( card == candidate )
\t\t\t\treturn 1;
\t\t\ttakenKeys.PushBack( FRGL_StatKey( id ) );
\t\t\tif( FRGL_DomAxis( id ) != '' )
\t\t\t\ttakenDoms.PushBack( FRGL_DomAxis( id ) );
\t\t\tfor( k2 = 0; k2 < 4; k2 += 1 )
\t\t\t{
\t\t\t\tif( FRGL_PlusAxis( id * 4 + k2 ) == '' )
\t\t\t\t\tbreak;
\t\t\t\ttakenAxes.PushBack( FRGL_PlusAxis( id * 4 + k2 ) );
\t\t\t\ttakenVals.PushBack( FRGL_PlusVal( id * 4 + k2 ) );
\t\t\t}
\t\t\tif( FRGL_IsJunk( id ) )
\t\t\t\tjunk += 1;
\t\t\telse
\t\t\t\tplus += 1;
\t\t}
\t}
\tif( cid <= 0 )
\t\treturn 0;
\t// РОД И СЛОТ ТЕЛА — у судьи (коды 3 и 6 те же, что были здесь)
\tif( haveTarget )
\t{
\t\tverdict = FRGW_LineVerdict( cid, w.inv.GetItemCategory( blankId ),
\t\t\tw.inv.IsItemWeapon( blankId ), true );
\t\tif( verdict != 0 )
\t\t\treturn verdict;
\t}
\tck = FRGL_StatKey( cid );
\tif( ck > 0 && takenKeys.Contains( ck ) )
\t\treturn 1;
\t// I-2: one axis - one line. The dominant stat must be free on this item.
\tif( FRGL_DomAxis( cid ) != '' && takenDoms.Contains( FRGL_DomAxis( cid ) ) )
\t\treturn 4;
\t// I-3: the world envelope. No axis may exceed the most generous single
\t// Redux item - the forge lives INSIDE the world, never above it.
\tfor( j = 0; j < 4; j += 1 )
\t{
\t\taxA = FRGL_PlusAxis( cid * 4 + j );
\t\tif( axA == '' )
\t\t\tbreak;
\t\tsumA = FRGL_PlusVal( cid * 4 + j );
\t\tfor( i = 0; i < takenAxes.Size(); i += 1 )
\t\t{
\t\t\tif( takenAxes[i] == axA )
\t\t\t\tsumA += takenVals[i];
\t\t}
\t\tif( sumA > FRGL_AxisCap( axA ) )
\t\t\treturn 5;
\t}
\tif( haveTarget && !FRGL_IsJunk( cid ) )
\t{
\t\tcap += junk;
\t\tif( cap > 5 )
\t\t\tcap = 5;
\t\tif( plus + 1 > cap )
\t\t\treturn 2;
\t}
\treturn 0;
}

// Our axis slots always cycle.
@wrapMethod( CR4CraftingMenu ) function CanCycleIngredient( ingredient : int ) : bool
{
\tvar orig : name;

\torig = m_schematicListOriginal[selectedSchematicIndex].ingredients[ingredient].itemName;
\tif( FRGW_IsPlaceholder( orig ) )
\t\treturn true;
\treturn wrappedMethod( ingredient );
}

// Candidates for an axis slot: the placeholder itself (zero stock, the walker
// skips it) plus every token card of the axis tag. The line axis builds its
// pool straight from the registry (ids come free there): taken cards, content
// twins and over-budget pluses are left out - the wheel only offers what
// will actually seat.
@wrapMethod( CR4CraftingMenu ) function PickCompatibleIngredient( ingredient : int ) : name
{
\tvar w : W3PlayerWitcher;
\tvar blankId : SItemUniqueId;
\tvar orig, tag, shapeTok, card : name;
\tvar pool, all, takenNames, takenDoms, axNames : array< name >;
\tvar takenKeys, axSums : array< int >;
\tvar bagIds : array< SItemUniqueId >;
\tvar i, j, id, k2, plus, junk, cap, axJ, sumA : int;
\tvar haveTarget, roomPlus, wantArmor, capHit, gearArmed : bool;
\tvar gearCat : name;

\torig = m_schematicListOriginal[selectedSchematicIndex].ingredients[ingredient].itemName;
\tif( !FRGW_IsPlaceholder( orig ) )
\t\treturn wrappedMethod( ingredient );

\ttag = FRGW_AxisTag( orig );
\tpool.PushBack( orig );
\t// the WORK slot (properties, enchanting, mark, naming): the ring walks
\t// the player's own gear. Vanilla blades are welcome - enchanting is no
\t// longer a privilege of forged ones (user's call 07.09). Armour never
\t// shows up in a blade recipe: the FRG_Blank tag is shared by both.
\tif( tag == 'FRG_Blank' )
\t{
\t\tw = GetWitcherPlayer();
\t\tbagIds.Clear();
\t\t// WORN FIRST (user 09.09): the work slot almost always means the thing
\t\t// on Geralt right now, and scrolling the whole bag to reach it is a
\t\t// chore. Equipment goes into the ring ahead of everything else.
\t\tfor( i = 0; i <= 5; i += 1 )
\t\t{
\t\t\tif( w.FRG_Slot( i, blankId ) )
\t\t\t\tbagIds.PushBack( blankId );
\t\t}
\t\tw.inv.GetAllItems( bagIds );
\t\tfor( i = 0; i < bagIds.Size(); i += 1 )
\t\t{
\t\t\tif( !w.inv.IsIdValid( bagIds[i] ) )
\t\t\t\tcontinue;
\t\t\tif( !FRGW_FitsWorkSlot( selectedSchematic.schemName, w.inv.GetItemCategory( bagIds[i] ) ) )
\t\t\t\tcontinue;
\t\t\t// a look CARRIER is scenery, never a work piece
\t\t\tif( w.inv.ItemHasTag( bagIds[i], 'FRG_LookItem' ) )
\t\t\t\tcontinue;
\t\t\t// ⛔ ТОЛЬКО НАШЕ (требование ГД 18.09: «в том окошке должна быть
\t\t\t// только одна вещь: кованая заготовка»). Прежде кольцо ходило по
\t\t\t// всему гардеробу, и в него валились сапоги, поножи и вилы.
\t\t\tif( !w.inv.ItemHasTag( bagIds[i], 'FRG_Blank' )
\t\t\t\t&& !w.inv.ItemHasTag( bagIds[i], 'FRG_Forge' ) )
\t\t\t\tcontinue;
\t\t\t// a raw blank has no look worth changing - forge it instead
\t\t\tif( FRGW_IsArmorReskin( selectedSchematic.schemName )
\t\t\t\t&& StrFindFirst( NameToString( w.inv.GetItemName( bagIds[i] ) ), "FRG Blank " ) == 0 )
\t\t\t\tcontinue;
\t\t\t// enchanting: only relics, witcher blades and our own forgings
\t\t\tif( selectedSchematic.schemName == 'FRG Enchant schematic'
\t\t\t\t&& !FRGW_IsWorthyBlade( w, bagIds[i] ) )
\t\t\t\tcontinue;
\t\t\tcard = w.inv.GetItemName( bagIds[i] );
\t\t\tif( pool.Contains( card ) )
\t\t\t\tcontinue;
\t\t\tpool.PushBack( card );
\t\t}
\t\tj = pool.FindFirst( itemsNames[ingredient] );
\t\tif( j < 0 )
\t\t\tj = 0;
\t\tj += shiftIndex;
\t\tif( j >= pool.Size() )
\t\t\tj = 0;
\t\tif( j < 0 )
\t\t\tj = pool.Size() - 1;
\t\treturn pool[j];
\t}
\t// "take measurements": the ring is built from the player's own BAG -
\t// every item worth studying, with the placeholder first so the slot
\t// can go back to empty (user's call 07.09)
\tif( FRGW_IsStudyTag( tag ) )
\t{
\t\tw = GetWitcherPlayer();
\t\tbagIds.Clear();
\t\tw.inv.GetAllItems( bagIds );
\t\tfor( i = 0; i < bagIds.Size(); i += 1 )
\t\t{
\t\t\tif( !w.inv.IsIdValid( bagIds[i] ) )
\t\t\t\tcontinue;
\t\t\tif( !FRGW_StudyFits( tag, w.inv.GetItemCategory( bagIds[i] ) ) )
\t\t\t\tcontinue;
\t\t\t// our own blanks and forged gear are not donors
\t\t\tif( w.inv.ItemHasTag( bagIds[i], 'FRG_Blank' ) )
\t\t\t\tcontinue;
\t\t\t// nothing to take? then it does not clutter the ring
\t\t\tif( w.FRG_MeasureLeft( bagIds[i] ) <= 0 )
\t\t\t\tcontinue;
\t\t\tcard = w.inv.GetItemName( bagIds[i] );
\t\t\tif( pool.Contains( card ) )
\t\t\t\tcontinue;
\t\t\tpool.PushBack( card );
\t\t}
\t\tj = pool.FindFirst( itemsNames[ingredient] );
\t\tif( j < 0 )
\t\t\tj = 0;
\t\tj += shiftIndex;
\t\tif( j >= pool.Size() )
\t\t\tj = 0;
\t\tif( j < 0 )
\t\t\tj = pool.Size() - 1;
\t\treturn pool[j];
\t}
\t// the armour forge's BONUS slot walks its own ring: the vanilla walker
\t// skips the placeholder, so the slot could never go back to empty
\tif( tag == 'FRG_LineTok' && FRGW_IsArmorSchem( selectedSchematic.schemName ) )
\t{
\t\tw = GetWitcherPlayer();
\t\tcap = 0;
\t\tif( !FRGW_IsPlaceholder( selectedSchematic.ingredients[2].itemName ) )
\t\t\tcap = FRGAD_WeightByText( StrAfterFirst( NameToString( selectedSchematic.ingredients[2].itemName ), "FRG Def " ) );
\t\ttag = FRGW_ArmorCatOfSchem( selectedSchematic.schemName );
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tid = FRGL_IdAt( i );
\t\t\tcard = FRGL_TokCard( id );
\t\t\t// в бонус брони мусорные метки не идут; род и слот — у судьи
\t\t\tif( FRGL_IsJunk( id ) || FRGW_LineVerdict( id, tag, false, true ) != 0 )
\t\t\t\tcontinue;
\t\t\t// a weight-bound bonus only shows when it matches the protection
\t\t\tif( cap > 0 && FRGL_WeightTag( id ) != ''
\t\t\t\t&& FRGL_WeightTag( id ) != FRGW_WeightTagOf( cap ) )
\t\t\t\tcontinue;
\t\t\tif( w.inv.GetItemQuantityByName( card ) > 0
\t\t\t\t&& !FRGW_TakenElsewhere( card, ingredient ) )
\t\t\t\tpool.PushBack( card );
\t\t}
\t\tj = pool.FindFirst( itemsNames[ingredient] );
\t\tif( j < 0 )
\t\t\tj = 0;
\t\tj += shiftIndex;
\t\tif( j >= pool.Size() )
\t\t\tj = 0;
\t\tif( j < 0 )
\t\t\tj = pool.Size() - 1;
\t\treturn pool[j];
\t}
\tif( tag == 'FRG_LineTok' )
\t{
\t\tw = GetWitcherPlayer();
\t\thaveTarget = false;
\t\tplus = 0;
\t\tjunk = 0;
\t\tcap = 0;
\t\tshapeTok = selectedSchematic.ingredients[0].itemName;
\t\tif( !FRGW_IsPlaceholder( shapeTok ) && w.FRG_FindForWork( shapeTok, blankId ) )
\t\t{
\t\t\thaveTarget = true;
\t\t\tcap = w.FRGL_BaseSlots( blankId );
\t\t\tif( w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 ) == 13 )
\t\t\t\tcap += 1;
\t\t}
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tid = FRGL_IdAt( i );
\t\t\tcard = FRGL_TokCard( id );
\t\t\tfor( j = 0; j < itemsNames.Size(); j += 1 )
\t\t\t{
\t\t\t\tif( j == ingredient || itemsNames[j] != card )
\t\t\t\t\tcontinue;
\t\t\t\ttakenNames.PushBack( card );
\t\t\t\ttakenKeys.PushBack( FRGL_StatKey( id ) );
\t\t\t\tif( FRGL_DomAxis( id ) != '' )
\t\t\t\t\ttakenDoms.PushBack( FRGL_DomAxis( id ) );
\t\t\t\tfor( k2 = 0; k2 < 4; k2 += 1 )
\t\t\t\t{
\t\t\t\t\tif( FRGL_PlusAxis( id * 4 + k2 ) == '' )
\t\t\t\t\t\tbreak;
\t\t\t\t\taxJ = axNames.FindFirst( FRGL_PlusAxis( id * 4 + k2 ) );
\t\t\t\t\tif( axJ < 0 )
\t\t\t\t\t{
\t\t\t\t\t\taxNames.PushBack( FRGL_PlusAxis( id * 4 + k2 ) );
\t\t\t\t\t\taxSums.PushBack( FRGL_PlusVal( id * 4 + k2 ) );
\t\t\t\t\t}
\t\t\t\t\telse
\t\t\t\t\t\taxSums[axJ] = axSums[axJ] + FRGL_PlusVal( id * 4 + k2 );
\t\t\t\t}
\t\t\t\tif( FRGL_IsJunk( id ) )
\t\t\t\t\tjunk += 1;
\t\t\t\telse
\t\t\t\t\tplus += 1;
\t\t\t}
\t\t}
\t\tcap += junk;
\t\tif( cap > 5 )
\t\t\tcap = 5;
\t\troomPlus = !haveTarget || plus < cap;
\t\t// what are we building - a blade or a piece of armour? Armour lines
\t\t// must never show up on a sword and the other way round.
\t\twantArmor = false;
\t\tgearCat = '';
\t\tgearArmed = false;
\t\tif( haveTarget )
\t\t{
\t\t\tgearArmed = w.inv.IsItemWeapon( blankId );
\t\t\twantArmor = !gearArmed;
\t\t\tgearCat = w.inv.GetItemCategory( blankId );
\t\t}
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tid = FRGL_IdAt( i );
\t\t\tcard = FRGL_TokCard( id );
\t\t\tif( card == itemsNames[ingredient] )
\t\t\t{
\t\t\t\tpool.PushBack( card );
\t\t\t\tcontinue;
\t\t\t}
\t\t\t// ⛔ РОД СПРАШИВАЕМ У СУДЬИ. Раньше здесь стоял свой фильтр под
\t\t\t// условием «вещь выбрана»: пока квадрат вещи пуст, он не
\t\t\t// срабатывал вовсе, и кольцо крутило броню в наборе для меча.
\t\t\tif( !FRGW_LineFitsGear( id, gearCat, gearArmed, haveTarget ) )
\t\t\t\tcontinue;
\t\t\tif( takenNames.Contains( card ) )
\t\t\t\tcontinue;
\t\t\tk2 = FRGL_StatKey( id );
\t\t\tif( k2 > 0 && takenKeys.Contains( k2 ) )
\t\t\t\tcontinue;
\t\t\t// I-2: dominant axis already forged in - not offered
\t\t\tif( FRGL_DomAxis( id ) != '' && takenDoms.Contains( FRGL_DomAxis( id ) ) )
\t\t\t\tcontinue;
\t\t\t// I-3: would any axis overflow the world envelope? Not offered either
\t\t\tcapHit = false;
\t\t\tfor( k2 = 0; k2 < 4; k2 += 1 )
\t\t\t{
\t\t\t\tif( FRGL_PlusAxis( id * 4 + k2 ) == '' )
\t\t\t\t\tbreak;
\t\t\t\tsumA = FRGL_PlusVal( id * 4 + k2 );
\t\t\t\taxJ = axNames.FindFirst( FRGL_PlusAxis( id * 4 + k2 ) );
\t\t\t\tif( axJ >= 0 )
\t\t\t\t\tsumA += axSums[axJ];
\t\t\t\tif( sumA > FRGL_AxisCap( FRGL_PlusAxis( id * 4 + k2 ) ) )
\t\t\t\t{
\t\t\t\t\tcapHit = true;
\t\t\t\t\tbreak;
\t\t\t\t}
\t\t\t}
\t\t\tif( capHit )
\t\t\t\tcontinue;
\t\t\tif( !roomPlus && !FRGL_IsJunk( id ) )
\t\t\t\tcontinue;
\t\t\tpool.PushBack( card );
\t\t}
\t\treturn GetArrayNextIngredient( pool, ingredient );
\t}
\tif( tag == 'FRG_FlawTok' )
\t{
\t\t// the flaw slot must be able to go BACK to empty: the vanilla walker
\t\t// skips the placeholder (nothing of that name is in the bag), so we
\t\t// step through the ring ourselves - placeholder first, then the marks.
\t\tfor( i = 1; i <= FRGF_Count(); i += 1 )
\t\t{
\t\t\t// ⛔ ТОЛЬКО РЕЛИКТОВЫЕ ПОРОКИ (решение ГД 18.09): лёгкие давали
\t\t\t// обычное место и в кольце только мешались.
\t\t\tif( FRGF_Weight( FRGF_IdAt( i ) ) != 2 )
\t\t\t\tcontinue;
\t\t\tcard = FRGF_TokCard( FRGF_IdAt( i ) );
\t\t\tif( thePlayer.inv.GetItemQuantityByName( card ) > 0 )
\t\t\t\tpool.PushBack( card );
\t\t}
\t\tj = pool.FindFirst( itemsNames[ingredient] );
\t\tif( j < 0 )
\t\t\tj = 0;
\t\tj += shiftIndex;
\t\tif( j >= pool.Size() )
\t\t\tj = 0;
\t\tif( j < 0 )
\t\t\tj = pool.Size() - 1;
\t\treturn pool[j];
\t}
\tall = theGame.GetDefinitionsManager().GetItemsWithTag( tag );
\tfor( i = 0; i < all.Size(); i += 1 )
\t{
\t\t// the "native look" mark shares the armour look axes with the FORGE,
\t\t// where it means nothing - offered only where it works
\t\tif( theGame.GetDefinitionsManager().ItemHasTag( all[i], 'FRG_Native' )
\t\t\t&& !FRGW_IsArmorReskin( selectedSchematic.schemName )
\t\t\t&& selectedSchematic.schemName != 'FRG Reskin schematic' )
\t\t\tcontinue;
\t\tif( !FRGW_TakenElsewhere( all[i], ingredient ) )
\t\t\tpool.PushBack( all[i] );
\t}
\treturn GetArrayNextIngredient( pool, ingredient );
}

// The ingredient popup: vanilla only knows its material categories, so on our
// axis slots it showed garbage. Build our own popup data: the axis tag as the
// filter, plus everything standing in ANOTHER slot of this schematic as
// forbidden - the same road the alchemy window drives.
// ⛔ СУДЬЯ РОДА СТРОКИ. Его спрашивают и кольцо, и список выбора —
// чтобы правило жило в ОДНОМ месте, а не переписывалось своими словами
// в каждой новой ветке интерфейса (ГД 17.09: «проходили много раз»).
// ЕДИНСТВЕННЫЙ СУДЬЯ РОДА. Вердикт числом, чтобы каждое место могло
// сказать игроку своё: 0 годится | 3 не тот род (броня <-> оружие) |
// 6 чужой слот тела | 7 вещь ещё не выбрана.
// ⛔ FRGL_IsArmorLine / FRGL_Cat вне этой функции звать НЕЛЬЗЯ — это
// ловит lint_methods.py. Протечка броневых свойств в мечи возвращалась
// именно потому, что правило жило в семи копиях.
function FRGW_LineVerdict( lineId : int, gearCat : name, isWeapon : bool, gearPicked : bool ) : int
{
\tif( FRGL_IsJunk( lineId ) )
\t\treturn 0;
\tif( !gearPicked )
\t\treturn 7;
\tif( FRGL_IsArmorLine( lineId ) )
\t{
\t\tif( isWeapon )
\t\t\treturn 3;
\t\t// нагрудный бонус не место на перчатках: в Redux один и тот же
\t\t// бафф на теле вдвое сильнее, чем на остальных трёх слотах
\t\tif( FRGL_Cat( lineId ) != '' && FRGL_Cat( lineId ) != gearCat )
\t\t\treturn 6;
\t\treturn 0;
\t}
\t// оружейная строка — только на оружие, в том числе вспомогательное
\tif( !isWeapon )
\t\treturn 3;
\treturn 0;
}

function FRGW_LineFitsGear( lineId : int, gearCat : name, isWeapon : bool, gearPicked : bool ) : bool
{
\treturn FRGW_LineVerdict( lineId, gearCat, isWeapon, gearPicked ) == 0;
}


@wrapMethod( CR4CraftingMenu ) function OpenIngredientSelectionPopup()
{
\tvar popupData : W3ItemSelectionPopupData;
\tvar frame : W3PopupData;
\tvar orig, card, shapeTok, gearCat : name;
\tvar tags, forbiddenTags, forbiddenItems : array< name >;
\tvar twinKeys : array< int >;
\tvar i, j, id : int;
\tvar w : W3PlayerWitcher;
\tvar blankId : SItemUniqueId;
\tvar haveTarget, gearArmed : bool;

\torig = m_schematicListOriginal[selectedSchematicIndex].ingredients[selectedIngredient].itemName;
\tif( !FRGW_IsPlaceholder( orig ) )
\t{
\t\twrappedMethod();
\t\treturn;
\t}
\ttags.PushBack( FRGW_AxisTag( orig ) );
\tforbiddenItems.PushBack( selectedSchematic.craftedItemName );
\tfor( i = 0; i < itemsNames.Size(); i += 1 )
\t{
\t\tif( i != selectedIngredient && !FRGW_IsPlaceholder( itemsNames[i] ) )
\t\t\tforbiddenItems.PushBack( itemsNames[i] );
\t}
\t// content twins of the seated tokens hide from the popup too
\tif( orig == 'frg_slot_line' )
\t{
\t\t// ⛔ В СПИСКЕ ВЫБОРА ФИЛЬТРА РОДА НЕ БЫЛО НИКОГДА: он показывал
\t\t// броневые строки при любой цели. Отдаём запрет движку — тогда
\t\t// чужая строка в списке попросту невозможна.
\t\tw = GetWitcherPlayer();
\t\tgearCat = '';
\t\tgearArmed = false;
\t\thaveTarget = false;
\t\tshapeTok = m_schematicListOriginal[selectedSchematicIndex].ingredients[0].itemName;
\t\tif( w && !FRGW_IsPlaceholder( shapeTok ) && w.FRG_FindForWork( shapeTok, blankId ) )
\t\t{
\t\t\thaveTarget = true;
\t\t\tgearCat = w.inv.GetItemCategory( blankId );
\t\t\tgearArmed = w.inv.IsItemWeapon( blankId );
\t\t}
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tid = FRGL_IdAt( i );
\t\t\tif( !FRGW_LineFitsGear( id, gearCat, gearArmed, haveTarget ) )
\t\t\t\tforbiddenItems.PushBack( FRGL_TokCard( id ) );
\t\t\tcard = FRGL_TokCard( id );
\t\t\tfor( j = 0; j < itemsNames.Size(); j += 1 )
\t\t\t{
\t\t\t\tif( j != selectedIngredient && itemsNames[j] == card )
\t\t\t\t\ttwinKeys.PushBack( FRGL_StatKey( id ) );
\t\t\t}
\t\t}
\t\tif( twinKeys.Size() > 0 )
\t\t{
\t\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t\t{
\t\t\t\tid = FRGL_IdAt( i );
\t\t\t\tif( twinKeys.Contains( FRGL_StatKey( id ) ) )
\t\t\t\t\tforbiddenItems.PushBack( FRGL_TokCard( id ) );
\t\t\t}
\t\t}
\t}
\tpopupData = new W3ItemSelectionPopupData in theGame.GetGuiManager();
\tpopupData.overrideQuestItemRestrictions = true;
\tpopupData.selectionMode = EISPM_Crafting;
\ttheInput.UnregisterListener( this, 'IngredientShift' );
\tpopupData.filterTagsList = tags;
\tpopupData.filterForbiddenTagsList = forbiddenTags;
\tpopupData.forbiddenItems = forbiddenItems;
\tpopupData.checkTagsOR = false;
\tframe = new W3PopupData in theGame.GetGuiManager();
\tpopupData.craftingMenuCallBack = this;
\tpopupData.frame = frame;
\tRequestSubMenu( 'PopupMenu', frame );
\ttheGame.RequestPopup( 'ItemSelectionPopup', popupData );
}

// Belt and braces: even if a taken token sneaks past the popup filter, refuse
// to seat it into a second slot. Our slots only - vanilla recipes legally
// repeat materials.
@wrapMethod( CR4CraftingMenu ) function IngredientSelectionPopupChangeIngredient( itemName : name )
{
\tvar orig : name;
\tvar deny : int;

\torig = m_schematicListOriginal[selectedSchematicIndex].ingredients[selectedIngredient].itemName;
\tif( FRGW_IsPlaceholder( orig ) )
\t{
\t\tdeny = 0;
\t\tif( orig == 'frg_slot_line' )
\t\t\tdeny = FRGW_LineDeny( itemName, selectedIngredient );
\t\telse if( FRGW_TakenElsewhere( itemName, selectedIngredient ) )
\t\t\tdeny = 1;
\t\tif( deny == 1 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_dup_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t\tif( deny == 2 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_full_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t\tif( deny == 3 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_kind_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t\tif( deny == 4 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_axis_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t\tif( deny == 5 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_cap_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t\tif( deny == 6 )
\t\t{
\t\t\tshowNotification( GetLocStringByKeyExt( "frgu_slot_deny" ) );
\t\t\tOnPlaySoundEvent( "gui_global_denied" );
\t\t\treturn;
\t\t}
\t}
\twrappedMethod( itemName );
}

// The preview must show a REAL card and dodge the vanilla string trick that
// expects the crafted name to end with a quality digit.
@wrapMethod( CR4CraftingMenu ) function AdjustItemType()
{
\tvar shapeTok, forgedName, pcat : name;
\tvar want : string;

\tif( selectedSchematic.schemName == 'FRG Engrave schematic'
\t\t|| selectedSchematic.schemName == 'FRG Upgrade2 schematic'
\t\t|| selectedSchematic.schemName == 'FRG Upgrade3 schematic'
\t\t|| selectedSchematic.schemName == 'FRG Upgrade4 schematic'
\t\t|| selectedSchematic.schemName == 'FRG Enchant schematic'
\t\t|| selectedSchematic.schemName == 'FRG Mark schematic'
\t\t|| selectedSchematic.schemName == 'FRG Name schematic' )
\t{
\t\t// preview the chosen blade itself
\t\titemAdjustedName = 'FRG Blank Steel Sword';
\t\tshapeTok = selectedSchematic.ingredients[0].itemName;
\t\tif( !FRGW_IsPlaceholder( shapeTok ) )
\t\t\titemAdjustedName = shapeTok;
\t\treturn;
\t}
\t// все семь заготовок разом. Для броневых это не косметика: без
\t// своей ветки они уходят в динамику W3EE, где имя режется по
\t// последнему символу и схеме переписывается уровень мастера
\tif( FRGW_BlankOfSchem( selectedSchematic.schemName ) != '' )
\t{
\t\titemAdjustedName = FRGW_BlankOfSchem( selectedSchematic.schemName );
\t\treturn;
\t}
\tif( selectedSchematic.schemName == 'FRG ForgeArmor schematic'
\t\t|| selectedSchematic.schemName == 'FRG ForgePants schematic'
\t\t|| selectedSchematic.schemName == 'FRG ForgeGloves schematic'
\t\t|| selectedSchematic.schemName == 'FRG ForgeBoots schematic' )
\t{
\t\t// the blank of this very schematic until a shape is picked
\t\titemAdjustedName = selectedSchematic.ingredients[0].itemName;
\t\tshapeTok = selectedSchematic.ingredients[1].itemName;
\t\tif( !FRGW_IsPlaceholder( shapeTok ) )
\t\t{
\t\t\twant = "FRG Forged " + StrAfterFirst( NameToString( shapeTok ), "FRG Shape " );
\t\t\tif( FRGW_FindTokCard( 'FRG_Forge', want, forgedName ) )
\t\t\t\titemAdjustedName = forgedName;
\t\t}
\t\treturn;
\t}
\tif( selectedSchematic.schemName == 'FRG ForgeSide schematic' )
\t{
\t\t// sidearm forging: the forged card keeps the DONOR's category, so the
\t\t// metal fork never matches and the fallback returns the native card
\t\titemAdjustedName = 'FRG Blank Secondary';
\t\tshapeTok = selectedSchematic.ingredients[1].itemName;
\t\tif( !FRGW_IsPlaceholder( shapeTok )
\t\t\t&& FRGW_ForgedFor( StrAfterFirst( NameToString( shapeTok ), "FRG Shape " ), 'secondary', forgedName ) )
\t\t\titemAdjustedName = forgedName;
\t\treturn;
\t}
\tif( selectedSchematic.schemName == 'FRG ForgeBlade schematic' )
\t{
\t\t// preview the ACTUAL forged card of the chosen shape; the blank until
\t\t// a shape is scrolled in
\t\titemAdjustedName = 'FRG Blank Steel Sword';
\t\tshapeTok = selectedSchematic.ingredients[1].itemName;
\t\tif( !FRGW_IsPlaceholder( shapeTok ) )
\t\t{
\t\t\t// preview follows the metal of the picked blank (steel by default)
\t\t\tpcat = 'steelsword';
\t\t\tif( !FRGW_IsPlaceholder( selectedSchematic.ingredients[0].itemName ) )
\t\t\t\tpcat = theGame.GetDefinitionsManager().GetItemCategory( selectedSchematic.ingredients[0].itemName );
\t\t\tif( FRGW_ForgedFor( StrAfterFirst( NameToString( shapeTok ), "FRG Shape " ), pcat, forgedName ) )
\t\t\t\titemAdjustedName = forgedName;
\t\t}
\t\treturn;
\t}
\twrappedMethod();
}

// The Craft button. Our schematic TRANSFORMS the player's own blank instead
// of crafting a new item: grooves, lines and marks already on it survive.
@addMethod( W3CraftingManager ) function FRG_CraftEngrave( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar kinSeen : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard, verdict : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;\t// the item being rebuilt
\t\tif( FRGW_IsPlaceholder( shapeTok ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Pick the item to rebuild - the first slot", 9000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t\treturn ECE_TooFewIngredients;

\t\t// the picked SET: duplicates collapse, placeholders are empty slots
\t\tpicks.Clear();
\t\tfor( i = 1; i < schem.ingredients.Size(); i += 1 )
\t\t{
\t\t\tk = FRGL_OfTokCard( schem.ingredients[i].itemName );
\t\t\tif( k > 0 && !picks.Contains( k ) )
\t\t\t\tpicks.PushBack( k );
\t\t}

\t\t// guards over the whole set: home, weight class, curse bond, relic-
\t\t// exclusive; count pluses and junk while at it
\t\twant_i = 0;\t// plus-properties picked
\t\tj = 0;\t\t// junk marks picked
\t\tk = 0;\t\t// relic properties picked
\t\tfor( i = 0; i < picks.Size(); i += 1 )
\t\t{
\t\t\t// ⛔ РОД — У СУДЬИ. Прежде здесь «клинком» считались только сталь и
\t\t\t// серебро, а вспомогательное оружие — бронёй: оружейное свойство
\t\t\t// на топор отвергалось как «не подходит броне».
\t\t\tverdict = FRGW_LineVerdict( picks[i], w.inv.GetItemCategory( blankId ),
\t\t\t\tw.inv.IsItemWeapon( blankId ), true );
\t\t\tif( verdict == 3 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "This property is for another kind of gear: " + FRGL_Title( picks[i] ), 10000 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\tif( verdict == 6 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "That bonus came off another body slot: " + FRGL_Title( picks[i] ), 11000 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\tif( FRGL_WeightTag( picks[i] ) != '' && !w.inv.ItemHasTag( blankId, FRGL_WeightTag( picks[i] ) ) )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "Tailored for another armour weight class: " + FRGL_Title( picks[i] ), 10000 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\tif( FRGL_IsCursed( picks[i] ) && w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 ) != 13 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "This gift demands its curse - enchant the Dark Curse first: " + FRGL_Title( picks[i] ), 12000 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\t// ⛔ СЧЁТ ЧЕСТНЫЙ, ПО СТРОКАМ. Прежняя поблажка «половины одного
\t\t\t// донора считаем за один реликт» открыла дыру: с двух мечей
\t\t\t// складывались четыре реликтовых свойства. Копию донора теперь
\t\t\t// обеспечивает базовый предел в две штуки, а не поблажка.
\t\t\tif( FRGL_IsRelic( picks[i] ) )
\t\t\t\tk += 1;
\t\t\tif( FRGL_IsJunk( picks[i] ) )
\t\t\t\tj += 1;
\t\t\telse
\t\t\t\twant_i += 1;
\t\t}
\t\t// RELIC properties: one per blade, TWO if a heavy flaw mark was forged
\t\t// into it at birth (design doc: a fat price buys a fat reward)
\t\tif( k > w.FRGL_RelicLimit( blankId ) )
\t\t{
\t\t\tif( w.FRGL_RelicLimit( blankId ) > 1 )
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "This blade holds two RELIC properties - you picked " + k, 12000 );
\t\t\telse
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "A RELIC property is exclusive - one per blade. A HEAVY flaw mark at the forge buys a second one (picked " + k + ")", 13000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// slot budget of the FUTURE state: tier base + picked junk (+1 for the
\t\t// Dark Curse), hard cap 5
\t\tk = w.FRGL_BaseSlots( blankId ) + j;
\t\tif( w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 ) == 13 )
\t\t\tk += 1;
\t\tif( k > 5 )
\t\t\tk = 5;
\t\tif( want_i > k )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Picked " + want_i + " plus-properties, the item holds " + k + " - the next tier or a junk mark opens more", 13000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// I-2: one axis - one line; I-3: the world envelope (approved: "go")
\t\taxNames.Clear();
\t\taxSums.Clear();
\t\tfor( i = 0; i < picks.Size(); i += 1 )
\t\t{
\t\t\tif( FRGL_DomAxis( picks[i] ) != '' )
\t\t\t{
\t\t\t\tif( axDoms.Contains( FRGL_DomAxis( picks[i] ) ) )
\t\t\t\t{
\t\t\t\t\ttheGame.GetGuiManager().ShowNotification( "One axis - one line: " + FRGL_Title( picks[i] ) + " doubles an axis already in the set", 12000 );
\t\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t\t}
\t\t\t\taxDoms.PushBack( FRGL_DomAxis( picks[i] ) );
\t\t\t}
\t\t\tfor( j = 0; j < 4; j += 1 )
\t\t\t{
\t\t\t\tif( FRGL_PlusAxis( picks[i] * 4 + j ) == '' )
\t\t\t\t\tbreak;
\t\t\t\tk2 = axNames.FindFirst( FRGL_PlusAxis( picks[i] * 4 + j ) );
\t\t\t\tif( k2 < 0 )
\t\t\t\t{
\t\t\t\t\taxNames.PushBack( FRGL_PlusAxis( picks[i] * 4 + j ) );
\t\t\t\t\taxSums.PushBack( FRGL_PlusVal( picks[i] * 4 + j ) );
\t\t\t\t}
\t\t\t\telse
\t\t\t\t\taxSums[k2] = axSums[k2] + FRGL_PlusVal( picks[i] * 4 + j );
\t\t\t}
\t\t}
\t\tfor( i = 0; i < axNames.Size(); i += 1 )
\t\t{
\t\t\tif( axSums[i] > FRGL_AxisCap( axNames[i] ) )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "The world envelope: axis sum " + axSums[i] + " exceeds the most generous Redux item (" + FRGL_AxisCap( axNames[i] ) + ")", 13000 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t}

\t\t// REBUILD: strip every registry property, then lay the picked set
\t\tprops.Clear();
\t\tw.inv.GetItemAbilities( blankId, props );
\t\tfor( i = 0; i < props.Size(); i += 1 )
\t\t{
\t\t\tif( FRGL_FromAbility( props[i] ) > 0 )
\t\t\t\tw.FRG_StripAb( blankId, props[i] );
\t\t}
\t\tfor( i = 0; i < picks.Size(); i += 1 )
\t\t\tw.inv.AddItemCraftedAbility( blankId, FRGL_Ability( picks[i] ), false );
\t\t// the bonus forged into a piece at its birth is part of the piece,
\t\t// not of the property set - the rebuild must not shave it off
\t\tk2 = w.inv.GetItemModifierInt( blankId, 'FRG_ArmBuff', 0 );
\t\tif( k2 > 0 && !picks.Contains( k2 ) )
\t\t\tw.inv.AddItemCraftedAbility( blankId, FRGL_Ability( k2 ), false );

\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\titem = blankId;
\t\tw.FRGL_CountOn( blankId, i, j );
\t\ttheGame.GetGuiManager().ShowNotification( "The property set is forged: " + i + " plus / " + j
\t\t\t+ " junk (limit " + w.FRGL_Limit( blankId ) + "). Tokens are knowledge - kept.", 13000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftEnchant( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;\t// the blade
\t\tfxTok = schem.ingredients[1].itemName;
\t\tif( FRGW_IsPlaceholder( shapeTok ) || FRGW_IsPlaceholder( fxTok ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t\treturn ECE_TooFewIngredients;
\t\t// relic effects are WEAPON-only in W3EE (IsItemWeapon gate)
\t\tif( w.inv.GetItemCategory( blankId ) != 'steelsword'
\t\t\t&& w.inv.GetItemCategory( blankId ) != 'silversword' )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Relic effects belong to weapons - armour carries none in W3EE", 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// ...and only a WORTHY blade takes one: a relic, a witcher school
\t\t// sword or something forged here. Otherwise the slot would make the
\t\t// player scroll a hundred junk swords (user's call 07.09).
\t\tif( !FRGW_IsWorthyBlade( w, blankId ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "A red line is laid on a relic or a witcher blade, not on a common sword", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// no tier gate any more (user's call 07.09): a red line may be laid
\t\t// on ANY blade, not only on one forged here
\t\tk = FRGFx_OfTokCard( fxTok );
\t\tif( k <= 0 )
\t\t\treturn ECE_TooFewIngredients;
\t\t// A blade that already carries a charm takes the new one anyway: the
\t\t// old is REPLACED (user 13.09). Native charms live in the card's tag
\t\t// and cannot be erased, so the swap happens where the buff is hung -
\t\t// HandleRelicAbilities drops the native buff whenever ours is set.
\t\tif( w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 ) == k )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "This blade already carries that very red line", 9000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// the buff of whatever it wore before goes down right now
\t\ti = w.inv.GetItemModifierInt( blankId, 'FRG_Fx', 0 );
\t\tif( i <= 0 )
\t\t\ti = w.FRG_FxCodeOf( w.inv.GetItemName( blankId ) );
\t\tif( i > 0 )
\t\t\tw.RemoveBuff( w.FRG_FxType( i ), false, "RelicWeaponBuff" );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Fx', k );
\t\tw.FRG_FxStamp( blankId );
\t\t// engraving used to hang the buff on the mere fact the blade sat in a
\t\t// SLOT - engrave the silver one while holding steel and its charm was
\t\t// live at once. The buff belongs to the blade in hand, nothing else.
\t\tw.FRG_FxRefresh();
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\titem = blankId;
\t\tif( k == 13 )
\t\t\ttheGame.GetGuiManager().ShowNotification( "CURSED FORGING: the Dark Curse settles in - it will feed on you between fights, but the blade gains +1 line slot ("
\t\t\t\t+ w.FRGL_Limit( blankId ) + " now)", 15000 );
\t\telse
\t\t\ttheGame.GetGuiManager().ShowNotification( "The red line settles onto the blade. The effect token is knowledge - kept.", 12000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftMark( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;\t// the blade
\t\tdmgTok = schem.ingredients[1].itemName;\t\t// the stamp
\t\tif( FRGW_IsPlaceholder( shapeTok ) || FRGW_IsPlaceholder( dmgTok ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( w.FRGP_TierOf( blankId ) < 4 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "The maker signs finished work: relic tier (upgrade III) first", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tk = FRGT_OfStampCard( dmgTok );
\t\tif( k <= 0 )
\t\t\treturn ECE_TooFewIngredients;
\t\t// one mark per blade; a SECOND only for a fully assembled piece
\t\t// ONE mark per blade, full stop (design doc 23.08: the old "second mark
\t\t// for a fully assembled piece" rule only confused the reading)
\t\tif( w.FRGT_Count( blankId ) >= 1 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "One maker's mark per blade - this one already carries it", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tif( w.FRG_CountAb( blankId, FRGT_Ability( k ) ) > 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "This exact mark is already burned in - pick another stamp", 9000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tw.inv.AddItemCraftedAbility( blankId, FRGT_Ability( k ), false );
\t\tif( w.FRG_CountAb( blankId, FRGT_Ability( k ) ) <= 0 )
\t\t\treturn ECE_TooFewIngredients;
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\titem = blankId;
\t\ttheGame.GetGuiManager().ShowNotification( FRGT_Title( k ) + " (" + FRGT_Stats( k ) + ") burned into "
\t\t\t+ w.inv.GetItemName( blankId ) + ". No line slot spent; the stamp stays.", 13000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftArmor( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard, verdict : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\t// the verdict is printed only when its TEXT changes, so a second
\t\t// press used to stay silent - clear the memory before asking
\t\tw.FRG_LastWhy = "";
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[1].itemName;\t// the LOOK
\t\tdmgTok = schem.ingredients[2].itemName;\t\t// the BACKBONE token
\t\t// THREE elements of a piece (user 15.09): the look, the BACKBONE
\t\t// (armour value + resistances + weight class - one inseparable
\t\t// thing in Redux) and the unique bonus, which may stay empty.
\t\tresTok = '';
\t\tlineTok = '';
\t\tif( schem.ingredients.Size() > 3 && !FRGW_IsPlaceholder( schem.ingredients[3].itemName ) )
\t\t\tlineTok = schem.ingredients[3].itemName;
\t\tif( FRGW_IsPlaceholder( shapeTok ) || FRGW_IsPlaceholder( dmgTok ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Armour forging needs a blank, a LOOK and a PROTECTION token; the bonus square may stay empty", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tif( !w.FRG_TakeForForge( schem.ingredients[0].itemName, blankId ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: no blank of this kind at all - " + schem.ingredients[0].itemName, 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// the look decides the CARD; the armour value decides ARMOR and CLASS
\t\twant = StrAfterFirst( NameToString( dmgTok ), "FRG Def " );
\t\tfdab = FRGAD_AbilityByText( want );
\t\tif( fdab == '' )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: no armour value known for [" + want + "] - pick another protection token", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// the "native look" mark belongs to the reskin recipes, not here
\t\tif( shapeTok == 'FRG Shape Native' )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "That mark restores a piece's own look - it is not a look to forge with", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tforgedName = '';
\t\tFRGW_FindTokCard( 'FRG_Forge', "FRG Forged " + StrAfterFirst( NameToString( shapeTok ), "FRG Shape " ), forgedName );
\t\tif( forgedName == '' )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: no forged card for the look [" + StrAfterFirst( NameToString( shapeTok ), "FRG Shape " ) + "]", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\ttoks = w.inv.AddAnItem( forgedName, 1 );
\t\tif( toks.Size() <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the forged card refused to spawn - " + forgedName, 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\titem = toks[0];
\t\tw.inv.SetItemModifierInt( item, 'FRG_Tier', 4 );
\t\tw.inv.SetItemModifierInt( item, 'ItemQualityModified', 1 );
\t\tfor( i = 2; i <= 4; i += 1 )
\t\t{
\t\t\tif( w.FRG_CountAb( item, FRGP_QAbility( i ) ) <= 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGP_QAbility( i ), false );
\t\t}
\t\t// the engine may refuse more sockets (armour often does): a plain
\t\t// while() here hung the whole game (user 05.09) - bail out instead
\t\tslotGuard = w.inv.GetItemEnhancementSlotsCount( item );
\t\twhile( slotGuard < 3 )
\t\t{
\t\t\tw.inv.AddSlot( item );
\t\t\tif( w.inv.GetItemEnhancementSlotsCount( item ) <= slotGuard )
\t\t\t\tbreak;
\t\t\tslotGuard = w.inv.GetItemEnhancementSlotsCount( item );
\t\t}
\t\tw.inv.AddItemCraftedAbility( item, fdab, false );
\t\t// the weight class rides the protection: stored as a NUMBER (survives
\t\t// saves), applied as an instance tag now and re-applied on every spawn
\t\ti = FRGAD_WeightByText( want );
\t\tif( i > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( item, 'FRG_Weight', i );
\t\t\tw.inv.AddItemTag( item, FRGW_WeightTagOf( i ) );
\t\t}
\t\t// resistances need no step of their own any more: they sit inside
\t\t// the protection ability, poured in above (user 15.09)
\t\t// the UNIQUE BONUS: one armour line, forged in at birth
\t\tif( lineTok != '' )
\t\t{
\t\t\tk = FRGL_OfTokCard( lineTok );
\t\t\tverdict = 0;
\t\t\tif( k > 0 )
\t\t\t\tverdict = FRGW_LineVerdict( k, FRGW_ArmorCatOfSchem( schemName ), false, true );
\t\t\tif( k <= 0 || FRGL_IsJunk( k ) || verdict == 3 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "That property belongs on a blade, not on armour - pick an armour bonus", 10000 );
\t\t\t\tw.inv.RemoveItem( item, 1 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\tif( verdict == 6 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "That bonus came off another body slot - pick one from this kind of piece", 11000 );
\t\t\t\tw.inv.RemoveItem( item, 1 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\t// the weight class comes from the PROTECTION token, never from
\t\t\t// the blank (all four blanks inherit LightArmor from the sample)
\t\t\tif( FRGL_WeightTag( k ) != ''
\t\t\t\t&& FRGL_WeightTag( k ) != FRGW_WeightTagOf( FRGAD_WeightByText( want ) ) )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "This bonus belongs to another weight class - match it to the protection you picked", 11000 );
\t\t\t\tw.inv.RemoveItem( item, 1 );
\t\t\t\treturn ECE_TooFewIngredients;
\t\t\t}
\t\t\tw.inv.AddItemCraftedAbility( item, FRGL_Ability( k ), false );
\t\t\t// remember it: the property workshop must not shave it off later
\t\t\tw.inv.SetItemModifierInt( item, 'FRG_ArmBuff', k );
\t\t}
\t\tw.FRGP_PourTier( item );
\t\t// lines and marks engraved into the blank carry over
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tk = FRGL_IdAt( i );
\t\t\tif( w.FRG_CountAb( blankId, FRGL_Ability( k ) ) > 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGL_Ability( k ), false );
\t\t}
\t\tfor( i = 1; i <= 4; i += 1 )
\t\t{
\t\t\tif( w.FRG_CountAb( blankId, FRGT_Ability( i ) ) > 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGT_Ability( i ), false );
\t\t}
\t\tw.inv.RemoveItem( blankId, 1 );
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\ttheGame.GetGuiManager().ShowNotification( "The armour is forged: RELIC quality, full protection, "
\t\t\t+ w.FRGL_Limit( item ) + " property slots, 3 rune sockets. Tokens are knowledge - kept.", 15000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftName( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;\t// the blade
\t\tdmgTok = schem.ingredients[1].itemName;\t\t// word 1
\t\tfxTok = schem.ingredients[2].itemName;\t\t// word 2
\t\tif( FRGW_IsPlaceholder( shapeTok ) || FRGW_IsPlaceholder( dmgTok ) || FRGW_IsPlaceholder( fxTok ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.inv.ItemHasTag( blankId, 'FRG_Forge' ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "A name is earned at the forge: only a FORGED blade is named", 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\ti = FRGN_OfWordCard( dmgTok, 1 );
\t\tk = FRGN_OfWordCard( fxTok, 2 );
\t\tif( i <= 0 || k <= 0 )
\t\t\treturn ECE_TooFewIngredients;
\t\t// renaming is always allowed; the free-text (console) name is cleared
\t\tw.FRG_LookErase( "frg_name_", w.inv.GetItemModifierInt( blankId, 'FRG_Name', 0 ) );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Name', 0 );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Nm1', i );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Nm2', k );
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\titem = blankId;
\t\ttheGame.GetGuiManager().ShowNotification( "The blade now bears the name: " + FRGN_Compose( i, k )
\t\t\t+ ". Rename any time; the words are eternal.", 13000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftBlank( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tfor( i = 0; i < schem.ingredients.Size(); i += 1 )
\t\t\tEquipment().RemoveItemByNameForCrafting( schem.ingredients[i].itemName, schem.ingredients[i].quantity );
\t\t// ⛔ прежний else выдавал 'FRG Blank Secondary' всему, что не сталь
\t\t// и не серебро — с броневыми заготовками бронник вручил бы меч
\t\ttoks = w.inv.AddAnItem( FRGW_BlankOfSchem( schemName ), 1 );
\t\tif( toks.Size() <= 0 )
\t\t\treturn ECE_TooFewIngredients;
\t\titem = toks[0];
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\ttheGame.GetGuiManager().ShowNotification( "The blank is forged - find it in the bag. Next: forge it into a blade or a piece of armour.", 12000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftReskin( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar blankId : SItemUniqueId;
\tvar lineTok, shapeTok, forgedName : name;
\tvar want, path : string;
\tvar k, oldK : int;

\tw = GetWitcherPlayer();
\tw.FRG_LastWhy = "";
\tw.FRG_InCraft = true;
\terror = CanCraftSchematic( schemName, true );
\tw.FRG_InCraft = false;
\tif( error != ECE_NoException )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\treturn error;
\t}
\tGetSchematic( schemName, schem );
\tlineTok = schem.ingredients[0].itemName;	// the blade
\tshapeTok = schem.ingredients[1].itemName;	// the look it should wear
\tif( FRGW_IsPlaceholder( lineTok ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "Pick the blade first - scroll the first square", 10000 );
\t\treturn ECE_TooFewIngredients;
\t}
\tif( !w.FRG_FindForWork( lineTok, blankId ) )
\t\treturn ECE_TooFewIngredients;

\t// the "native look" mark - the same one the armour recipes use: the
\t// blade goes back to its own shape (user 13.09)
\tif( FRGW_IsPlaceholder( shapeTok ) || shapeTok == 'FRG Shape Native' )
\t{
\t\toldK = w.inv.GetItemModifierInt( blankId, 'FRG_Look', 0 );
\t\tif( oldK <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "This blade already wears its own look - scroll the look square to another one", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tif( w.inv.GetItemCategory( blankId ) == 'steelsword' )
\t\t\tw.FRG_ClearLookVisual( 4 );
\t\telse if( w.inv.GetItemCategory( blankId ) == 'silversword' )
\t\t\tw.FRG_ClearLookVisual( 5 );
\t\tw.FRG_LookEraseAll( oldK );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Look', 0 );
\t\titem = blankId;
\t\ttheGame.GetGuiManager().ShowNotification( "The blade wears its own face again", 9000 );
\t\treturn ECE_NoException;
\t}

\t// ⛔ THE BLADE ITSELF IS NEVER TOUCHED (user 09.09, paid for with a lost
\t// Griffin cuirass). Moving an item onto another card takes its identity
\t// with it: witcher-gear quality is read from the CARD NAME, the glyph
\t// enchantment does not travel, the name changes and the upgrade recipes
\t// stop recognising it. So the look is MOUNTED instead - the AMM trick of
\t// stage A: a fake entity of the donor is attached to the blade's own
\t// entity and the real mesh is hidden. Everything else stays untouched.
\twant = StrAfterFirst( NameToString( shapeTok ), "FRG Shape " );
\tforgedName = '';
\tFRGW_ForgedFor( want, w.inv.GetItemCategory( blankId ), forgedName );
\tif( forgedName == '' )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: no card for the look [" + want + "]", 11000 );
\t\treturn ECE_TooFewIngredients;
\t}
\t// the forged card is a clone of the donor, so its equip template is the
\t// donor's own - and a template path is all the mounted look needs
\tpath = theGame.GetDefinitionsManager().GetItemEquipTemplate( forgedName );
\tif( path == "" )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: that look has no equip template - nothing to wear", 11000 );
\t\treturn ECE_TooFewIngredients;
\t}

\t// a blade wears one look at a time: the old one is dropped first
\toldK = w.inv.GetItemModifierInt( blankId, 'FRG_Look', 0 );
\tif( oldK > 0 )
\t{
\t\tw.FRG_LookEraseAll( oldK );
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Look', 0 );
\t}

\tk = FactsQuerySum( "FRG_LookSeq" ) + 1;
\tFactsSet( "FRG_LookSeq", k );
\tif( !w.FRG_LookPack( "frg_look_", k, path ) )
\t{
\t\tw.FRG_LookEraseAll( k );
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: could not store the look - nothing changed", 10000 );
\t\treturn ECE_TooFewIngredients;
\t}
\tpath = theGame.GetDefinitionsManager().GetItemIconPath( forgedName );
\tif( path != "" )
\t\tw.FRG_LookPack( "frg_icon_", k, path );
\tw.inv.SetItemModifierInt( blankId, 'FRG_Look', k );

\t// mount it now if the blade is in hand; otherwise the equip hook does it
\tif( w.inv.GetItemCategory( blankId ) == 'steelsword' )
\t\tw.FRG_ApplyLookVisual( 4 );
\tif( w.inv.GetItemCategory( blankId ) == 'silversword' )
\t\tw.FRG_ApplyLookVisual( 5 );

\titem = blankId;
\tw.RemoveMoney( GetCraftingCost( schemName ) );
\ttheGame.GetGuiManager().ShowNotification( "The blade wears a new face. It is the SAME blade - name, quality, "
\t\t+ "enchantment, runes and upgrades all untouched. Undo: frglook0(4) or frglook0(5)", 15000 );
\treturn ECE_NoException;
}

@addMethod( W3CraftingManager ) function FRG_CraftStudy( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;
\t\tif( FRGW_IsPlaceholder( shapeTok ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Pick the item to measure - scroll the square", 9000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\t// worn gear counts too: measuring does not touch the item at all
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: that item is gone - " + shapeTok, 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tcpNew = w.FRG_MeasureItem( blankId );
\t\titem = blankId;
\t\tif( cpNew <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "This one is already studied whole - nothing new, nothing spent", 9000 );
\t\t\treturn ECE_NoException;
\t\t}
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\ttheGame.GetGuiManager().ShowNotification( "Measurements taken: " + cpNew + " new tokens, and the item is still yours", 11000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftCopyLook( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tcpNew = 0;
\t\tcpFirst = "";
\t\tfor( k2 = 1; k2 <= 6; k2 += 1 )
\t\t{
\t\t\tif( k2 == 1 )
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_SteelSword );
\t\t\telse if( k2 == 2 )
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_SilverSword );
\t\t\telse if( k2 == 3 )
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_Armor );
\t\t\telse if( k2 == 4 )
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_Pants );
\t\t\telse if( k2 == 5 )
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_Gloves );
\t\t\telse
\t\t\t\tcpGot = w.FRG_CopySlotLook( EES_Boots );
\t\t\tif( cpGot != '' )
\t\t\t{
\t\t\t\tif( cpNew == 0 )
\t\t\t\t\tcpFirst = GetLocStringByKeyExt( w.inv.GetItemLocalizedNameByName( cpGot ) );
\t\t\t\tcpNew += 1;
\t\t\t}
\t\t}
\t\tif( cpNew <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Every worn look is already in your book - nothing spent", 9000 );
\t\t\treturn ECE_NoException;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tfor( i = 0; i < schem.ingredients.Size(); i += 1 )
\t\t\tEquipment().RemoveItemByNameForCrafting( schem.ingredients[i].itemName, schem.ingredients[i].quantity );
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\tif( cpNew == 1 )
\t\t\ttheGame.GetGuiManager().ShowNotification( "A pattern taken, the garment unharmed: " + cpFirst, 10000 );
\t\telse
\t\t\ttheGame.GetGuiManager().ShowNotification( "Patterns taken, the gear unharmed: " + cpFirst + " and " + ( cpNew - 1 ) + " more", 10000 );
\t\treturn ECE_NoException;
\t
}

@addMethod( W3CraftingManager ) function FRG_CraftUpgrade( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t\tw = GetWitcherPlayer();
\t\tw.FRG_InCraft = true;
\t\terror = CanCraftSchematic( schemName, true );
\t\tw.FRG_InCraft = false;
\t\tif( error != ECE_NoException )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\t\treturn error;
\t\t}
\t\tGetSchematic( schemName, schem );
\t\tshapeTok = schem.ingredients[0].itemName;\t// the blade slot
\t\tif( FRGW_IsPlaceholder( shapeTok ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.FRG_FindForWork( shapeTok, blankId ) )
\t\t\treturn ECE_TooFewIngredients;
\t\tif( !w.inv.ItemHasTag( blankId, 'FRG_Forge' ) )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "Only a FORGED blade climbs tiers - forge the blank first", 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tif( schemName == 'FRG Upgrade2 schematic' )
\t\t\tk = 2;
\t\telse if( schemName == 'FRG Upgrade3 schematic' )
\t\t\tk = 3;
\t\telse
\t\t\tk = 4;
\t\tif( w.FRGP_TierOf( blankId ) != k - 1 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "This blade is tier " + w.FRGP_TierOf( blankId )
\t\t\t\t+ " of 4 - upgrades go in order", 11000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tw.inv.AddItemCraftedAbility( blankId, FRGP_QAbility( k ), false );
\t\tif( w.FRG_CountAb( blankId, FRGP_QAbility( k ) ) <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "The engine refused the tier - nothing changed, nothing spent", 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\tw.inv.SetItemModifierInt( blankId, 'FRG_Tier', k );
\t\tw.FRGP_PourTier( blankId );
\t\t// the relic tier awakens the donor's flat damage add-ons (§3)
\t\tif( k == 4 )
\t\t{
\t\t\tfdab = FRGFD_AbilityByText( StrAfterFirst( NameToString( w.inv.GetItemName( blankId ) ), "FRG Forged " ) );
\t\t\tif( fdab != '' && w.FRG_CountAb( blankId, fdab ) <= 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( blankId, fdab, false );
\t\t}
\t\t// materials burn; slot [0] is the blade itself and is skipped
\t\tfor( i = 1; i < schem.ingredients.Size(); i += 1 )
\t\t\tEquipment().RemoveItemByNameForCrafting( schem.ingredients[i].itemName, schem.ingredients[i].quantity );
\t\tw.RemoveMoney( GetCraftingCost( schemName ) );
\t\titem = blankId;
\t\ttheGame.GetGuiManager().ShowNotification( "Tier " + k + " of 4 reached: line slots " + w.FRGL_Limit( blankId )
\t\t\t+ ". Quality, damage and the name color follow the tier.", 14000 );
\t\treturn ECE_NoException;
\t
}

// CHANGE THE LOOK OF A PIECE OF ARMOUR - STAGE B (probe confirmed by the
// user 11.09). What a worn piece looks like is a MOUNTED item entity, so the
// real piece is unmounted and a CARRIER card of the chosen look is mounted
// in its place. The real piece stays equipped and untouched. Everything
// that binds the two is a number: FRG_ArmLook on the piece, FRG_LookFor on
// the carrier. An empty look square gives the native look back.
@addMethod( W3CraftingManager ) function FRG_CraftReskinArmor( schemName : name, out item : SItemUniqueId ) : ECraftingException
{
	var w : W3PlayerWitcher;
	var schem : SCraftingSchematic;
	var error : ECraftingException;
	var pieceId : SItemUniqueId;
	var pieceTok, shapeTok, card : name;
	var want : string;

	w = GetWitcherPlayer();
	w.FRG_LastWhy = "";
	w.FRG_InCraft = true;
	error = CanCraftSchematic( schemName, true );
	w.FRG_InCraft = false;
	if( error != ECE_NoException )
	{
		theGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
		return error;
	}
	GetSchematic( schemName, schem );
	pieceTok = schem.ingredients[0].itemName;	// the piece itself
	shapeTok = schem.ingredients[1].itemName;	// the look, or empty = native
	if( FRGW_IsPlaceholder( pieceTok ) )
	{
		theGame.GetGuiManager().ShowNotification( "Pick the piece first - scroll the first square", 9000 );
		return ECE_TooFewIngredients;
	}
	if( !w.FRG_FindForWork( pieceTok, pieceId ) )
	{
		theGame.GetGuiManager().ShowNotification( "FRG gate: that piece is gone - " + pieceTok, 10000 );
		return ECE_TooFewIngredients;
	}
	if( StrFindFirst( NameToString( w.inv.GetItemName( pieceId ) ), "FRG Blank " ) == 0 )
	{
		theGame.GetGuiManager().ShowNotification( "A raw blank has no look worth changing - forge it instead", 10000 );
		return ECE_TooFewIngredients;
	}

	// the "native look" mark (or an empty square, if one ever happens):
	// the piece goes back to its own shape
	if( FRGW_IsPlaceholder( shapeTok ) || shapeTok == 'FRG Shape Native' )
	{
		if( w.inv.GetItemModifierInt( pieceId, 'FRG_ArmLook', 0 ) <= 0 )
		{
			theGame.GetGuiManager().ShowNotification( "This piece already wears its own look - scroll the look square to another one", 11000 );
			return ECE_TooFewIngredients;
		}
		w.FRG_ArmLookStrip( pieceId );
		item = pieceId;
		theGame.GetGuiManager().ShowNotification( "The piece wears its own face again", 9000 );
		return ECE_NoException;
	}

	want = StrAfterFirst( NameToString( shapeTok ), "FRG Shape " );
	card = '';
	FRGW_ForgedFor( want, FRGW_ReskinCatOf( schemName ), card );
	if( card == '' )
	{
		theGame.GetGuiManager().ShowNotification( "FRG gate: no carrier card for the look [" + want + "]", 11000 );
		return ECE_TooFewIngredients;
	}
	if( !w.FRG_ArmLookWear( pieceId, card ) )
	{
		theGame.GetGuiManager().ShowNotification( "FRG gate: the carrier card refused to spawn - " + card, 10000 );
		return ECE_TooFewIngredients;
	}
	item = pieceId;
	w.RemoveMoney( GetCraftingCost( schemName ) );
	theGame.GetGuiManager().ShowNotification( "The piece wears a new face. It is the SAME piece - nothing on it changed. Dye it as before; an empty look square brings its own face back.", 13000 );
	return ECE_NoException;
}

@wrapMethod( W3CraftingManager ) function Craft( schemName : name, out item : SItemUniqueId, optional itemName : name ) : ECraftingException
{
\tvar flawId, k2 : int;
\tvar axDoms, axNames : array< name >;
\tvar axSums : array< int >;
\tvar w : W3PlayerWitcher;
\tvar schem : SCraftingSchematic;
\tvar error : ECraftingException;
\tvar toks : array< SItemUniqueId >;
\tvar picks : array< int >;
\tvar props : array< name >;
\tvar shapeTok, dmgTok, lineTok, fxTok, forgedName, fdab, resTok : name;
\tvar tokId, blankId : SItemUniqueId;
\tvar j : int;
\tvar i, k, want_i, cpNew, slotGuard : int;
\tvar want, cpFirst : string;
\tvar cpGot : name;

\t// ------- blade properties: rebuild the whole SET in one craft ---------
\t// (user's call: "forge properties together, see the blade I am building,
\t// rearrange on the fly"). Empty slots are legal; old properties come off;
\t// tokens are eternal knowledge.
\tif( schemName == 'FRG Engrave schematic' )
\t
\t{
\t\treturn FRG_CraftEngrave( schemName, item );
\t}

\t// ------- enchanting: a relic effect onto a relic-tier blade ------------
\tif( schemName == 'FRG Enchant schematic' )
\t
\t{
\t\treturn FRG_CraftEnchant( schemName, item );
\t}

\t// ------- the maker's mark: a stamp burns in one pure plus --------------
\tif( schemName == 'FRG Mark schematic' )
\t
\t{
\t\treturn FRG_CraftMark( schemName, item );
\t}

\t// ------- armour forging: blank + shape; protection rides the shape -----
\t// The donor's card ARMOR (W3EE keeps armour on the card, autogen is off)
\t// arrives as a per-donor ability, taxed -15/-10/-5% until the relic tier.
\tif( schemName == 'FRG ForgeArmor schematic' || schemName == 'FRG ForgePants schematic'
\t\t|| schemName == 'FRG ForgeGloves schematic' || schemName == 'FRG ForgeBoots schematic' )
\t
\t{
\t\treturn FRG_CraftArmor( schemName, item );
\t}

\t// ------- naming: the blade takes a two-word name (256 combinations) ----
\tif( schemName == 'FRG Name schematic' )
\t
\t{
\t\treturn FRG_CraftName( schemName, item );
\t}

\t// ------- blank recipes: the stub result parks them in the Path group,
\t// the REAL blank is created here (materials and fee, vanilla-style)
\tif( FRGW_BlankOfSchem( schemName ) != '' )
\t
\t{
\t\treturn FRG_CraftBlank( schemName, item );
\t}

\t// ------- take a pattern: copy the LOOK of worn gear, no sacrifice ----
\t// (user's call 03.09): shape tokens of everything equipped; the items
\t// stay whole. Nothing new studied - nothing spent.
\t// ------- change the look: the same blade in another shape -----------
\t// (MVP call 07.09). Everything that makes the blade what it is moves
\t// over: properties, damage counters, the red line, tier, runes.
\tif( schemName == 'FRG Reskin schematic' )
\t
\t{
\t\treturn FRG_CraftReskin( schemName, item );
\t}

\t// ------- the same for ARMOUR (stage B): a carrier is worn OVER the piece
\tif( FRGW_IsArmorReskin( schemName ) )
\t{
\t\treturn FRG_CraftReskinArmor( schemName, item );
\t}

\t// ------- take measurements: all tokens of an item, item unharmed ----
\tif( StrFindFirst( NameToString( schemName ), "FRG Study " ) == 0 )
\t
\t{
\t\treturn FRG_CraftStudy( schemName, item );
\t}

\tif( schemName == 'FRG CopyLook schematic' )
\t
\t{
\t\treturn FRG_CraftCopyLook( schemName, item );
\t}

\t// ------- upgrades I..III: the blade climbs one quality tier -----------
\t// Tier = quality: the engine's own formula raises the damage floor and
\t// repaints the name (Common -> Masterwork -> Magical -> Relic).
\tif( schemName == 'FRG Upgrade2 schematic' || schemName == 'FRG Upgrade3 schematic' || schemName == 'FRG Upgrade4 schematic' )
\t
\t{
\t\treturn FRG_CraftUpgrade( schemName, item );
\t}

\tif( schemName != 'FRG ForgeBlade schematic' && schemName != 'FRG ForgeSide schematic' )
\t\treturn wrappedMethod( schemName, item, itemName );

\tw = GetWitcherPlayer();
\tw.FRG_InCraft = true;
\terror = CanCraftSchematic( schemName, true );
\tw.FRG_InCraft = false;
\tif( error != ECE_NoException )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the window itself refuses, code " + error, 9000 );
\t\treturn error;
\t}

\tGetSchematic( schemName, schem );
\tshapeTok = schem.ingredients[1].itemName;
\tdmgTok = schem.ingredients[2].itemName;
\t// the fourth slot is OPTIONAL: a flaw mark, chosen at the blade's birth
\tflawId = 0;
\tif( schem.ingredients.Size() > 3 && !FRGW_IsPlaceholder( schem.ingredients[3].itemName ) )
\t{
\t\tflawId = FRGF_OfTokCard( schem.ingredients[3].itemName );
\t\tif( flawId <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "That is not a flaw mark - the fourth slot takes marks only", 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t}

\t// forging is strict: the blank, the shape and the damage are all REQUIRED
\tif( FRGW_IsPlaceholder( schem.ingredients[0].itemName )
\t\t|| FRGW_IsPlaceholder( shapeTok ) || FRGW_IsPlaceholder( dmgTok ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "Forging needs all three: a blank, a shape token and a damage token", 10000 );
\t\treturn ECE_TooFewIngredients;
\t}
\tif( !w.FRG_TakeForForge( schem.ingredients[0].itemName, blankId ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: no blank of this kind at all - " + schem.ingredients[0].itemName, 10000 );
\t\treturn ECE_TooFewIngredients;
\t}

\t// The REAL result: a per-donor forged card (donor's template, icon and
\t// anims live in the CARD, so the world, the paperdoll doll and the grid
\t// all render it natively - no fake entities for forged blades at all).
\t// the "native look" mark restores a look, it is not a look to forge with
\tif( shapeTok == 'FRG Shape Native' )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "That mark restores a blade's own look - pick a real look to forge with", 11000 );
\t\treturn ECE_TooFewIngredients;
\t}
\tforgedName = '';
\twant = StrAfterFirst( NameToString( shapeTok ), "FRG Shape " );
\t// THE BLANK DECIDES THE METAL: a steel blank forges a steel blade even
\t// with a silver donor's look (the cross-metal twin card). The damage
\t// token carries BOTH stack counters, so the pour always fits.
\tFRGW_ForgedFor( want, w.inv.GetItemCategory( blankId ), forgedName );
\tif( forgedName != '' )
\t{
\t\ttoks = w.inv.AddAnItem( forgedName, 1 );
\t\tif( toks.Size() <= 0 )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG gate: the forged card refused to spawn - " + forgedName, 10000 );
\t\t\treturn ECE_TooFewIngredients;
\t\t}
\t\titem = toks[0];

\t\t// STAGES ARE GONE (user's call 22.08): the forge delivers a RELIC
\t\t// outright - full quality, every property slot, rune sockets.
\t\tw.inv.SetItemModifierInt( item, 'FRG_Tier', 4 );
\t\tw.inv.SetItemModifierInt( item, 'ItemQualityModified', 1 );
\t\tfor( i = 2; i <= 4; i += 1 )
\t\t{
\t\t\tif( w.FRG_CountAb( item, FRGP_QAbility( i ) ) <= 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGP_QAbility( i ), false );
\t\t}
\t\t// the engine may refuse more sockets (armour often does): a plain
\t\t// while() here hung the whole game (user 05.09) - bail out instead
\t\tslotGuard = w.inv.GetItemEnhancementSlotsCount( item );
\t\twhile( slotGuard < 3 )
\t\t{
\t\t\tw.inv.AddSlot( item );
\t\t\tif( w.inv.GetItemEnhancementSlotsCount( item ) <= slotGuard )
\t\t\t\tbreak;
\t\t\tslotGuard = w.inv.GetItemEnhancementSlotsCount( item );
\t\t}

\t\t// THE FLAW: a clean minus the player accepts at the forge in exchange
\t\t// for one more property slot. The weight lives as a NUMBER on the
\t\t// instance (tags do not survive a save); the token is knowledge - kept.
\t\tif( flawId > 0 )
\t\t{
\t\t\tw.inv.AddItemCraftedAbility( item, FRGF_Ability( flawId ), false );
\t\t\tw.inv.SetItemModifierInt( item, 'FRG_Flaw', FRGF_Weight( flawId ) );
\t\t}

\t\t// carry over whatever the player already engraved into the blank
\t\tfor( i = 1; i <= 4; i += 1 )
\t\t{
\t\t\tif( w.FRG_CountAb( blankId, FRGD_Ability( i ) ) > 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGD_Ability( i ), false );
\t\t\tif( w.FRG_CountAb( blankId, FRGT_Ability( i ) ) > 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGT_Ability( i ), false );
\t\t}
\t\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t\t{
\t\t\tk = FRGL_IdAt( i );
\t\t\tif( w.FRG_CountAb( blankId, FRGL_Ability( k ) ) > 0 )
\t\t\t\tw.inv.AddItemCraftedAbility( item, FRGL_Ability( k ), false );
\t\t}

\t\t// the blank is consumed; the shape token is NOT - pure cosmetics, the
\t\t// user made it a reusable applicator (like the look token before it)
\t\tw.inv.RemoveItem( blankId, 1 );
\t}
\telse
\t{
\t\t// fallback: no forged card known - transform the blank itself and hang
\t\t// the look as a fake entity (console-era path)
\t\ttheGame.GetGuiManager().ShowNotification( "FRG diag: no forged card for [" + want + "] - falling back to the blank itself", 10000 );
\t\titem = blankId;
\t}

\t// damage: the token's counters become the blade's TARGET; the pour
\t// follows the tier (deficit -7/-5/-3/0 stacks - the game's own quality
\t// grammar). The damage token is knowledge (eternal) - never spent.
\ttoks = w.inv.GetItemsByName( dmgTok );
\tif( toks.Size() > 0 )
\t{
\t\ttokId = toks[0];
\t\tw.inv.SetItemModifierInt( item, 'FRG_St', w.inv.GetItemModifierInt( tokId, 'FRG_St', 0 ) );
\t\tw.inv.SetItemModifierInt( item, 'FRG_Sv', w.inv.GetItemModifierInt( tokId, 'FRG_Sv', 0 ) );
\t\tw.inv.SetItemModifierInt( item, 'FRG_StB', w.inv.GetItemModifierInt( tokId, 'FRG_StB', 0 ) );
\t\tw.inv.SetItemModifierInt( item, 'FRG_StD', w.inv.GetItemModifierInt( tokId, 'FRG_StD', 0 ) );
\t\tw.inv.SetItemModifierInt( item, 'FRG_SvB', w.inv.GetItemModifierInt( tokId, 'FRG_SvB', 0 ) );
\t\tw.inv.SetItemModifierInt( item, 'FRG_SvD', w.inv.GetItemModifierInt( tokId, 'FRG_SvD', 0 ) );
\t\tw.FRGP_PourTier( item );
\t}

\t// the donor's flat damage add-ons arrive at once (no tiers any more)
\tfdab = FRGFD_AbilityByText( StrAfterFirst( NameToString( shapeTok ), "FRG Shape " ) );
\tif( fdab != '' && w.FRG_CountAb( item, fdab ) <= 0 )
\t\tw.inv.AddItemCraftedAbility( item, fdab, false );

\t// lines and the effect join later on the path: engraving any time,
\t// enchanting at the relic tier (phase 3)

\t// shape as a FAKE-entity look: only the fallback path needs it - a real
\t// forged card carries the donor's template natively. The token survives
\t// either way (cosmetics are free to reuse - user's call).
\tif( forgedName == '' && !FRGW_IsPlaceholder( shapeTok ) )
\t{
\t\ttoks = w.inv.GetItemsByName( shapeTok );
\t\tif( toks.Size() > 0 )
\t\t{
\t\t\tk = w.inv.GetItemModifierInt( toks[0], 'FRG_Look', 0 );
\t\t\tif( k > 0 )
\t\t\t{
\t\t\t\t// clone the key: the eternal token must not share fact storage
\t\t\t\t// with the blade, or frglook0 on one would orphan the other
\t\t\t\ti = FactsQuerySum( "FRG_LookSeq" ) + 1;
\t\t\t\tFactsSet( "FRG_LookSeq", i );
\t\t\t\tw.FRG_LookPack( "frg_look_", i, w.FRG_LookRead( "frg_look_", k ) );
\t\t\t\tw.FRG_LookPack( "frg_icon_", i, w.FRG_LookRead( "frg_icon_", k ) );
\t\t\t\tw.inv.SetItemModifierInt( item, 'FRG_Look', i );
\t\t\t}
\t\t}
\t}

\tw.RemoveMoney( GetCraftingCost( schemName ) );
\ttheGame.GetGuiManager().ShowNotification( "The blade is forged: RELIC quality, full donor damage, "
\t\t+ w.FRGL_Limit( item ) + " property slots, 3 rune sockets. Tokens are knowledge - none were spent.", 15000 );
\treturn ECE_NoException;
}
"""


def _frgl_section():
    """Генерит ws-секцию конструктора строк из lines_data — один источник
    истины. Единый реестр = 26 пул-строк + нарезка школ/реликтов (CUT)."""
    # ПУЛОВЫЕ СТРОКИ REDUX УБРАНЫ (просьба пользователя, повторно 07.09):
    # «Жало», «Проворство», «Сокрушение» и родня — готовые способности
    # мода, да ещё в максимуме диапазона; кузница должна давать только то,
    # что снято с РЕАЛЬНЫХ вещей. LINES/ARMOR_LINES остаются в данных
    # (их абилки нужны старым предметам), но в реестр выбора не идут.
    records = [(c["id"], "", c["ability"], c["junk"], c["stats"]) for c in CUT]
    # id РАЗРЕЖЕНЫ (броневые пулы живут в диапазоне 2001+): циклы ходят по
    # ПЛОТНОМУ индексу 1..Count через FRGL_IdAt(i) -> настоящий id
    n = len(records)
    all_ids = [rec[0] for rec in records]

    def switch(fname, rtype, default, pick):
        rows = "".join("\t\tcase %d:\treturn %s;\n" % (rec[0], pick(rec))
                       for rec in records)
        return ("function %s( id : int ) : %s\n{\n\tswitch( id )\n\t{\n%s\t}\n"
                "\treturn %s;\n}\n\n" % (fname, rtype, rows, default))

    # ⛔ компилятор WS падает «memory exhausted» на switch длиннее ~390 строк
    # (и if-цепочке ~780): большие функции дробятся на чанки по 250 case
    # с диспетчером по диапазонам id.
    def chunked_switch(fname, rtype, default, pairs, chunk=250):
        # ⛔ диспетчер маршрутизирует по ГРАНИЦАМ id — case ОБЯЗАНЫ идти по
        # возрастанию. Реестр после перегенераций перемешан (наследование id),
        # несортированные пары молча роутились мимо своих чанков (Белая вдова).
        pairs = sorted(pairs, key=lambda p: p[0])
        parts = [pairs[i:i + chunk] for i in range(0, len(pairs), chunk)]
        out = ""
        for ci, part in enumerate(parts):
            out += ("function %s_c%d( id : int ) : %s\n{\n\tswitch( id )\n\t{\n"
                    % (fname, ci, rtype))
            out += "".join("\t\tcase %d:\treturn %s;\n" % (i, v) for i, v in part)
            out += "\t}\n\treturn %s;\n}\n\n" % default
        out += "function %s( id : int ) : %s\n{\n" % (fname, rtype)
        for ci, part in enumerate(parts):
            if ci < len(parts) - 1:
                out += ("\tif( id <= %d )\n\t\treturn %s_c%d( id );\n"
                        % (part[-1][0], fname, ci))
            else:
                out += "\treturn %s_c%d( id );\n" % (fname, ci)
        out += "}\n\n"
        return out

    def chunked_textmap(fname, rtype, default, pairs, chunk=120):
        """pairs: (строка, выражение). Дробление строковых if-цепочек:
        чанки пробуются по очереди, пустой ответ = «не моё»."""
        parts = [pairs[i:i + chunk] for i in range(0, len(pairs), chunk)]
        out = ""
        for ci, part in enumerate(parts):
            out += ("function %s_c%d( txt : string ) : %s\n{\n"
                    % (fname, ci, rtype))
            out += "".join("\tif( txt == \"%s\" )\n\t\treturn %s;\n" % (s, v)
                           for s, v in part)
            out += "\treturn %s;\n}\n\n" % default
        return out, len(parts)

    junk_ids = [str(rec[0]) for rec in records if rec[3]]

    # имена нарезанных строк — лок-ключ ДОНОРА; донор строки — для чеканки
    # ⛔ ПОЛОВИНКИ ПОДПИСЫВАЮТСЯ ПО-РАЗНОМУ (ГД 17.09): один профиль
    # печатался двумя строками с одним именем, и это читалось как
    # «свойств стало больше, чем у оригинала».
    _parts, _seen, _rows = {}, {}, []
    for _c in CUT:
        _parts[_c["donor"]] = _parts.get(_c["donor"], 0) + 1
    for _c in CUT:
        _n = _seen.get(_c["donor"], 0) + 1
        _seen[_c["donor"]] = _n
        _key = _c.get("lockey") or "frgl_token"
        if _parts[_c["donor"]] > 1:
            _rows.append("\t\tcase %d:\treturn GetLocStringByKeyExt( \"%s\" )"
                         " + \" (%d/%d)\";\n"
                         % (_c["id"], _key, _n, _parts[_c["donor"]]))
        else:
            _rows.append("\t\tcase %d:\treturn GetLocStringByKeyExt( \"%s\" );\n"
                         % (_c["id"], _key))
    title_cut = "".join(_rows)
    donor_cut = "".join(
        "\t\tcase %d:\treturn '%s';\n" % (c["id"], c["donor"]) for c in CUT)

    s = "\n// ------------------------------------------------------------- lines ---\n"
    s += "// The line builder. Donor items carry Redux pool abilities; sacrifice mints\n"
    s += "// LINE TOKENS (FRG_Part=5, FRG_Line=id). A line is forged onto a BLANK only,\n"
    s += "// as our fixed-value FRG_L_* ability (values sit mid-range of Redux's roll,\n"
    s += "// no re-roll - save-scumming is dead). Strong lines carry their minus INSIDE\n"
    s += "// the pair - Redux's own grammar - and junk marks are pure minuses that OPEN\n"
    s += "// extra slots: %d plus-lines free, +1 per junk mark, hard cap %d.\n\n" % (LINE_LIMIT_BASE, LINE_LIMIT_MAX)

    s += "function FRGL_Count() : int\n{\n\treturn %d;\n}\n\n" % n
    s += "// dense index 1..Count -> sparse line id (armour pools sit at 2001+)\n"
    s += chunked_switch("FRGL_IdAt", "int", "0",
                        [(i + 1, str(lid)) for i, lid in enumerate(all_ids)])
    s += chunked_switch("FRGL_Ability", "name", "''",
                        [(rec[0], "'%s'" % rec[2]) for rec in records])
    s += chunked_switch("FRGL_Redux", "name", "''",
                        [(rec[0], "'%s'" % rec[1]) for rec in records])
    # статы строк живут в ЛОКАЛИЗАЦИИ (frgls_<id>): компактно и по-русски
    s += ("function FRGL_Stats( id : int ) : string\n{\n"
          "\treturn GetLocStringByKeyExt( \"frgls_\" + id );\n}\n\n")

    s += "function FRGL_IsJunk( id : int ) : bool\n{\n"
    s += "".join("\tif( id == %s )\n\t\treturn true;\n" % j for j in junk_ids)
    s += "\treturn false;\n}\n\n"

    # реликтовые строки: эксклюзив «одна на клинок» (Р-2, одобрено)
    relic_ids = [str(c["id"]) for c in CUT if c.get("relic")]
    s += "// RELIC line: exclusive - at most ONE per blade, like a runeword\n"
    # if-цепочка живёт до ~780 строк (вольт: memory exhausted).
    # После починки реликтовости 08.09 их стало 684, функция
    # выросла до 1371 строки и компилятор упал. Дробим на чанки.
    s += chunked_switch("FRGL_IsRelic", "bool", "false",
                        [(int(r), "true") for r in relic_ids])

    # дом строки: броневые строки — на броню, клинковые — на клинки
    armor_line_ids = ([c["id"] for c in CUT
                       if c.get("cat") in ("armor", "pants", "gloves", "boots")]
                      + [rec[0] for rec in ARMOR_LINES])
    s += "// a line's home: armour lines fit armour, blade lines fit blades\n"
    # ⛔ ПОЛОВИНЫ ОДНОГО ДОНОРА — ОДИН РЕЛИКТ (требование ГД 17.09).
    # Разрез профиля сделали мы, а не игрок, и платить за него он не должен.
    _kin_no = {}
    for _c in CUT:
        if _c.get("relic") and _c["donor"] not in _kin_no:
            _kin_no[_c["donor"]] = len(_kin_no) + 1
    s += "// relic KIN: halves of ONE donor profile count as ONE relic\n"
    s += chunked_switch("FRGL_RelicKin", "int", "0",
                        [(_c["id"], str(_kin_no[_c["donor"]])) for _c in CUT
                         if _c.get("relic")])
    s += chunked_switch("FRGL_IsArmorLine", "bool", "false",
                        [(i, "true") for i in sorted(armor_line_ids)])

    # слот тела строки: нагрудная строка не лезет в перчатки (жалоба 05.09).
    # Пуловые строки брони категории не имеют - годятся любому слоту.
    s += "// which body slot a cut line came from ('' = fits any armour slot)\n"
    s += chunked_switch("FRGL_Cat", "name", "''",
                        sorted([(c["id"], "'%s'" % c["cat"]) for c in CUT
                                if c.get("cat") in ("armor", "pants", "gloves", "boots")]))

    # вес-класс пул-строки брони: Redux вешает их по весу — уважаем
    weight_tag = {"Light": "LightArmor", "Medium": "MediumArmor",
                  "Heavy": "HeavyArmor"}
    s += "// armour POOL lines respect the weight class (Redux's own rule);\n"
    s += "// cut lines carry a donor's style and fit any weight ('' = no gate)\n"
    s += "function FRGL_WeightTag( id : int ) : name\n{\n\tswitch( id )\n\t{\n"
    s += "".join("\t\tcase %d:\treturn '%s';\n" % (rec[0], weight_tag[rec[3]])
                 for rec in ARMOR_LINES)
    s += "\t}\n\treturn '';\n}\n\n"

    # проклятая сцепка (Р-3а): вампиризм-строки проклятых доноров
    cursed_ids = [str(c["id"]) for c in CUT if c.get("cursed")]
    s += "// CURSED bond: a cursed donor's lifesteal line demands the Dark\n"
    s += "// Curse effect on the blade - the gift and the curse are one\n"
    s += "function FRGL_IsCursed( id : int ) : bool\n{\n"
    s += "".join("\tif( id == %s )\n\t\treturn true;\n" % r for r in cursed_ids)
    s += "\treturn false;\n}\n\n"

    # плоские урон-добавки доноров: текстовый матч (StringToName в сборке
    # нет), чанкованный — 438 доноров пробивают лимит if-цепочки (~780)
    def textmap_dispatch(fname, rtype, default, pairs, chunk=120):
        body, np = chunked_textmap(fname, rtype, default, pairs, chunk)
        out = body
        out += "function %s( txt : string ) : %s\n{\n" % (fname, rtype)
        out += "\tvar v : %s;\n\n" % rtype
        for ci in range(np - 1):
            out += ("\tv = %s_c%d( txt );\n\tif( v != %s )\n\t\treturn v;\n"
                    % (fname, ci, default))
        out += "\treturn %s_c%d( txt );\n}\n\n" % (fname, np - 1)
        return out

    _flat_sorted = sorted(FLAT.items(), key=lambda kv: kv[1]["num"])
    s += "// Flat damage add-ons of a donor's card - what relics really differ\n"
    s += "// by in hand damage.\n"
    s += textmap_dispatch("FRGFD_AbilityByText", "name", "''",
                          [(d, "'%s'" % flat_ability(d)) for d, r in _flat_sorted])
    s += textmap_dispatch("FRGFD_StatsByText", "string", '""',
                          [(d, 'GetLocStringByKeyExt( "frgfd_%d" )' % r["num"])
                           for d, r in _flat_sorted])

    # лестница ступеней (решение пользователя 02.09): разбор возвращает
    # предыдущую версию вещи — апгрейд ковался ИЗ неё. Карта из рецептов.
    import json as _json3, os as _os3
    _prev3 = _json3.load(open(_os3.path.join(_os3.path.dirname(
        _os3.path.abspath(__file__)), "prev_data.json"), encoding="utf-8"))
    s += "// The tier ladder: an upgrade was forged FROM the previous version,\n"
    s += "// so dismantling frees that version whole (map: the game's recipes).\n"
    s += textmap_dispatch("FRGX_PrevOf", "name", "''",
                          [(k, "'%s'" % v) for k, v in sorted(_prev3.items())])

    # защита брони доноров: в W3EE броня - карточный стат (автоген выключен),
    # переносится абилкой FRG_AD_<num>; штрафы тиров FRG_AP1..3 снимаемые.
    _armor_sorted = sorted(ARMOR.items(), key=lambda kv: kv[1]["num"])
    s += "// A donor's card ARMOR - W3EE keeps armour on the card (autogen off),\n"
    s += "// so the forge carries it as a per-donor ability, tier-taxed.\n"
    s += textmap_dispatch("FRGAD_AbilityByText", "name", "''",
                          [(d, "'%s'" % armor_ability(d)) for d, r in _armor_sorted])
    s += textmap_dispatch("FRGAD_ValueByText", "int", "0",
                          [(d, str(round(r["armor"]))) for d, r in _armor_sorted])
    s += "// weight class of the protection donor: 1 light / 2 medium / 3 heavy\n"
    s += textmap_dispatch("FRGAD_WeightByText", "int", "0",
                          [(d, str(r.get("weight", 0))) for d, r in _armor_sorted])
    # сопротивления и повадки веса донора — своя абилка, свой жетон (05.09)
    s += "// A donor's RESISTANCES (and how the piece taxes stamina): a\n"
    s += "// separate token from the armour value itself.\n"
    s += textmap_dispatch("FRGAR_AbilityByText", "name", "''",
                          [(d, "'%s'" % armor_res_ability(d))
                           for d, r in _armor_sorted if r.get("skel")])
    s += "// ...and what those resistances actually read as, for the hover\n"
    s += textmap_dispatch("FRGAR_StatsByText", "string", '""',
                          [(d, 'GetLocStringByKeyExt( "frgar_%d" )' % r["num"])
                           for d, r in _armor_sorted if r.get("skel")])
    s += "function FRGAP_Ability( tier : int ) : name\n{\n\tswitch( tier )\n\t{\n"
    s += "".join("\t\tcase %d:\treturn '%s';\n" % (t, ab)
                 for t, ab, _p in ARMOR_TIER_PENALTY)
    s += "\t}\n\treturn '';\n}\n\n"

    s += chunked_switch("FRGL_TitleCut", "string", '""',
                        [(c["id"], 'GetLocStringByKeyExt( "%s" )'
                          % (c.get("lockey") or "frgl_token")) for c in CUT])
    s += "function FRGL_Title( id : int ) : string\n{\n"
    s += "\tvar t : string;\n\n\tt = FRGL_TitleCut( id );\n"
    s += "\tif( t != \"\" )\n\t\treturn t;\n"
    s += "\treturn GetLocStringByKeyExt( \"frgl_\" + id );\n}\n\n"

    s += "// donor of a CUT line - minting at disassembly matches by this\n"
    s += chunked_switch("FRGL_CutDonor", "name", "''",
                        [(c["id"], "'%s'" % c["donor"]) for c in CUT])

    # мост родни: статы у Redux часто живут только на одной карточке семьи
    # «X» / «X_crafted» / «NGP X» (Объятья проклятого, НГ+-трофеи). Строка
    # отвечает на разбор ЛЮБОГО члена семьи, не имеющего своих строк.
    donors_with_lines = {c["donor"] for c in CUT}

    def kinset(nm):
        base = nm[:-8] if nm.endswith("_crafted") else nm
        fam = {base, base + "_crafted", "NGP " + base,
               "NGP " + base + "_crafted"}
        fam.discard(nm)
        return [k for k in sorted(fam) if k not in donors_with_lines]
    match_pairs = []
    for c in CUT:
        conds = ["donor == '%s'" % c["donor"]] +                 ["donor == '%s'" % k for k in kinset(c["donor"])]
        match_pairs.append((c["id"], " || ".join(conds)))
    s += "// does this donor name belong to the CUT line's family?\n"
    match_pairs.sort(key=lambda p: p[0])   # диспетчер требует монотонных id
    parts = [match_pairs[i:i + 200] for i in range(0, len(match_pairs), 200)]
    for ci, part in enumerate(parts):
        s += ("function FRGL_MatchDonor_c%d( id : int, donor : name ) : bool\n"
              "{\n\tswitch( id )\n\t{\n" % ci)
        for lid, cond in part:
            s += "\t\tcase %d:\treturn %s;\n" % (lid, cond)
        s += "\t}\n\treturn false;\n}\n\n"
    s += "function FRGL_MatchDonor( id : int, donor : name ) : bool\n{\n"
    for ci, part in enumerate(parts):
        if ci < len(parts) - 1:
            s += ("\tif( id <= %d )\n\t\treturn FRGL_MatchDonor_c%d( id, donor );\n"
                  % (part[-1][0], ci))
        else:
            s += "\treturn FRGL_MatchDonor_c%d( id, donor );\n" % ci
    s += "}\n\n"

    s += "function FRGL_FromAbility( ab : name ) : int\n{\n\tvar i, id : int;\n\n"
    s += "\tfor( i = 1; i <= FRGL_Count(); i += 1 )\n\t{\n"
    s += "\t\tid = FRGL_IdAt( i );\n"
    s += "\t\tif( FRGL_Ability( id ) == ab || FRGL_Redux( id ) == ab )\n\t\t\treturn id;\n"
    s += "\t}\n\treturn 0;\n}\n\n"

    s += """@addMethod( W3PlayerWitcher ) function FRGL_FindToken( id : int, out item : SItemUniqueId ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar i : int;

\t// line tokens are per-line CARDS now (window model) - the name IS the id
\titems = inv.GetItemsByName( FRGL_TokCard( id ) );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( inv.IsIdValid( items[i] ) )
\t\t{
\t\t\titem = items[i];
\t\t\treturn true;
\t\t}
\t}
\treturn false;
}

// Counts plus-lines and junk marks already forged into an item.
@addMethod( W3PlayerWitcher ) function FRGL_CountOn( item : SItemUniqueId, out plus : int, out junk : int )
{
\tvar i, id : int;

\tplus = 0;
\tjunk = 0;
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tid = FRGL_IdAt( i );
\t\tif( FRG_CountAb( item, FRGL_Ability( id ) ) <= 0 )
\t\t\tcontinue;
\t\tif( FRGL_IsJunk( id ) )
\t\t\tjunk += 1;
\t\telse
\t\t\tplus += 1;
\t}
}

// The blade's path: line slots grow with the TIER (1..4). Legacy grooves on
// raw blanks keep working (retired from the path, R-6), plain blanks get 1.
@addMethod( W3PlayerWitcher ) function FRGL_BaseSlots( item : SItemUniqueId ) : int
{
\tvar t : int;

\tt = FRGP_TierOf( item );
\tif( t > 0 )
\t\treturn t;
%BASESLOTS%\treturn 1;
}

// Сколько РЕЛИКТОВЫХ свойств несёт клинок (решение ГД 18.09): базово ДВА —
// ровно столько нужно, чтобы собрать копию донора, чей профиль наша
// нарезка делит надвое. Порок открывает ТРЕТЬЕ место и это потолок.
@addMethod( W3PlayerWitcher ) function FRGL_RelicLimit( item : SItemUniqueId ) : int
{
\tif( inv.GetItemModifierInt( item, 'FRG_Flaw', 0 ) == 2 )
\t\treturn 3;
\treturn 2;
}

@addMethod( W3PlayerWitcher ) function FRGL_Limit( item : SItemUniqueId ) : int
{
\tvar plus, junk, lim : int;

\tFRGL_CountOn( item, plus, junk );
\tlim = FRGL_BaseSlots( item ) + junk;
\t// cursed forging (P-3v): the Dark Curse anti-enchant pays for itself
\t// with one extra line slot - a fat minus buying a fat plus
\tif( inv.GetItemModifierInt( item, 'FRG_Fx', 0 ) == 13 )
\t\tlim += 1;
\t// a LIGHT flaw mark forged into the blade buys one ordinary slot
\tif( inv.GetItemModifierInt( item, 'FRG_Flaw', 0 ) == 1 )
\t\tlim += 1;
\tif( lim > %CAP% )
\t\tlim = %CAP%;
\treturn lim;
}

// Teleport the player to exact world coordinates. The game ships pos()
// (prints your position) but no "stand here" command - this is it.
// Usage in console:  frggoto(261.63, 1595.52, 42.42)
// Which crafting schematics does the player actually know? Filter by a
// substring: frgschem("Viper") lists every Viper recipe in the book.
exec function frgschem( part : string )
{
\tvar w : W3PlayerWitcher;
\tvar all : array< name >;
\tvar i, n : int;
\tvar s : string;

\tw = GetWitcherPlayer();
\tall = w.GetCraftingSchematicsNames();
\ts = "";
\tn = 0;
\tfor( i = 0; i < all.Size(); i += 1 )
\t{
\t\tif( part == "" || StrContains( NameToString( all[i] ), part ) )
\t\t{
\t\t\ts = s + NameToString( all[i] ) + "<br>";
\t\t\tn += 1;
\t\t}
\t}
\tif( n <= 0 )
\t\ts = "nothing found for [" + part + "] among " + all.Size() + " known schematics";
\telse
\t\ts = "known (" + n + " of " + all.Size() + "):<br>" + s;
\ttheGame.GetGuiManager().ShowNotification( s, 30000 );
}

// Cheat minting: spawn the donor, read it EXACTLY like a disassembly
// would, mint, remove. Tokens are indistinguishable from honestly earned.
@addMethod( W3PlayerWitcher ) function FRG_CheatMint( donor : name ) : int
{
\tvar made : array< SItemUniqueId >;
\tvar abilities : array< name >;
\tvar st, sv, stB, stD, svB, svD, fx, n : int;

\tmade = inv.AddAnItem( donor, 1 );
\tif( made.Size() <= 0 )
\t\treturn 0;
\tinv.GetItemAbilities( made[0], abilities );
\tst = FRG_CountAb( made[0], 'autogen_fixed_steel_dmg' );
\tsv = FRG_CountAb( made[0], 'autogen_fixed_silver_dmg' );
\tstB = FRG_CountAb( made[0], 'autogen_steel_base' );
\tstD = FRG_CountAb( made[0], 'autogen_steel_dmg' );
\tsvB = FRG_CountAb( made[0], 'autogen_silver_base' );
\tsvD = FRG_CountAb( made[0], 'autogen_silver_dmg' );
\tfx = inv.GetItemModifierInt( made[0], 'FRG_Fx', 0 );
\tif( fx <= 0 )
\t\tfx = FRG_FxCodeOf( donor );
\tinv.RemoveItem( made[0], 1 );
\tn = FRG_MintTokens( donor, false, st, sv, stB, stD, svB, svD, fx, abilities, true );
\treturn n;
}

%FRGCHEAT_BODY%

// Diagnostics: what in the bag has a previous tier waiting inside it
exec function frgprev()
{
\tvar w : W3PlayerWitcher;
\tvar ids : array< SItemUniqueId >;
\tvar nm, prev : name;
\tvar msg : string;
\tvar i, n : int;

\tw = GetWitcherPlayer();
\tw.inv.GetAllItems( ids );
\tmsg = "";
\tn = 0;
\tfor( i = 0; i < ids.Size(); i += 1 )
\t{
\t\tnm = w.inv.GetItemName( ids[i] );
\t\tprev = FRGX_PrevAny( nm );
\t\tif( prev == '' )
\t\t\tcontinue;
\t\tn += 1;
\t\tif( n <= 12 )
\t\t\tmsg = msg + NameToString( nm ) + " -> " + NameToString( prev ) + "<br>";
\t}
\ttheGame.GetGuiManager().ShowNotification( "FRG ladder: " + n + " items in the bag have a previous tier", 12000 );
\tif( msg != "" )
\t\ttheGame.GetGuiManager().ShowNotification( msg, 20000 );
}

// Diagnostics: how many RELIC properties are already studied, and where
// the rest still sleep. The crafting ring shows only what is in the bag.
exec function frgrelic()
{
	var w : W3PlayerWitcher;
	var msg : string;
	var i, id, have, total, shown : int;

	w = GetWitcherPlayer();
	total = 0;
	have = 0;
	msg = "";
	for( i = 1; i <= FRGL_Count(); i += 1 )
	{
		id = FRGL_IdAt( i );
		if( !FRGL_IsRelic( id ) || FRGL_IsArmorLine( id ) )
			continue;
		total += 1;
		if( w.inv.GetItemQuantityByName( FRGL_TokCard( id ) ) > 0 )
			have += 1;
		else if( shown < 8 )
		{
			shown += 1;
			msg = msg + NameToString( FRGL_CutDonor( id ) ) + "<br>";
		}
	}
	theGame.GetGuiManager().ShowNotification( "FRG relics: " + have + " of " + total
		+ " blade relic properties studied", 12000 );
	if( msg != "" )
		theGame.GetGuiManager().ShowNotification( "not yet studied, for example:<br>" + msg, 20000 );
}

// Diagnostics: why did the last craft refuse?
exec function frgwhy()
{
\tvar w : W3PlayerWitcher;

\tw = GetWitcherPlayer();
\tif( w && w.FRG_LastWhy != "" )
\t\ttheGame.GetGuiManager().ShowNotification( w.FRG_LastWhy, 20000 );
\telse
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the last verdict is empty - the window had no complaint", 12000 );
}

exec function frggoto( x : float, y : float, z : float )
{
\tvar v : Vector;

\tv.X = x;
\tv.Y = y;
\tv.Z = z;
\tGetWitcherPlayer().Teleport( v );
\ttheGame.GetGuiManager().ShowNotification( "FRG: moved to " + x + ", " + y + ", " + z, 6000 );
}

// Where am I (same as the game's pos(), kept close by for convenience).
exec function frgwhere()
{
\tvar v : Vector;

\tv = GetWitcherPlayer().GetWorldPosition();
\ttheGame.GetGuiManager().ShowNotification( "FRG: you are at " + v.X + ", " + v.Y + ", " + v.Z, 12000 );
}

exec function frgtokens()
{
\tvar w : W3PlayerWitcher;
\tvar items : array< SItemUniqueId >;
\tvar msg : string;
\tvar i, id, cnt : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tmsg = "FRG line tokens in the bag:<br>";
\tcnt = 0;
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tid = FRGL_IdAt( i );
\t\titems = w.inv.GetItemsByName( FRGL_TokCard( id ) );
\t\tif( items.Size() <= 0 )
\t\t\tcontinue;
\t\tmsg = msg + id + ": " + FRGL_Title( id ) + " x" + items.Size()
\t\t\t+ "  (" + FRGL_Stats( id ) + ")";
\t\tif( FRGL_IsJunk( id ) )
\t\t\tmsg = msg + "  [junk mark: +1 slot]";
\t\tmsg = msg + "<br>";
\t\tcnt += 1;
\t}
\tif( cnt == 0 )
\t\tmsg = msg + "none - sacrifice items carrying Redux pool abilities (masterwork/magical loot)";
\ttheGame.GetGuiManager().ShowNotification( msg, 25000 );
}

exec function frglines( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar dst : SItemUniqueId;
\tvar msg : string;
\tvar i, plus, junk : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tmsg = "FRG lines on " + w.inv.GetItemName( dst ) + ":<br>";
\tfor( i = 1; i <= FRGL_Count(); i += 1 )
\t{
\t\tjunk = FRGL_IdAt( i );
\t\tif( w.FRG_CountAb( dst, FRGL_Ability( junk ) ) <= 0 )
\t\t\tcontinue;
\t\tmsg = msg + junk + ": " + FRGL_Title( junk ) + "  (" + FRGL_Stats( junk ) + ")";
\t\tif( FRGL_IsJunk( junk ) )
\t\t\tmsg = msg + "  [junk mark]";
\t\tmsg = msg + "<br>";
\t}
\tif( w.FRGP_TierOf( dst ) > 0 )
\t\tmsg = msg + "blade tier " + w.FRGP_TierOf( dst ) + " of 4 (slots = tier)<br>";
\tfor( i = 1; i <= 4; i += 1 )
\t{
\t\tif( w.FRG_CountAb( dst, FRGD_Ability( i ) ) > 0 )
\t\t\tmsg = msg + "grooves level " + i + " (legacy, damage -" + ( 5 * i ) + "%)<br>";
\t}
\tif( w.FRGT_On( dst ) > 0 )
\t\tmsg = msg + "maker's mark: " + FRGT_Title( w.FRGT_On( dst ) )
\t\t\t+ "  (" + FRGT_Stats( w.FRGT_On( dst ) ) + ", no slot spent)<br>";
\tw.FRGL_CountOn( dst, plus, junk );
\tmsg = msg + "plus-lines " + plus + "/" + w.FRGL_Limit( dst )
\t\t+ " (base " + w.FRGL_BaseSlots( dst ) + " by grooves), junk marks " + junk
\t\t+ " (each opens +1 slot, cap %CAP%)";
\ttheGame.GetGuiManager().ShowNotification( msg, 25000 );
}

exec function frgline( slot : int, id : int )
{
\tvar w : W3PlayerWitcher;
\tvar dst, tok : SItemUniqueId;
\tvar plus, junk, verdict : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( id < 1 || id > FRGL_Count() )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: line id is 1.." + FRGL_Count() + " - see frgtokens()", 8000 );
\t\treturn;
\t}
\tif( !w.FRGL_FindToken( id, tok ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: no token of this line in the BAG - frgtokens() lists them", 9000 );
\t\treturn;
\t}
\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\t// род и слот тела — у того же судьи, что и в окне ремесла
\tverdict = FRGW_LineVerdict( id, w.inv.GetItemCategory( dst ),
\t\tw.inv.IsItemWeapon( dst ), true );
\tif( verdict == 3 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this line is for another kind of gear", 9000 );
\t\treturn;
\t}
\tif( verdict == 6 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: that bonus came off another body slot", 9000 );
\t\treturn;
\t}
\tif( !w.inv.ItemHasTag( dst, 'FRG_Blank' ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: lines are forged onto BLANKS only - regular items keep their card", 10000 );
\t\treturn;
\t}
\tif( w.FRG_CountAb( dst, FRGL_Ability( id ) ) > 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this line is already on the item - stacking the SAME line is not a thing", 10000 );
\t\treturn;
\t}
\tif( FRGL_IsRelic( id ) )
\t{
\t\tfor( plus = 1; plus <= FRGL_Count(); plus += 1 )
\t\t{
\t\t\tjunk = FRGL_IdAt( plus );
\t\t\tif( junk != id && FRGL_IsRelic( junk ) && w.FRG_CountAb( dst, FRGL_Ability( junk ) ) > 0 )
\t\t\t{
\t\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: a RELIC line is exclusive - one per item (carried: " + FRGL_Title( junk ) + ")", 12000 );
\t\t\t\treturn;
\t\t\t}
\t\t}
\t}
\tif( FRGL_WeightTag( id ) != '' && !w.inv.ItemHasTag( dst, FRGL_WeightTag( id ) ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this line is tailored for another armour weight class", 10000 );
\t\treturn;
\t}
\tif( FRGL_IsCursed( id ) && w.inv.GetItemModifierInt( dst, 'FRG_Fx', 0 ) != 13 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this gift demands its curse - the Dark Curse effect must live on the blade first", 12000 );
\t\treturn;
\t}
\tw.FRGL_CountOn( dst, plus, junk );
\tif( !FRGL_IsJunk( id ) && plus >= w.FRGL_Limit( dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: line slots are full (" + plus + "/" + w.FRGL_Limit( dst )
\t\t\t+ ") - a junk mark opens one more (cap %CAP%)", 12000 );
\t\treturn;
\t}

\tw.inv.AddItemCraftedAbility( dst, FRGL_Ability( id ), false );
\tif( w.FRG_CountAb( dst, FRGL_Ability( id ) ) <= 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the engine refused the ability - nothing changed, token kept", 10000 );
\t\treturn;
\t}
\tw.inv.RemoveItem( tok, 1 );
\tw.FRGL_CountOn( dst, plus, junk );
\ttheGame.GetGuiManager().ShowNotification( FRGL_Title( id ) + " forged into " + w.inv.GetItemName( dst )
\t\t+ "  (plus-lines " + plus + "/" + w.FRGL_Limit( dst ) + ").<br>Undo: frglinedrop(" + slot + ", " + id + ")", 15000 );
}

exec function frglinedrop( slot : int, id : int )
{
\tvar w : W3PlayerWitcher;
\tvar dst : SItemUniqueId;
\tvar made : array< SItemUniqueId >;
\tvar plus, junk, lim : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( !w.FRG_Slot( slot, dst ) )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\t\treturn;
\t}
\tif( w.FRG_CountAb( dst, FRGL_Ability( id ) ) <= 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this line is not on the item - frglines(" + slot + ") lists them", 9000 );
\t\treturn;
\t}
\t// pulling a junk mark must not orphan plus-lines its slot was carrying
\tif( FRGL_IsJunk( id ) )
\t{
\t\tw.FRGL_CountOn( dst, plus, junk );
\t\tlim = w.FRGL_BaseSlots( dst ) + junk - 1;
\t\tif( lim > %CAP% )
\t\t\tlim = %CAP%;
\t\tif( plus > lim )
\t\t{
\t\t\ttheGame.GetGuiManager().ShowNotification( "FRG: this mark carries a used line slot - remove a plus line first", 10000 );
\t\t\treturn;
\t\t}
\t}
\tif( w.FRG_StripAb( dst, FRGL_Ability( id ) ) <= 0 )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "FRG: the line would not come off - nothing changed", 10000 );
\t\treturn;
\t}
\t// tokens are KNOWLEDGE (eternal): re-mint only if the token was lost
\tif( w.inv.GetItemQuantityByName( FRGL_TokCard( id ) ) <= 0 )
\t{
\t\tmade = w.inv.AddAnItem( FRGL_TokCard( id ), 1 );
\t\tif( made.Size() > 0 )
\t\t{
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Part', 5 );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Line', id );
\t\t\tw.inv.SetItemModifierInt( made[0], 'FRG_Ver', FRG_TokenVer() );
\t\t}
\t}
\ttheGame.GetGuiManager().ShowNotification( FRGL_Title( id ) + " struck off "
\t\t+ w.inv.GetItemName( dst ) + " - the knowledge stays in your book", 12000 );
}
"""
    base_rows = ""
    for lvl, ab, _pen, _ru, _en in reversed(DMG_MARKS):
        base_rows += "\\tif( FRG_CountAb( item, '%s' ) > 0 )\n\\t\\treturn %d;\n" % (ab, 1 + lvl)

    groove_switch = ""
    for lvl, ab, _pen, _ru, _en in DMG_MARKS:
        groove_switch += "\\t\\tcase %d:\\treturn '%s';\n" % (lvl, ab)

    linecard_switch = ""
    for rec in LINES:
        linecard_switch += "\\t\\tcase %d:\\treturn 'frg_line_%d';\n" % (rec[0], rec[0])
    for c in CUT:
        linecard_switch += "\\t\\tcase %d:\\treturn '%s';\n" % (c["id"], c["card"])
    for rec in ARMOR_LINES:
        linecard_switch += "\\t\\tcase %d:\\treturn 'frg_line_%d';\n" % (rec[0], rec[0])

    temper_switch = ""
    for tid, ours, attrs, _ru, _en in TEMPER:
        temper_switch += "\\t\\tcase %d:\\treturn '%s';\n" % (tid, ours)
    temper_stats = ""
    for tid, ours, attrs, _ru, _en in TEMPER:
        temper_stats += "\\t\\tcase %d:\\treturn \"%s\";\n" % (tid, stat_text(attrs))

    s += """// ------------------------------------------------------------ temper ---
// The maker's mark - the user's "little extra for the effort": ONE small PURE
// plus of the player's choice, no minus, and it does NOT occupy a line slot.
// Honest because Redux hands the same tiny pure pluses to common loot for
// free (WEAPON_COMMON pool); ours is chosen, paid for, and capped at one.

function FRGT_Ability( id : int ) : name
{
\\tswitch( id )
\\t{
%TSWITCH%\\t}
\\treturn '';
}

function FRGT_Stats( id : int ) : string
{
\\treturn GetLocStringByKeyExt( "frgts_" + id );
}

function FRGT_Title( id : int ) : string
{
\\treturn GetLocStringByKeyExt( "frgt_" + id );
}

@addMethod( W3PlayerWitcher ) function FRGT_Count( item : SItemUniqueId ) : int
{
\\tvar i, n : int;

\\tfor( i = 1; i <= %TCOUNT%; i += 1 )
\\t{
\\t\\tif( FRG_CountAb( item, FRGT_Ability( i ) ) > 0 )
\\t\\t\\tn += 1;
\\t}
\\treturn n;
}

@addMethod( W3PlayerWitcher ) function FRGT_On( item : SItemUniqueId ) : int
{
\\tvar i : int;

\\tfor( i = 1; i <= %TCOUNT%; i += 1 )
\\t{
\\t\\tif( FRG_CountAb( item, FRGT_Ability( i ) ) > 0 )
\\t\\t\\treturn i;
\\t}
\\treturn 0;
}

function FRGD_Ability( lvl : int ) : name
{
\\tswitch( lvl )
\\t{
%GSWITCH%\\t}
\\treturn '';
}

// RETIRED (design doc v2, P-6): quality tiers open line slots now. Legacy
// grooves on old blanks keep counting; new ones are not cut.
exec function frgblade( slot : int, lvl : int )
{
\\tvar w : W3PlayerWitcher;
\\tvar dst : SItemUniqueId;
\\tvar i, plus, junk : int;

\\tw = GetWitcherPlayer();
\\tif( !w ) return;

\\ttheGame.GetGuiManager().ShowNotification( "Grooves are retired: the blade's path (quality tiers) opens line slots now. Existing grooves still count.", 12000 );
\\treturn;

\\tif( lvl < 0 || lvl > 4 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: groove level is 0..4 (0 none .. 4 = -20% damage, 5 slots)", 10000 );
\\t\\treturn;
\\t}
\\tif( !w.FRG_Slot( slot, dst ) )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\\t\\treturn;
\\t}
\\tif( slot < 4 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: grooves fit swords for now (slots 4-5)", 8000 );
\\t\\treturn;
\\t}
\\tif( !w.inv.ItemHasTag( dst, 'FRG_Blank' ) )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: grooves are cut into BLANKS only", 9000 );
\\t\\treturn;
\\t}
\\t// lowering the level must not orphan lines already engraved
\\tw.FRGL_CountOn( dst, plus, junk );
\\ti = 1 + lvl + junk;
\\tif( i > %CAP% )
\\t\\ti = %CAP%;
\\tif( plus > i )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: engraved lines (" + plus + ") would not fit level " + lvl + " - strike lines off first", 12000 );
\\t\\treturn;
\\t}

\\tfor( i = 1; i <= 4; i += 1 )
\\t\\tw.FRG_StripAb( dst, FRGD_Ability( i ) );
\\tif( lvl > 0 )
\\t{
\\t\\tw.inv.AddItemCraftedAbility( dst, FRGD_Ability( lvl ), false );
\\t\\tif( w.FRG_CountAb( dst, FRGD_Ability( lvl ) ) <= 0 )
\\t\\t{
\\t\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: the engine refused the groove - the blank is groove-free now", 10000 );
\\t\\t\\treturn;
\\t\\t}
\\t}
\\ttheGame.GetGuiManager().ShowNotification( "Grooves level " + lvl + " on " + w.inv.GetItemName( dst )
\\t\\t+ ": plus-line slots " + w.FRGL_Limit( dst ) + " (junk marks add +1 each, cap %CAP%)", 12000 );
}

exec function frgtemper( slot : int, id : int )
{
\\tvar w : W3PlayerWitcher;
\\tvar dst : SItemUniqueId;
\\tvar have, lim : int;

\\tw = GetWitcherPlayer();
\\tif( !w ) return;

\\ttheGame.GetGuiManager().ShowNotification( "The console mark is retired: use the Maker's mark recipe (blade + stamp) at any smith", 11000 );
\\treturn;

\\tif( id < 1 || id > %TCOUNT% )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: mark id is 1..%TCOUNT%: 1 poise, 2 armor pen, 3 counter, 4 crit dmg", 10000 );
\\t\\treturn;
\\t}
\\tif( !w.FRG_Slot( slot, dst ) )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: target slot is empty (0..5)", 8000 );
\\t\\treturn;
\\t}
\\tif( slot < 4 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: marks fit swords for now (slots 4-5)", 8000 );
\\t\\treturn;
\\t}
\\tif( !w.inv.ItemHasTag( dst, 'FRG_Blank' ) )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: the maker's mark goes onto BLANKS only", 9000 );
\\t\\treturn;
\\t}
\\t// One mark per item - but a FULLY assembled piece (every line slot filled)
\\t// earns a SECOND one: the maker signs finished work. The "pleasant bonus"
\\t// for seeing the build through.
\\tw.FRGL_CountOn( dst, have, lim );
\\tlim = w.FRGL_Limit( dst );
\\tif( w.FRGT_Count( dst ) >= 2 || ( w.FRGT_Count( dst ) >= 1 && ( have < lim || lim < 2 ) ) )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: one mark per item - a SECOND is earned only by a fully assembled piece (all line slots filled)", 12000 );
\\t\\treturn;
\\t}
\\tif( w.FRG_CountAb( dst, FRGT_Ability( id ) ) > 0 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: this exact mark is already burned in - pick another", 9000 );
\\t\\treturn;
\\t}
\\tif( w.GetMoney() < 1 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: even a mark wants 1 coin", 8000 );
\\t\\treturn;
\\t}

\\tw.inv.AddItemCraftedAbility( dst, FRGT_Ability( id ), false );
\\tif( w.FRG_CountAb( dst, FRGT_Ability( id ) ) <= 0 )
\\t{
\\t\\ttheGame.GetGuiManager().ShowNotification( "FRG: the engine refused the mark - nothing changed", 9000 );
\\t\\treturn;
\\t}
\\tw.RemoveMoney( 1 );
\\ttheGame.GetGuiManager().ShowNotification( FRGT_Title( id ) + " (" + FRGT_Stats( id ) + ") burned into "
\\t\\t+ w.inv.GetItemName( dst ) + ". No line slot spent.", 12000 );
}
"""
    lc_pairs = ([(rec[0], "'frg_line_%d'" % rec[0]) for rec in LINES]
                + [(c["id"], "'%s'" % c["card"]) for c in CUT]
                + [(rec[0], "'frg_line_%d'" % rec[0]) for rec in ARMOR_LINES])
    s += chunked_switch("FRGL_TokCard", "name", "''", lc_pairs)

    # ---- ПОРОКИ: марка -> абилка / вес / карточка / имя ---------------------
    from lines_data import FLAWS
    s += "// FLAW marks: the optional fourth slot of the forging recipe.\n"
    s += "// Weight 1 (light) opens one ORDINARY property slot, weight 2\n"
    s += "// (heavy) opens a RELIC one - a fat price buys a fat reward.\n"
    s += "function FRGF_Count() : int\n{\n\treturn %d;\n}\n\n" % len(FLAWS)
    s += chunked_switch("FRGF_Ability", "name", "''",
                        [(f[0], "'%s'" % f[1]) for f in FLAWS])
    s += chunked_switch("FRGF_Weight", "int", "0",
                        [(f[0], str(f[5])) for f in FLAWS])
    s += chunked_switch("FRGF_TokCard", "name", "''",
                        [(f[0], "'frg_flaw_%d'" % f[0]) for f in FLAWS])
    s += chunked_switch("FRGF_Title", "string", '""',
                        [(f[0], 'GetLocStringByKeyExt( "frgf_%d" )' % f[0]) for f in FLAWS])
    s += chunked_switch("FRGF_Stats", "string", '""',
                        [(f[0], 'GetLocStringByKeyExt( "frgfs_%d" )' % f[0]) for f in FLAWS])
    s += "function FRGF_IdAt( i : int ) : int\n{\n\tswitch( i )\n\t{\n"
    for _i, _f in enumerate(FLAWS):
        s += "\t\tcase %d:\treturn %d;\n" % (_i + 1, _f[0])
    s += "\t}\n\treturn 0;\n}\n\n"
    s += ("function FRGF_OfTokCard( tok : name ) : int\n{\n"
          "\tvar i, id : int;\n\n"
          "\tfor( i = 1; i <= FRGF_Count(); i += 1 )\n\t{\n"
          "\t\tid = FRGF_IdAt( i );\n"
          "\t\tif( FRGF_TokCard( id ) == tok )\n\t\t\treturn id;\n"
          "\t}\n\treturn 0;\n}\n\n")
    s += ("// which flaw sits on this blade (0 = none)\n"
          "@addMethod( W3PlayerWitcher ) function FRGF_On( item : SItemUniqueId ) : int\n{\n"
          "\tvar i, id : int;\n\n"
          "\tfor( i = 1; i <= FRGF_Count(); i += 1 )\n\t{\n"
          "\t\tid = FRGF_IdAt( i );\n"
          "\t\tif( FRG_CountAb( item, FRGF_Ability( id ) ) > 0 )\n\t\t\treturn id;\n"
          "\t}\n\treturn 0;\n}\n\n")
    # класс эквивалентности стат-профиля: близнецы по содержанию (разные
    # доноры, одинаковые статы - Netflix-мечи, стартовые сапоги, булавы) =
    # ОДНО свойство при сборке набора; класс = min id группы, 0 = вне реестра
    def _statnorm(attrs):
        return tuple(sorted((a, k, round(float(v), 4)) for a, k, v in attrs))
    _classes = {}
    for _id, _keyt in ([(rec[0], _statnorm(rec[4])) for rec in LINES]
                       + [(c["id"], _statnorm(c["stats"])) for c in CUT]
                       + [(rec[0], _statnorm(rec[4])) for rec in ARMOR_LINES]):
        _classes.setdefault(_keyt, []).append(_id)
    _sk_pairs = []
    for _ids in _classes.values():
        for _id in _ids:
            _sk_pairs.append((_id, str(min(_ids))))
    s += "// stat-profile class: content twins share one key (0 = no key)\n"
    s += chunked_switch("FRGL_StatKey", "int", "0", _sk_pairs)

    # ---- И-2/И-3: оси строк и конверт мира (одобрено ГД: «го») -------------
    import json as _json2
    import os as _os2

    def _axes_of(stats):
        out = [(a, float(v)) for a, k, v in stats
               if k != "effect" and 0 < float(v) <= 1.5]
        out.sort(key=lambda p: -p[1])
        return out[:4]

    def _dom_of(stats):
        for a, k, v in stats:
            if k == "effect":
                return a
        ax = _axes_of(stats)
        return ax[0][0] if ax else ""

    _dom_pairs, _pa_pairs, _pv_pairs = [], [], []
    for _id, _st in ([(r[0], r[4]) for r in LINES]
                     + [(c["id"], c["stats"]) for c in CUT]
                     + [(r[0], r[4]) for r in ARMOR_LINES]):
        _d = _dom_of(_st)
        if _d:
            _dom_pairs.append((_id, "'%s'" % _d))
        for _k, (_a, _v) in enumerate(_axes_of(_st)):
            _pa_pairs.append((_id * 4 + _k, "'%s'" % _a))
            _pv_pairs.append((_id * 4 + _k, str(int(round(_v * 100)))))
    s += "// dominant axis of a line: one axis - one line on a blade (I-2)\n"
    s += chunked_switch("FRGL_DomAxis", "name", "''", _dom_pairs)
    s += "// every percent plus of a line, key = id*4+k (axis caps, I-3)\n"
    s += chunked_switch("FRGL_PlusAxis", "name", "''", _pa_pairs)
    s += chunked_switch("FRGL_PlusVal", "int", "0", _pv_pairs)
    _caps = _json2.load(open(_os2.path.join(_os2.path.dirname(
        _os2.path.abspath(__file__)), "axis_caps.json"), encoding="utf-8"))
    s += "// the world envelope: max of an axis on ONE reachable Redux item\n"
    s += "function FRGL_AxisCap( a : name ) : int\n{\n"
    for _a in sorted(_caps):
        s += "\tif( a == '%s' )\n\t\treturn %d;\n" % (
            _a, int(round(_caps[_a][0] * 100)))
    s += "\treturn 999;\n}\n\n"

    # ---- чит-команда frgcheat(): отборные доноры для тестов ------------------
    try:
        _reach2 = _json2.load(open(_os2.path.join(_os2.path.dirname(
            _os2.path.abspath(__file__)), "reachable.json"), encoding="utf-8"))
    except Exception:
        _reach2 = {}
    _SWC = ("steelsword", "silversword")

    def _net2(st):
        p = n = 0.0
        for a, k, v in st:
            v = float(v)
            if k == "effect" or abs(v) > 1.5:
                continue
            if v > 0:
                p += v
            else:
                n += -v
        return p - n
    _cheat = []
    _seen2 = set()
    # реликтовые достижимые мечи
    for _c in CUT:
        if _c.get("cat") in _SWC and _c.get("relic") and _reach2.get(_c["donor"], False):
            if _c["donor"] not in _seen2:
                _seen2.add(_c["donor"])
                _cheat.append(_c["donor"])
    # гроссмейстеры школ: "... School ... sword 4" (обе стали)
    for _c in CUT:
        _d = _c["donor"]
        if (_c.get("cat") in _SWC and "School" in _d and _d.endswith(" 4")
                and _reach2.get(_d, False) and _d not in _seen2):
            _seen2.add(_d)
            _cheat.append(_d)
    # интересные уники: топ-12 достижимых по чистой пользе профиля
    import collections as _coll2
    _prof = _coll2.defaultdict(float)
    for _c in CUT:
        if _c.get("cat") in _SWC and _reach2.get(_c["donor"], False):
            _prof[_c["donor"]] += _net2(_c["stats"])
    _extra = 0
    for _d, _v in sorted(_prof.items(), key=lambda kv: -kv[1]):
        if _d in _seen2:
            continue
        _seen2.add(_d)
        _cheat.append(_d)
        _extra += 1
        if _extra >= 12:
            break
    _body = "// Test cheat: tokens of relic swords, grandmaster school blades\n"
    _body += "// and a dozen strongest reachable uniques. Generated from data.\n"
    _body += "exec function frgcheat()\n{\n"
    _body += "\tvar w : W3PlayerWitcher;\n\tvar n : int;\n\n"
    _body += "\tw = GetWitcherPlayer();\n\tn = 0;\n"
    for _d in _cheat:
        _body += "\tn += w.FRG_CheatMint( '%s' );\n" % _d
    _body += ("\ttheGame.GetGuiManager().ShowNotification( "
              "\"FRG cheat: \" + n + \" new tokens from %d donors\", 12000 );\n"
              % len(_cheat))
    _body += "}\n"
    s = s.replace("%FRGCHEAT_BODY%", _body)
    s = s.replace("%GSWITCH%", groove_switch)
    s = s.replace("%TSWITCH%", temper_switch)
    s = s.replace("%TSTATS%", temper_stats)
    s = s.replace("%TCOUNT%", str(len(TEMPER)))
    s = s.replace("%BASESLOTS%", base_rows)
    s = s.replace("%TOKEN%", TOKEN_ITEM)
    s = s.replace("%BASE%", str(LINE_LIMIT_BASE))
    s = s.replace("%CAP%", str(LINE_LIMIT_MAX))
    return s

# ревизия витрин (пишет build_blanks.py -> stock_rev.json): сменился состав
# жетонов — сменился ключ факта — встреченный торговец доливается ещё раз.
# Нет файла — ревизия "0" (долив всё равно без двойников).
import json as _json_rev, os as _os_rev
_rev_p = _os_rev.path.join(_os_rev.path.dirname(_os_rev.path.abspath(__file__)), "stock_rev.json")
_rev = _json_rev.load(open(_rev_p, encoding="utf-8")) if _os_rev.path.exists(_rev_p) else {}
assert WS.count("@@FRG_REV_GM@@") == 1 and WS.count("@@FRG_REV_EL@@") == 1
WS = (WS.replace("@@FRG_REV_GM@@", _rev.get("_FRG_stock_gm", "0"))
        .replace("@@FRG_REV_EL@@", _rev.get("_FRG_stock_elihal", "0")))
print("  ревизия витрин: гроссмейстер %s, Элихаль %s"
      % (_rev.get("_FRG_stock_gm", "0"), _rev.get("_FRG_stock_elihal", "0")))
import json as _json_sl, os as _os_sl
_sl_p = _os_sl.path.join(_os_sl.path.dirname(_os_sl.path.abspath(__file__)), "stock_list.json")
_sl = _json_sl.load(open(_sl_p, encoding="utf-8")) if _os_sl.path.exists(_sl_p) else {}
def _shoplooks_ws():
    # ⛔ Одна функция на 666 PushBack валит компилятор WitcherScript («memory
    # exhausted», 21.09). Режем на мелкие функции-куски по 25 имён; диспетчер
    # зовёт нужные. Каждая функция маленькая — компилятор не давится.
    B = chr(92) + "t"
    CHUNK = 25
    helpers = ""
    hid = 0
    calls_of = {}
    for shop in sorted(_sl):
        names = _sl[shop]
        calls = []
        for i in range(0, len(names), CHUNK):
            fn = "FRGV_sl_%d" % hid
            hid += 1
            helpers += "function %s( out a : array< name > )\n{\n" % fn
            for nm in names[i:i + CHUNK]:
                helpers += B + "a.PushBack( '%s' );\n" % nm
            helpers += "}\n\n"
            calls.append(fn)
        calls_of[shop] = calls
    out = "function FRGV_ShopLooks( shop : name ) : array< name >\n{\n"
    out += B + "var a : array< name >;\n"
    first = True
    for shop in sorted(_sl):
        kw = "if" if first else "else if"
        first = False
        out += B + "%s( shop == '%s' )\n" % (kw, shop) + B + "{\n"
        for fn in calls_of[shop]:
            out += B + B + "%s( a );\n" % fn
        out += B + "}\n"
    out += B + "return a;\n}\n"
    return helpers + out
WS = WS.replace("@@FRG_SHOPLOOKS@@", _shoplooks_ws())
WS = WS + _frgl_section()

print("=" * 66)
print("  modForgeLab — кузница, этапы 1-2")
print("=" * 66)

body = WS.replace("\\t", "\t")
if "\\t" in body:
    raise SystemExit("буквальные \\t остались — не записываю")

d = os.path.join(MOD, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "ForgeLab.ws")
data = body.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
print("   [ok] ForgeLab.ws  %d Б  UTF-16 LE + BOM  (табуляций: %d)"
      % (len(data), body.count("\t")))

ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read().decode("utf-8", "replace")
if "[modForgeLab]" in raw:
    print("   [--] уже прописан в mods.settings")
else:
    raw = raw.rstrip("\r\n") + "\r\n[modForgeLab]\r\nEnabled=1\r\nPriority=%d\r\n" % PRIORITY
    open(ms, "wb").write(raw.encode("utf-8"))
    print("   [ok] прописан в mods.settings, Priority=%d" % PRIORITY)

print()
print("  ЦИКЛ ЭТАПА 2 (после перезапуска игры):")
print("     frgsplit('Cheesecutter')     жертва: Эмменталь -> детали, -1 монета")
print("     frgparts()                   что за детали лежат в сумке")
print("     frgapply('Cheesecutter',4,1) ОБЛИК Эмменталя -> надетый стальной (жетон не тратится)")
print("     frglook0(4)                  снять облик, вернуть родной вид")
print("")
print("  КОНСТРУКТОР СТРОК (v1, оружие):")
print("     frgtokens()                  жетоны строк в сумке (id, имя, статы)")
print("     frglines(4)                  строки на надетом мече, лимит, свободно")
print("     frgline(4, id)               вковать строку id в надетую БОЛВАНКУ")
print("     frglinedrop(4, id)           снять строку, жетон вернётся в сумку")
print("  ПУТЬ КЛИНКА (фаза 1, одобрено 21.08.2026) — всё в окне кузнеца-ПОДМАСТЕРЬЯ,")
print("  группа рецептов «Путь клинка»: заготовка -> ковка (заготовка+облик+урон) ->")
print("  улучшения I/II/III (тир = качество: слоты 1..4, урон растёт формулой игры) ->")
print("  гравировка. Жетоны ВЕЧНЫ (знание). Желоба сняты с производства (легаси).")
print("     junk-марка открывает +1 слот сверх тира, потолок 5")
print("     frgtemper(4, 1..4)           клеймо: чистый плюс вне лимита; ВТОРОЕ - за полную сборку")
print("     frgapply('Cheesecutter',4,2) урон Эмменталя -> надетый стальной")
print("     frgapply('Cheesecutter',4,3) проценты -> туда же")
print("     frgapply('Cheesecutter',4,4) эффект-облако -> туда же")
print("     fstat(4)                     сверить, что легло")
print("     сейв -> выход -> загрузка    облако должно ВЕРНУТЬСЯ само")
