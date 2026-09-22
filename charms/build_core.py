# -*- coding: utf-8 -*-
"""
Собирает ЯДРО мода «Камни чар» — modCharmTransfer.

Что делает мод:
  * пустой камень чар, приложенный к НАДЕТОМУ реликтовому оружию, снимает копию
    его чар — оружие остаётся целым (решение ГД 09.09);
  * заряженный камень, приложенный к другому оружию, накладывает эти чары;
  * камень очищения снимает наложенные нами чары обратно.

Механика вскрыта и доказана ещё 13-14.08 (вольт: witcher3-forge-spec):
чары живут ЯРЛЫКОМ на карточке, при экипировке W3EE читает ярлык и вешает бафф.
Ярлык, добавленный на ЭКЗЕМПЛЯР, эта функция не видит — поэтому носителем служит
ЧИСЛО на вещи (переживает сейв), а бафф вешает наша обёртка того же места.

⚠️ В .ws НЕТ кириллицы (кодировщик её не переваривает) — все игровые надписи
   английские, как в modSetBonusTransfer.
⚠️ Папка мода не описана в split/spec.py — пересобирать этим скриптом.
"""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GAME = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
DOCS = os.path.join(os.environ["USERPROFILE"], "Documents", "The Witcher 3")
MOD = os.path.join(GAME, "mods", "modCharmTransfer")
PRIORITY = 19

# W3EE вмёржил в окно инвентаря Quick Slots и ПЕРЕИМЕНОВАЛ класс. Ванильное имя
# тут не скомпилируется (грабли из modSetBonusTransfer, записаны в его исходнике).
VANILLA = "--vanilla" in sys.argv
MENU_CLASS = "CR4InventoryMenu" if VANILLA else "WmkCR4InventoryMenu"

from data import CHARMS, STONE, EMPTY_NAME, CLEAN_NAME


def _switch(body_lines, indent=2):
    return "".join("\t" * indent + l + "\n" for l in body_lines)


TAGS_SW = _switch(["case %d:\treturn '%s';" % (c, tag) for c, tag, _t, _r, _e in CHARMS])
TYPE_SW = _switch(["case %d:\treturn %s;" % (c, et) for c, _tag, et, _r, _e in CHARMS])
CARD_SW = _switch(["if( dm.ItemHasTag( itemName, '%s' ) )\treturn %d;" % (tag, c)
                   for c, tag, _t, _r, _e in CHARMS], indent=1)
STONE_SW = _switch(["case %d:\treturn '%s';" % (c, STONE % c) for c, _tg, _t, _r, _e in CHARMS])
SCHEM_SW = _switch(["case '%s schematic':\treturn %d;" % (STONE % c, c)
                    for c, _tg, _t, _r, _e in CHARMS])

WS = """// modCharmTransfer - charmstones.
//
// Takes a RELIC CHARM off a weapon onto a stone, and lays it on another weapon.
//
// HOW A CHARM IS BUILT (W3EE, read 13.08 - vault "witcher3-forge-spec")
//   1. the charm is a TAG on the item CARD          SwordGasEffect and kin
//   2. on equip, HandleRelicAbilities reads the tag and hangs a BUFF
//   3. the buff is what actually works in a fight
//   A tag added to an INSTANCE is invisible to step 2 (it reads GetItemTags of
//   the card). So the carrier here is a NUMBER on the item - modifiers survive
//   a save - and the buff is hung by our own wrap of the very same funnel.
//
// RULES
//   * weapons only. W3EE returns from HandleRelicAbilities for anything else,
//     so armour cannot carry a charm at all - that is the game, not us.
//   * one charm per weapon. The game takes the first matching tag and stops,
//     so a blade with its OWN charm refuses a second one.
//   * the source keeps its charm: the stone takes a COPY (GD call 09.09).
//
// CONSOLE
//   chtinfo()        what is on the equipped weapons
//   chtgive()        one of every stone, for testing
//   chtuse(4, 10)    lay charm 10 on the steel slot (4 steel, 5 silver)
//   chtclear(4)      strip our charm off that slot

// ------------------------------------------------------------- settings ---
// Read from the mod's own menu group; the group name is repeated INSIDE this
// file, so renaming it in the XML silently drops every setting to its fallback.

function CHT_Str( varName : name, fallback : string ) : string
{
\tvar s : string;

\ts = theGame.GetInGameConfigWrapper().GetVarValue( 'CharmTransfer', varName );
\tif( s == "" )
\t\treturn fallback;

\treturn s;
}

function CHT_Bool( varName : name, fallback : bool ) : bool
{
\tvar s : string;

\ts = CHT_Str( varName, "" );
\tif( s == "" )
\t\treturn fallback;

\tif( s == "true" || s == "1" )
\t\treturn true;

\treturn false;
}

function CHT_Say( msg : string )
{
\tif( CHT_Bool( 'ShowMessages', true ) )
\t\ttheGame.GetGuiManager().ShowNotification( msg, 7000 );
}

// ---------------------------------------------------------------- tables ---

function CHT_FxTag( code : int ) : name
{
\tswitch( code )
\t{
%s\t}
\treturn '';
}

function CHT_FxType( code : int ) : EEffectType
{
\tswitch( code )
\t{
%s\t}
\treturn EET_Undefined;
}

function CHT_StoneOf( code : int ) : name
{
\tswitch( code )
\t{
%s\t}
\treturn '';
}

// The charm a CARD carries natively. Asked of the definitions manager, because
// that is where the card's own tags live (an instance tag would not show here,
// and that asymmetry is exactly why this mod exists).
function CHT_CardCode( itemName : name ) : int
{
\tvar dm : CDefinitionsManagerAccessor;

\tdm = theGame.GetDefinitionsManager();
%s\treturn 0;
}

// The red tooltip line. W3EE's own text builder works off a card NAME, so we
// hand it any card carrying the same tag and let it do words, colour and
// parameters itself - zero duplicated text.
@addMethod( W3PlayerWitcher ) function CHT_RedLine( code : int ) : string
{
\tvar dm : CDefinitionsManagerAccessor;
\tvar reps : array< name >;
\tvar tag : name;
\tvar s : string;
\tvar i : int;

\ttag = CHT_FxTag( code );
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

// The blades this charm is native to, by their LOCALISED names, "A / B".
// Read from the game itself: a charm is a card tag, so every card carrying
// the tag is a source. Our own stones carry the tag too - they are skipped.
//
// Why not bake the names into the mod's strings: the game's .w3strings hold
// no text keys at all (checked by decoding content0/ep1/modW3EE), so at build
// time there is nothing to read. In the game one call does it, in any
// language, always matching what the player sees.
@addMethod( W3PlayerWitcher ) function CHT_SourcesOf( code : int ) : string
{
\tvar dm : CDefinitionsManagerAccessor;
\tvar reps : array< name >;
\tvar res, one : string;
\tvar tag : name;
\tvar i : int;

\ttag = CHT_FxTag( code );
\tif( tag == '' )
\t\treturn "";

\tdm = theGame.GetDefinitionsManager();
\treps = dm.GetItemsWithTag( tag );
\tfor( i = 0; i < reps.Size(); i += 1 )
\t{
\t\tif( dm.ItemHasTag( reps[i], 'CHT_Stone' ) )
\t\t\tcontinue;
\t\tif( !dm.IsItemWeapon( reps[i] ) )
\t\t\tcontinue;
\t\tone = GetLocStringByKeyExt( dm.GetItemLocalisationKeyName( reps[i] ) );
\t\tif( one == "" || StrContains( res, one ) )
\t\t\tcontinue;
\t\tif( res != "" )
\t\t	res = res + " / ";
\t	res = res + one;
\t}
\treturn res;
}

// The full line for a stone: what the charm does, and where it comes from.
@addMethod( W3PlayerWitcher ) function CHT_StoneLine( code : int ) : string
{
\tvar res, src : string;

	res = CHT_RedLine( code );
\tsrc = CHT_SourcesOf( code );
\tif( src != "" )
\t{
\t\tif( res != "" )
\t\t	res = res + "<br>";
\t	res = res + GetLocStringByKeyExt( "cht_from" ) + " " + src;
\t}
\treturn res;
}

// Which charm a recipe makes. The name carries the code, but a name cannot be
// taken apart in this build (no StringToName), so the table is written out.
function CHT_CodeForSchematic( schematicName : name ) : int
{
\tswitch( schematicName )
\t{
%s\t}
\treturn 0;
}

// Does the player HAVE a weapon carrying this charm? The weapon is not spent -
// owning it is the price, exactly as owning a full set is the price of a school
// runestone in modSetBonusTransfer.
//
// Only a GENUINE charm counts: the tag lives on the card, and GetItemsByTag
// reads cards. A charm we laid ourselves is not a source - otherwise a stone
// would breed stones.
@addMethod( W3PlayerWitcher ) function CHT_HasCharm( code : int ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar item : SItemUniqueId;
\tvar tag : name;
\tvar i : int;

\ttag = CHT_FxTag( code );
\tif( tag == '' )
\t\treturn false;

\titems = inv.GetItemsByTag( tag );
\tfor( i = 0; i < items.Size(); i += 1 )
\t{
\t\tif( inv.IsItemWeapon( items[i] ) )
\t\t\treturn true;
\t}

\t// worn blades are checked apart: the bag listing has been caught before not
\t// returning what is equipped
\tif( GetItemEquippedOnSlot( EES_SteelSword, item )
\t\t&& CHT_CardCode( inv.GetItemName( item ) ) == code )
\t\treturn true;
\tif( GetItemEquippedOnSlot( EES_SilverSword, item )
\t\t&& CHT_CardCode( inv.GetItemName( item ) ) == code )
\t\treturn true;

\treturn false;
}

// One hook covers both the list and the craft itself: Craft() asks this first,
// so a refusal here greys the recipe out AND blocks the attempt.
@wrapMethod( W3CraftingManager ) function CanCraftSchematic( schematicName : name, checkMerchant : bool ) : ECraftingException
{
\tvar code : int;
\tvar w : W3PlayerWitcher;

\tcode = CHT_CodeForSchematic( schematicName );
\tif( code > 0 )
\t{
\t\tw = GetWitcherPlayer();
\t\tif( w && !w.CHT_HasCharm( code ) )
\t\t\treturn ECE_TooFewIngredients;
\t}

\treturn wrappedMethod( schematicName, checkMerchant );
}

// --------------------------------------------------------------- the work ---

// What charm this weapon shows right now: its own if the card carries one,
// ours otherwise.
@addMethod( W3PlayerWitcher ) function CHT_CodeOn( item : SItemUniqueId ) : int
{
\tvar code : int;

\tif( !inv.IsIdValid( item ) )
\t\treturn 0;

\tcode = CHT_CardCode( inv.GetItemName( item ) );
\tif( code > 0 )
\t\treturn code;

\treturn inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
}

@addMethod( W3PlayerWitcher ) function CHT_Equipped( item : SItemUniqueId ) : bool
{
\treturn GetItemSlot( item ) != EES_InvalidSlot;
}

// Lays a charm on a weapon. The buff is hung at once when the weapon is worn;
// otherwise it waits for the equip, where our wrap picks it up.
@addMethod( W3PlayerWitcher ) function CHT_Apply( item : SItemUniqueId, code : int ) : bool
{
\tvar old : int;

\tif( !inv.IsIdValid( item ) || code <= 0 )
\t\treturn false;

\told = inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\tif( old == code )
\t\treturn false;

\tif( old > 0 && CHT_Equipped( item ) )
\t\tRemoveBuff( CHT_FxType( old ), false, "RelicWeaponBuff" );

\tinv.SetItemModifierInt( item, 'CHT_Fx', code );
\tif( CHT_Equipped( item ) )
\t\tAddEffectDefault( CHT_FxType( code ), this, "RelicWeaponBuff", false );

\treturn true;
}

@addMethod( W3PlayerWitcher ) function CHT_Strip( item : SItemUniqueId ) : bool
{
\tvar old : int;

\tif( !inv.IsIdValid( item ) )
\t\treturn false;

\told = inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\tif( old <= 0 )
\t\treturn false;

\tif( CHT_Equipped( item ) )
\t\tRemoveBuff( CHT_FxType( old ), false, "RelicWeaponBuff" );

\tinv.SetItemModifierInt( item, 'CHT_Fx', 0 );
\treturn true;
}

// One entry point for every stone: empty ones take a copy, charged ones lay it
// on, the cleansing one takes ours back off.
@addMethod( W3PlayerWitcher ) function CHT_UseStone( stone : SItemUniqueId, target : SItemUniqueId )
{
\tvar code : int;

\tif( !inv.IsIdValid( target ) )
\t\treturn;

\tif( !inv.IsItemWeapon( target ) )
\t{
\t\tCHT_Say( "A charm only holds on a weapon - W3EE gives armour none." );
\t\treturn;
\t}

\t// the cleansing stone: the same tool pointed the other way
\tif( inv.ItemHasTag( stone, 'CHT_Clean' ) )
\t{
\t\tif( CHT_Strip( target ) )
\t\t\tCHT_Say( "The laid charm is gone. The weapon's own charm, if it had one, stays." );
\t\telse
\t\t\tCHT_Say( "Nothing was laid on this weapon." );

\t\treturn;
\t}

\t// An empty stone is CRAFTING MATERIAL now (GD call 09.09): the charm is
\t// recorded at a craftsman's, with the relic weapon as an ingredient that
\t// is never spent. So an empty stone has nothing to do here.
\tcode = CHT_CardCode( inv.GetItemName( stone ) );
\tif( code <= 0 )
\t{
\t\tCHT_Say( "This stone carries no charm." );
\t\treturn;
\t}

\t// A blade that already carries a charm takes the new one anyway - the old
\t// is REPLACED (user 13.09). A native charm is a card tag and cannot be
\t// erased, so the swap happens in the buff funnel: our wrap drops the
\t// native buff whenever our own code is set on the item.

\tif( CHT_Apply( target, code ) )
\t{
\t\tCHT_Say( "The charm is laid on: " + CHT_RedLine( code ) );

\t\t// off by default: the stone is a tool, not a consumable
\t\tif( CHT_Bool( 'ConsumeStone', false ) )
\t\t\tinv.RemoveItem( stone, 1 );
\t}
\telse
\t{
\t\tCHT_Say( "This weapon already carries that charm." );
\t}
}

// ------------------------------------------------------------- the funnel ---

// A transferred charm lives as a buff and must follow equip state. W3EE has
// exactly one funnel for that - the same one it uses for genuine relics.
@wrapMethod( W3EEEquipmentHandler ) function HandleRelicAbilities( witcher : W3PlayerWitcher, item : SItemUniqueId, equip : bool )
{
\tvar fx, native : int;

\twrappedMethod( witcher, item, equip );

\tif( !witcher )
\t\treturn;

\tfx = witcher.inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\tif( fx <= 0 )
\t\treturn;

\t// ours REPLACES the weapon's own charm: the original call above has just
\t// hung the native buff, so it goes down and ours goes up instead
\tnative = CHT_CardCode( witcher.inv.GetItemName( item ) );
\tif( native > 0 && native != fx )
\t\twitcher.RemoveBuff( CHT_FxType( native ), false, "RelicWeaponBuff" );

\tif( equip )
\t\twitcher.AddEffectDefault( CHT_FxType( fx ), witcher, "RelicWeaponBuff", false );
\telse
\t\twitcher.RemoveBuff( CHT_FxType( fx ), false, "RelicWeaponBuff" );
}

// Buffs do not survive a load; the numbers on the items do. Re-arm on spawn.
@wrapMethod( W3PlayerWitcher ) function OnSpawned( spawnData : SEntitySpawnData )
{
\tvar item : SItemUniqueId;
\tvar fx : int;

\twrappedMethod( spawnData );

\tif( GetItemEquippedOnSlot( EES_SteelSword, item ) )
\t{
\t\tfx = inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\t\tif( fx > 0 )
\t\t\tAddEffectDefault( CHT_FxType( fx ), this, "RelicWeaponBuff", false );
\t}
\tif( GetItemEquippedOnSlot( EES_SilverSword, item ) )
\t{
\t\tfx = inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\t\tif( fx > 0 )
\t\t\tAddEffectDefault( CHT_FxType( fx ), this, "RelicWeaponBuff", false );
\t}

\tCHT_GrantSchematics();
}

// Diagrams are taught on every spawn, found by TAG so the mod need not know
// their names (idiom borrowed from the forge, where a size guard misfired).
@addMethod( W3PlayerWitcher ) function CHT_GrantSchematics()
{
\tvar schems : array< name >;
\tvar i : int;

\tif( !CHT_Bool( 'GrantDiagrams', true ) )
\t\treturn;

\tschems = theGame.GetDefinitionsManager().GetItemsWithTag( 'CHT_Schem' );
\tfor( i = 0; i < schems.Size(); i += 1 )
\t\tAddCraftingSchematic( schems[i], true, true );
}

// The laid charm says so in the tooltip, in W3EE's own words and colour.
@wrapMethod( W3TooltipComponent ) function GetBaseItemData( item : SItemUniqueId, itemInvComponent : CInventoryComponent, optional isShopItem : bool, optional compareWithItem : SItemUniqueId, optional compareItemInv : CInventoryComponent ) : CScriptedFlashObject
{
\tvar o : CScriptedFlashObject;
\tvar w : W3PlayerWitcher;
\tvar line, cur : string;
\tvar fx : int;

\to = wrappedMethod( item, itemInvComponent, isShopItem, compareWithItem, compareItemInv );

\t// a STONE tells what its charm does and which blades wear it natively
\tw = GetWitcherPlayer();
\tif( w && itemInvComponent.ItemHasTag( item, 'CHT_Stone' ) )
\t{
\t\tfx = CHT_CardCode( itemInvComponent.GetItemName( item ) );
\t\tif( fx > 0 )
\t\t{
\t\t\tline = w.CHT_StoneLine( fx );
\t\t\tif( line != "" )
\t\t\t{
\t\t\t\tcur = o.GetMemberFlashString( "Description" );
\t\t\t\tif( cur != "" )
\t\t\t\t\tline = line + "<br>" + cur;
\t\t\t\to.SetMemberFlashString( "Description", line );
\t\t\t}
\t\t\treturn o;
\t\t}
\t}

\tfx = itemInvComponent.GetItemModifierInt( item, 'CHT_Fx', 0 );
\tif( fx > 0 && w )
\t{
\t\tline = w.CHT_RedLine( fx );
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

// ------------------------------------------------------- the crafting window ---
//
// The right-hand panel of the crafting window. The LIST on the left keeps the
// plain name ("Charmstone: Gas cloud") - it is built inside PopulateData and
// there is no hook that does not mean copying the whole method. The panel,
// though, asks the menu for a display name and the inventory component for a
// description, and both are wrappable.

// wrappedMethod may appear in the body EXACTLY ONCE. Four calls in four
// branches did not compile: the first mention was accepted and every later one
// was rejected with "Could not find function 'wrappedMethod'". So the original
// is called once at the top and the stored result returned from there on.
@wrapMethod( CR4CraftingMenu ) function GetCurrentDisplayName() : string
{
\tvar w : W3PlayerWitcher;
\tvar dm : CDefinitionsManagerAccessor;
\tvar base, src : string;
\tvar code : int;

\tbase = wrappedMethod();

\tdm = theGame.GetDefinitionsManager();
\tif( !dm.ItemHasTag( selectedSchematic.craftedItemName, 'CHT_Stone' ) )
\t\treturn base;

\tw = GetWitcherPlayer();
\tcode = CHT_CardCode( selectedSchematic.craftedItemName );
\tif( !w || code <= 0 )
\t\treturn base;

\tsrc = w.CHT_SourcesOf( code );
\tif( src == "" )
\t\treturn base;

\treturn base + " - " + src;
}

@wrapMethod( W3GuiPlayerInventoryComponent ) function GetCraftedItemInfo( craftedItemName : name, targetObject : CScriptedFlashObject, optional shouldCompareItems : bool ) : void
{
\tvar w : W3PlayerWitcher;
\tvar line, cur : string;
\tvar code : int;

\twrappedMethod( craftedItemName, targetObject, shouldCompareItems );

\tif( !theGame.GetDefinitionsManager().ItemHasTag( craftedItemName, 'CHT_Stone' ) )
\t\treturn;
\tcode = CHT_CardCode( craftedItemName );
\tw = GetWitcherPlayer();
\tif( !w || code <= 0 )
\t\treturn;

\tline = w.CHT_StoneLine( code );
\tif( line == "" )
\t\treturn;
\tcur = targetObject.GetMemberFlashString( "itemDescription" );
\tif( cur != "" )
\t\tline = line + "<br>" + cur;
\ttargetObject.SetMemberFlashString( "itemDescription", line );
}

// ---------------------------------------------------------------- the dye ---
//
// The stones declare themselves DYES (tag mod_dye) and inherit the game's own
// "use from the bag -> pick a worn item" move for free.
//
// The class is NOT called CR4InventoryMenu here: W3EE ships its own
// inventoryMenu.ws with Quick Slots merged in and renames it. A wrapper refused
// with "must wrap an existing function" usually means the class, not the
// signature (lesson paid for once already in modSetBonusTransfer).

@wrapMethod( %s ) function OnUseDye( item : SItemUniqueId, optional isPreview : bool )
{
\tvar targets : array< int >;
\tvar onSlot : SItemUniqueId;
\tvar w : W3PlayerWitcher;

\tw = GetWitcherPlayer();

\tif( w.inv.ItemHasTag( item, 'CHT_Stone' ) )
\t{
\t\t// weapons only - a charm has nowhere to sit on armour
\t\tif( w.GetItemEquippedOnSlot( EES_SteelSword, onSlot ) )\t\ttargets.PushBack( EES_SteelSword );
\t\tif( w.GetItemEquippedOnSlot( EES_SilverSword, onSlot ) )\ttargets.PushBack( EES_SilverSword );

\t\tif( targets.Size() > 0 )
\t\t\tShowSelectionMode( item, targets );

\t\t// an event answers with a flag even where the declaration shows none
\t\treturn true;
\t}

\treturn wrappedMethod( item, isPreview );
}

@wrapMethod( %s ) function ApplyDye( itemId : SItemUniqueId, targetSlot : int ) : void
{
\tvar w : W3PlayerWitcher;
\tvar target : SItemUniqueId;

\tw = GetWitcherPlayer();

\tif( w.inv.ItemHasTag( itemId, 'CHT_Stone' ) )
\t{
\t\tif( w.GetItemEquippedOnSlot( targetSlot, target ) )
\t\t\tw.CHT_UseStone( itemId, target );

\t\t// the original is deliberately not called: no colouring, nothing spent
\t\treturn;
\t}

\twrappedMethod( itemId, targetSlot );
}

// ---------------------------------------------------------------- console ---

exec function chtinfo()
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar msg : string;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tmsg = "CHT v1<br>";
\tif( w.GetItemEquippedOnSlot( EES_SteelSword, item ) )
\t\tmsg = msg + "steel: card=" + CHT_CardCode( w.inv.GetItemName( item ) )
\t\t\t+ " laid=" + w.inv.GetItemModifierInt( item, 'CHT_Fx', 0 ) + "<br>";
\telse
\t\tmsg = msg + "steel: empty<br>";

\tif( w.GetItemEquippedOnSlot( EES_SilverSword, item ) )
\t\tmsg = msg + "silver: card=" + CHT_CardCode( w.inv.GetItemName( item ) )
\t\t\t+ " laid=" + w.inv.GetItemModifierInt( item, 'CHT_Fx', 0 );
\telse
\t\tmsg = msg + "silver: empty";

\ttheGame.GetGuiManager().ShowNotification( msg, 15000 );
}

exec function chtgive()
{
\tvar w : W3PlayerWitcher;
\tvar i : int;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tw.inv.AddAnItem( 'CHT Empty Charmstone', 3 );
\tw.inv.AddAnItem( 'CHT Cleansing Charmstone', 1 );
\tfor( i = 1; i <= 15; i += 1 )
\t\tw.inv.AddAnItem( CHT_StoneOf( i ), 1 );

\ttheGame.GetGuiManager().ShowNotification( "Charmstones: 3 empty, 1 cleansing, 15 charged", 8000 );
}

// 4 steel | 5 silver - the two slots a charm can live in
exec function chtuse( slot : int, code : int )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar ok : bool;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( slot == 4 )
\t\tok = w.GetItemEquippedOnSlot( EES_SteelSword, item );
\telse
\t\tok = w.GetItemEquippedOnSlot( EES_SilverSword, item );

\tif( !ok )
\t{
\t\ttheGame.GetGuiManager().ShowNotification( "CHT: that slot is empty", 6000 );
\t\treturn;
\t}

\tif( w.CHT_Apply( item, code ) )
\t\ttheGame.GetGuiManager().ShowNotification( "CHT: laid " + code, 6000 );
\telse
\t\ttheGame.GetGuiManager().ShowNotification( "CHT: nothing changed", 6000 );
}

exec function chtclear( slot : int )
{
\tvar w : W3PlayerWitcher;
\tvar item : SItemUniqueId;
\tvar ok : bool;

\tw = GetWitcherPlayer();
\tif( !w ) return;

\tif( slot == 4 )
\t\tok = w.GetItemEquippedOnSlot( EES_SteelSword, item );
\telse
\t\tok = w.GetItemEquippedOnSlot( EES_SilverSword, item );

\tif( ok && w.CHT_Strip( item ) )
\t\ttheGame.GetGuiManager().ShowNotification( "CHT: stripped", 6000 );
\telse
\t\ttheGame.GetGuiManager().ShowNotification( "CHT: nothing to strip", 6000 );
}
""" % (TAGS_SW, TYPE_SW, STONE_SW, CARD_SW, SCHEM_SW, MENU_CLASS, MENU_CLASS)


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
say("  modCharmTransfer — ядро (камни чар)")
say("=" * 66)

if "\\t" in WS:
    raise SystemExit("в коде остались буквальные обратные слэши — не записываю")
for ch in WS:
    if "\u0400" <= ch <= "\u04ff":
        raise SystemExit("в .ws попала кириллица — игра такой файл не съест")

d = os.path.join(MOD, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "CharmTransfer.ws")
data = WS.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
say("   [ok] CharmTransfer.ws  %d Б  UTF-16 LE + BOM  (табуляций: %d)"
    % (len(data), WS.count("\t")))
say("   [ok] класс окна инвентаря: %s" % MENU_CLASS)

if game_running():
    say("   игра запущена — скрипт подхватится при следующем старте")

# ---- регистрация --------------------------------------------------------------
ms = os.path.join(DOCS, "mods.settings")
raw = open(ms, "rb").read().decode("utf-8", "replace")
if not os.path.exists(ms + ".bak_charms"):
    shutil.copyfile(ms, ms + ".bak_charms")
if "[modCharmTransfer]" in raw:
    say("   [--] уже прописан в mods.settings")
else:
    raw = raw.rstrip("\r\n") + "\r\n[modCharmTransfer]\r\nEnabled=1\r\nPriority=%d\r\n" % PRIORITY
    open(ms, "wb").write(raw.encode("utf-8"))
    say("   [ok] прописан в mods.settings, Priority=%d" % PRIORITY)

say()
say("  ЧАРЫ")
for c, tag, _t, ru, _en in CHARMS:
    say("     %2d  %-28s %s" % (c, tag, ru))

say()
say("  ПРОВЕРКА В ИГРЕ")
say("     1. взять в сумку реликтовый меч с чарами и пустой камень чар")
say("     2. у мастера-ремесленника: рецепт «Камень чар: <название>» стал")
say("        доступен -> скрафтить. Меч НЕ расходуется, камень заряжен")
say("     3. надеть другой меч, применить камень (сумка -> использовать ->")
say("        выбрать слот) -> красная строка в подсказке, бафф работает")
say("     4. сейв -> выход -> загрузка -> chtinfo(): laid по-прежнему стоит")
