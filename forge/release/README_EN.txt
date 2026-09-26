Path of the Blade 1.0 - a forge for W3EE Redux
============================================================

WHAT IT IS
  A sword built to your own taste. Love how one blade looks but want the
  damage of another? The forge takes the look from the first, the damage from
  the second and the properties from a third, then forges a relic-quality
  sword from a blank. After that you can give it a charm and a name.

  Armour works the same way: a chest piece, trousers, gloves or boots can
  look like one item and protect like another.

  Everything you take apart or study stays with you as knowledge tokens.
  Tokens are never used up, so you can rebuild as often as you like. A token
  is lost only if you sell it or drop it.

HOW IT WORKS
  You fill a recipe's squares the same way as W3EE ingredients: scroll the
  square (mouse wheel) or press R and pick from the list.

  1. Learn an item. There are three ways to do it.
     - Dismantle it at a blacksmith or armorer. The item is destroyed, W3EE
       gives its usual materials and the forge gives you tokens.
     - Study it with "Study a weapon" (or "Study an armor", "Study trousers",
       "Study gloves", "Study boots"). This is free, you keep the item, and
       you don't have to take it off.
     - Use "Take a pattern". You get the looks of the swords, chest piece,
       trousers, gloves and boots you're wearing, and the items stay intact.
       It costs linen, leather straps and a fee. If you already know every
       worn look, nothing is spent.
     An item can give you tokens for its look, its damage (swords), its
     protection (armour), its properties (two at most from a weapon, one
     from an armour piece) and its charm. Properties come only from bonuses
     fixed on the item itself: witcher school gear, relics, unique items and
     some craftable items. The random bonuses Redux adds to ordinary items
     can't be taken. You never get the same token twice.
     If you dismantle an upgraded crafted item (a witcher set tier, for
     example), you get its previous tier back whole, and the parts list shows
     this before you confirm. A forged item dismantles back into its blank.

  2. Forge a blank from ordinary materials. The blacksmith makes the steel
     and silver blade blanks, the armorer makes the chest, trousers, gloves
     and boots blanks.

  3. Forge a blade ("Forged blade"). You need a blank, a shape token (the look
     of any sword) and a damage token (the damage of any sword, the same one
     or another). The fourth square, the flaw, can stay empty.
     The blank decides the metal, so a steel blade can look like a silver
     sword and the other way round. It still hangs on its own side of your
     back, in a matching scabbard. The blade comes out at relic quality right
     away, with no upgrade tiers: the donor's damage, 2 property slots and up
     to 3 rune sockets. It takes its name from the sword whose look it wears.
     Only the blank and the smith's fee are spent. Before you forge, the
     "- The build -" summary on the right shows what you'll get.
     A heavy flaw is a pure drawback, but it buys the blade a third property
     slot. A light flaw buys no slot; it is just a drawback. A blade can have
     only one flaw, and it can only be added at forging. The forge gives you
     the flaw marks for free.

  4. Forge armour ("Forged armor", "Forged trousers", "Forged gauntlets",
     "Forged boots"). You need a blank, a look for the same body part and a
     protection token, which carries the donor's armour value, resistances
     and weight class as one piece. In the fourth square you can add a unique
     armour bonus taken from the same body part and matching the weight class.

  5. Finish the blade. The blade you are wearing comes first in its square.
     - "Blade properties" builds the property set from your tokens, from
       scratch every time. Leaving a square empty removes that property. The
       window only offers what will fit: one property per stat, no
       duplicates, and no stat total above the most generous item in Redux.
     - "Blade enchanting" adds one of 15 relic effects (the red line) learned
       from relic swords. A new charm replaces the old one.
     - "Blade naming" gives the blade a two-word name such as "Fang of the
       Striga" or "Dawn of Toussaint". There are 256 combinations, and you
       can rename it at any time.

WHERE
  You don't need to find or buy any recipes: the forge learns them itself
  every time you load.
  Any blacksmith, group "The Blade's Path: Blades": blade blanks, "Forged
    blade", "Study a weapon", "Take a pattern", "Blade properties", "Blade
    enchanting", "Blade naming".
  Any armorer, group "The Blade's Path: Armour": armour blanks, forging
    chest pieces, trousers, gauntlets and boots, and the "Study ..." recipes
    for each of them.
  Dismantling: the regular dismantle tab at any blacksmith or armorer.
  Shops that sell shape tokens (base price 25 plus the merchant's markup):
    Elihal in Novigrad sells armour looks;
    Lafargue, the grandmaster smith in Toussaint, sells sword and armour
    looks.
    Looks you already know are hidden from the shelf. Damage, protection,
    properties and charms are never sold: you only get them by studying or
    dismantling.
    Armour looks from other mods (Raven Armor Set, Frayed Armor V2, Vagabond
    Armor) are put on the shelf only if that mod is installed.

REQUIREMENTS
  - The Witcher 3 Next-Gen 4.0 or newer (the author plays on 4.04c). Classic
    1.32 will not work.
  - W3EE Redux (the author plays on 1.47). The script won't compile without
    it.
  - Both expansions: Hearts of Stone and Blood and Wine.
  - No Script Merger needed: the mod doesn't replace any game or W3EE script.

INSTALLATION
  1. Put the mods and dlc folders from the archive into the game root
     (...\The Witcher 3\, where bin, content, dlc and mods live), merging with
     the existing ones.
  2. That's it. There is no settings menu, and you don't need to touch the
     filelists or mods.settings.
  3. Load a save and open crafting at a blacksmith or armorer: the recipes
     are already there. Flaw marks and naming words will appear in your
     bag.

  If the recipes are missing, open Documents\The Witcher 3\user.settings and
  dx12user.settings. The [DLC] section should contain
      DlcEnabled_frgblankitems=1
  If it says 0, change it to 1 in both files. Normally the game adds this
  line by itself.

  When updating, replace both folders together. If the item package is older
  than the script, studying and dismantling for tokens are paused and the
  game shows a message about it: close the game and copy both folders from
  the same archive again.

UNINSTALLING
  Uninstalling hasn't been tested in game yet, so make a separate save first.
  1. Unequip your forged gear.
  2. Delete both folders: mods\modForgeLab and dlc\dlcFRGBlanks. You can also
     remove the DlcEnabled_frgblankitems line from [DLC].
  The mod's items exist only in its own package, so without it the blanks,
  forged blades and armour, all tokens, marks and words will disappear.
  Dismantled items don't come back, just like with normal dismantling. The
  forge never alters regular items, and studying only reads them, so those
  stay as they were. The learned recipes and the mod's markers stay in your
  save; how the game treats them without the mod hasn't been tested yet.

KNOWN LIMITATIONS
  - Most of the forge's pop-up messages (forging results, refusals after you
    press the craft button, "Forge: new knowledge") are in English only. The
    hints shown while you pick a token, the "- The build -" summary, recipe
    and item names and descriptions exist in English and Russian; all other
    languages get English.
  - If the recipe squares don't scroll although the wheel and R hint is
    shown, your Documents\The Witcher 3\input.settings lacks W3EE's menu
    bindings (the [EMPTY_CONTEXT] section, actions IngredientShift and
    IngredientSelect). Copy them from the input.settings in the Redux
    archive.
  - Only Lafargue sells sword looks, and his shop opens only after the Blood
    and Wine quest in which you find him. Until then you get sword looks by
    dismantling, studying or taking a pattern.
  - A weapon gives at most two property tokens, an armour piece one. A blade
    holds 2 properties; only a heavy flaw gives a third, and a flaw can only
    be added at forging.
  - A forged item's look, like an armour piece's unique bonus, is chosen
    only when you forge it. To change it, forge the item again; the old one
    dismantles back into its blank.
  - Charms only go on forged steel and silver swords and only work while the
    sword is drawn. The Dark Curse, while its sword is drawn, drains 1% of
    your health every second once you go 5 seconds without landing a hit,
    in combat or not, and it can kill you. In exchange the blade gets +10%
    vampirism.
  - The forge can't study the heavy two-handed W3EE axes, hammers and maces,
    and dismantling them gives no tokens.
  - The forge only sees what is in Geralt's bag or on Geralt, not the stash
    or the saddlebags. A token is an ordinary item: sell it or drop it and
    the knowledge is gone. Studying or dismantling the same item again gives
    any token back. A look sold by Elihal or Lafargue can also be bought
    again (if it is no longer on the shelf, stand next to the merchant and
    type frgstock(1)). A property comes back on load if the damage or
    protection token from the same item is still in your bag.
  - If you have two identical forged blades (same look and metal), the window
    shows them as one, and properties, charms and names go to the one you
    are wearing. To work on the other one, equip it first.
  - Forged swords make no hit sound on strong attacks. Fast attacks have
    their sound.
  - Forged armour may come out with no glyph sockets, even though the message
    says "3 rune sockets".
  - Some swords in the game are built on a model of the other metal (for
    example the "silver" gnomish and dwarven W3EE swords, some Blood and
    Wine school swords, Ciri's sword) and have no scabbard even without this
    mod. For their forged copies, as for blades of the "other" metal, the
    forge uses a model of the right metal so the scabbard shows, but this
    hasn't been checked in game on every sword.
  - Recipe prices are base prices: blank and forging 50, properties 20, charm
    30, naming 10, pattern 50, studying free. W3EE multiplies them by its
    crafting price setting and the regional multiplier.

CONSOLE (OPTIONAL)
  frgwhy()             shows why the window refused your last recipe
  frgstock()           stand next to Lafargue or Elihal: lays out the shape
                       tokens if that shop hasn't been stocked yet (opening
                       the shop does the same); frgstock(1) puts back every
                       look missing from the shelf
  frgrelic()           shows how many blade properties you have studied, with
                       up to 8 examples (internal item names) of items to get
                       the rest from
  frgname(4, "Name")   gives your equipped forged steel sword a name of your
                       own (5 for the silver one). English letters, digits,
                       spaces and punctuation only, 2 to 28 characters; the
                       name is lost in NG+. frgname0(4) gives the blade back
                       its original name.
