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
\t}
\treturn '';
}

// Codes are OUR numbering, not the game's. EItemSetType is numbered differently in
// vanilla (9 values) and in W3EE Redux (30 values, with minor tiers and armour
// weights), so a raw number would silently mean a different set in each. Only these
// eight names exist in both, so only these are offered.
@addMethod( W3PlayerWitcher ) function SBT_TypeForCode( code : int ) : EItemSetType
{
\tswitch( code )
\t{
\t\tcase 1:\treturn EIST_Lynx;
\t\tcase 2:\treturn EIST_Gryphon;
\t\tcase 3:\treturn EIST_Bear;
\t\tcase 4:\treturn EIST_Wolf;
\t\tcase 5:\treturn EIST_RedWolf;
\t\tcase 6:\treturn EIST_Vampire;
\t\tcase 7:\treturn EIST_Viper;
\t\tcase 8:\treturn EIST_Netflix;
\t}
\treturn EIST_Undefined;
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

\tcode = inv.GetItemModifierInt( item, 'SBT_Set', 0 );
\tif( code > 0 )
\t\treturn SBT_TypeForCode( code );

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

\tif( SBT_TypeForCode( code ) == EIST_Undefined )
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

\t// Let the game add or drop the actual buffs for every set we could have touched.
\tManageActiveSetBonuses( EIST_Lynx );
\tManageActiveSetBonuses( EIST_Gryphon );
\tManageActiveSetBonuses( EIST_Bear );
\tManageActiveSetBonuses( EIST_Wolf );
\tManageActiveSetBonuses( EIST_RedWolf );
\tManageActiveSetBonuses( EIST_Vampire );
\tManageActiveSetBonuses( EIST_Viper );
\tManageActiveSetBonuses( EIST_Netflix );

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

@addMethod( W3PlayerWitcher ) function SBT_HasFullSet( code : int ) : bool
{
\tvar items : array< SItemUniqueId >;
\tvar slots : array< EEquipmentSlots >;
\tvar item : SItemUniqueId;
\tvar tag, cat : name;
\tvar i : int;
\tvar hasArmor, hasBoots, hasGloves, hasPants, hasSteel, hasSilver : bool;

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

\t\tif( cat == 'armor' )\t\thasArmor = true;
\t\tif( cat == 'boots' )\t\thasBoots = true;
\t\tif( cat == 'gloves' )\t\thasGloves = true;
\t\tif( cat == 'pants' )\t\thasPants = true;
\t\tif( cat == 'steelsword' )\thasSteel = true;
\t\tif( cat == 'silversword' )\thasSilver = true;
\t}

\treturn hasArmor && hasBoots && hasGloves && hasPants && hasSteel && hasSilver;
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
\t\tw = GetWitcherPlayer();
\t\tif( !w.SBT_HasFullSet( code ) )
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
\tif( !SBT_Bool( 'GrantSchematics', true ) )
\t\treturn;

\tif( FactsQuerySum( 'SBT_Schematics' ) > 0 )
\t\treturn;

\tAddCraftingSchematic( 'SBT Runestone Feline schematic',    true, true );
\tAddCraftingSchematic( 'SBT Runestone Griffin schematic',   true, true );
\tAddCraftingSchematic( 'SBT Runestone Ursine schematic',    true, true );
\tAddCraftingSchematic( 'SBT Runestone Wolven schematic',    true, true );
\tAddCraftingSchematic( 'SBT Runestone Manticore schematic', true, true );
\tAddCraftingSchematic( 'SBT Runestone Vampire schematic',   true, true );
\tAddCraftingSchematic( 'SBT Runestone Viper schematic',     true, true );
\tAddCraftingSchematic( 'SBT Runestone Netflix schematic',   true, true );
\tAddCraftingSchematic( 'SBT Empty Runestone schematic',     true, true );

\tFactsSet( 'SBT_Schematics', 1 );
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

\treturn 0;
}

@addMethod( W3PlayerWitcher ) function SBT_UseStone( stone : SItemUniqueId, target : SItemUniqueId )
{
\tvar code : int;

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

@wrapMethod( WmkCR4InventoryMenu ) function OnUseDye( item : SItemUniqueId, optional isPreview : bool )
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

@wrapMethod( WmkCR4InventoryMenu ) function ApplyDye( itemId : SItemUniqueId, targetSlot : int ) : void
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

d = os.path.join(MOD, "content", "scripts", "local")
os.makedirs(d, exist_ok=True)
p = os.path.join(d, "SetBonusTransfer.ws")
data = WS.replace("\n", "\r\n").encode("utf-16")
open(p, "wb").write(data)
say("   [ok] SetBonusTransfer.ws  %d Б  UTF-16 LE + BOM  (табуляций: %d)"
    % (len(data), WS.count("\t")))

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
