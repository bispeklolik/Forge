# W3EE Redux — Tier-Scaled Set Bonuses

**The grandmaster half of every armour set, available from the first tier — just weaker.**

An add-on for [W3EE Redux](https://www.nexusmods.com/witcher3/mods/3559). Touches no W3EE file.

---

## The problem

W3EE gives every witcher set two bonuses, and locks the second one — the "grandmaster
bonus" — behind a full grandmaster set.

Until then, half of what the set advertises does nothing at all. A tier-1 Ursine set is not
a weaker Ursine set; it is an Ursine set with one of its two defining mechanics simply
absent. Every tier below grandmaster reads as filler you wear on the way to the real thing.

## What this does

Unlocks the second bonus on **every** tier, scaled down by the average tier of the pieces
you are wearing:

| Average tier | Strength |
|---|---|
| 1 | 40% |
| 2 | 55% |
| 3 | 70% |
| 4 | 85% |
| grandmaster | 100% |

All four percentages are sliders. Grandmaster is deliberately **not** a slider — a complete
set always behaves exactly like unmodded W3EE, so nothing you already built changes.

**The added part of a bonus is scaled, never the total.** The Wolf adrenaline cap is
`100 + 50 × strength`, so it reads 120 at tier 1 and 150 at grandmaster — not 60. This
matters: scaling the total would make low tiers actively worse than no set at all.

Switch the mod off and the second bonus goes back to grandmaster-only, which is stock
behaviour.

## Honest tooltips

This is half the point of the mod.

W3EE builds its set bonus descriptions in code and pushes fixed numbers into them. Those
numbers know nothing about any scaling — so with any tier-scaling mod installed, a tooltip
promises 150 adrenaline while the game gives you 120. You end up doing arithmetic to find
out what you are actually wearing.

This rewrites the affected descriptions with the real values, and optionally shows the
grandmaster figure in brackets:

> Maximum Adrenaline is increased to **120 (150)**.

So you can see what finishing the set would buy you, without a calculator.

Three rules the rewrite follows:

- **Only numbers this mod actually scales are rewritten.** Everything else is passed
  through exactly as W3EE wrote it. Lying in the other direction would be no better.
- **Only for a set you are wearing.** The game builds this text for any item the cursor
  touches — shops, stashes, chests, the crafting preview for something you do not own. The
  strength comes from your equipped gear, not from the item under the cursor, so rewriting
  there would promise your tier-1 numbers for a grandmaster piece in a shop.
- **The "tier-scaled strength" line appears only where the whole sentence is scaled** —
  Lynx and Bear. The other four descriptions mix scaled and untouched clauses, and a single
  percentage under the paragraph would be read as applying to all of them.

## What is scaled, family by family

| Set | Scaled | Left at full strength |
|---|---|---|
| **Lynx** | the enemy speed and damage debuff | — |
| **Bear** | chip damage reduction, attack speed, poise damage, enemy armour piercing | the poise-regeneration lockout (a yes/no rule, not a number) |
| **Wolf** | maximum adrenaline | bleed-resistance shred |
| **Gryphon** | extra Yrden time slow | — |
| **Viper** | multi-oil potency | crit transfusion per oil, the extra oil slot |
| **Netflix** | adrenaline per sign cast | potion and decoction effects |
| **Manticore** | *nothing — see below* | |

**Manticore / Red Wolf is deliberately excluded.** Its second bonus is toxicity-based, and
none of it can be scaled from script: part of it does not change a number at all, it changes
the *shape* of the formula (percentages become absolute values). Unlocking it early would
hand a tier-1 set the entire grandmaster bonus at full strength while every other family sat
at 40%. It stays grandmaster-only, exactly as in stock W3EE.

### Why some things cannot be scaled

Several magnitudes live in item and ability XML rather than in script, and script extensions
cannot reach them:

- **Netflix** potion and decoction effects — an ability swap, not a number.
- **Viper** extra oil slot — an integer +1, with no middle value.
- **Viper** crit transfusion — one of eight additive terms feeding a local variable inside a
  larger routine; no clean interception point.
- **Bear** poise-regeneration lockout — a boolean gate, not a magnitude.

These arrive at full strength the moment the bonus unlocks. The mod does not pretend
otherwise, which is why the strength line is suppressed for those families.

### One thing you should know about Gryphon

Two thirds of the Gryphon second-bonus description — "+20% Vigor regeneration" and "+20%
Intensity for other Signs" — describe nothing that runs, at any tier. No producing code
exists anywhere in the game or in W3EE. That is a pre-existing W3EE text defect, not
something this mod introduces, and this mod passes those numbers through untouched rather
than inventing scaled versions of effects that do not exist.

## Settings

`Options → Mods → W3EE → Addons → W3EE Redux Add-ons → Tier-Scaled Set Bonuses`

| Setting | Default | What it does |
|---|---|---|
| Grandmaster bonus on every tier | on | Off = stock W3EE behaviour |
| Strength at tier 1–4 | 40 / 55 / 70 / 85 | The four sliders |
| Tooltips: grandmaster value in brackets | on | `120 (150)` versus `120` |
| Tooltips: add a strength line | on | Only ever shown for Lynx and Bear |

## Compatibility

No file of W3EE, of the game, or of any other mod is replaced. Everything runs through
`@wrapMethod`, and wrappers from different mods chain by design — Script Merger has nothing
to merge here. Safe to add or remove mid-playthrough.

**Nothing is written to your save.** No `saved` fields, no facts, no item tags. Removing the
mod leaves no residue.

Known interaction worth checking: **Set Bonus Transfer** also works on set bonuses. The two
have not been tested together.

## Requirements

W3EE Redux. This is an add-on, not a standalone mod — without W3EE the game refuses to start
and the error names this mod's file. That refusal is deliberate.

Tested on The Witcher 3 Next-Gen (4.0x) on DX12. Not tested on Classic 1.32.

## Install

1. Drop the `mods` and `bin` folders into your game folder — the one that already contains
   `bin`, `content` and `mods`.
2. Register the settings page: add `W3EERedux_TierBonuses.xml;` to **both**
   `dx12filelist.txt` and `dx11filelist.txt` in
   `bin\config\r4game\user_config_matrix\pc\`. Menu Filelist Updater
   ([Nexus 7171](https://www.nexusmods.com/witcher3/mods/7171)) does this for every installed
   mod in one run. Without the line the mod still works, but its options page never appears
   and every setting stays at its default.

   Editing by hand: those two files are UTF-16 LE. Saving them as UTF-8 breaks the menus of
   every installed mod, not just this one.

## Uninstall

Delete `mods\modW3EERedux_TierBonuses` and remove the xml line from both filelists.

## Credits

Built on top of W3EE Redux — every set bonus this hooks into belongs to its authors. This
add-on ships none of their files and modifies none of them; it only wraps their methods at
load time.

Technical documentation, including the interception techniques used and the traps found
along the way, is in `TECHNICAL.md`.
