# -*- coding: utf-8 -*-
"""Пакует modAardShatter в устанавливаемый архив."""
import zipfile, os

G = r"F:\SteamLibrary\steamapps\common\The Witcher 3"
MOD = os.path.join(G, "mods", "modAardShatter")
CFG = os.path.join(G, "bin", "config", "r4game", "user_config_matrix", "pc")
OUT = r"C:\Users\New\Downloads\modAardShatter v1.2.zip"

README = r"""AardShatter v1.2 - an add-on for W3EE Redux
===========================================

Signs tear enemies apart instead of merely knocking them down, swords stop
being blocked by armour, and finishers become varied again.

WHAT IT DOES

  Aard / Igni shatter
    * The NEXT sign hit on an already poise-broken human may tear it apart;
      on a miss the normal knockdown happens. The chance scales with
      MISSING health: 70% health left = 30% chance, 30% left = 70% chance.
      A curve slider bends that relation, a ceiling slider can forbid it
      above a chosen health percent.
    * Anything a sign delivers the KILLING BLOW to is torn apart - guaranteed,
      no roll involved.
    * Huge enemies (griffins, trolls, golems, leshens) and bosses never are.
    * Creatures without gore models fall back to a plain cut instead of
      dying intact.
    * Optional slow motion, with its own chance, strength and duration.

  Sword dismemberment for everyone
    W3EE refuses dismemberment for several reasons that all sit above the
    sign branch: heavy armour, a battle mace in hand, wooden weapons, arrows.
    From outside there is no way to tell which one fired, so this simply
    overrides any refusal on a normal human. Huge enemies, bosses and
    quest-protected NPCs stay protected. A wrapper can only turn false into
    true, so the result is never worse than stock behaviour.

  Finisher variety
    W3EE replaced the vanilla random finisher pool with a direction-based
    one, which collapses to a single animation while standing still - the
    same chest stab over and over. This restores the vanilla pool plus every
    DLC finisher, chosen at random again.

  Bug fix
    W3EE raises an internal Igni-explosion flag and never lowers it, so a
    single Eruption glyphword disables ALL finishers until the game is
    restarted. This clears the flag on every non-Igni hit.

REQUIREMENTS
  W3EE Redux. Without it the game will NOT start (unknown class
  W3EECombatHandler). This mod wraps W3EE methods via script extensions -
  it does not replace or copy any of its files, so a W3EE update cannot be
  silently reverted by it.

INSTALL
  1. Copy  modAardShatter  into  <game>/mods/
  2. Copy  AardShatter.xml  into
     <game>/bin/config/r4game/user_config_matrix/pc/
  3. Append a line  AardShatter.xml;  to BOTH dx12filelist.txt and
     dx11filelist.txt in that same folder.
     THOSE TWO FILES ARE UTF-16 LE. Saving them as UTF-8 breaks every mod menu.
  4. Settings: Options -> Mods -> Aard Shatter. Press the preset button once
     so the values are written.

UNINSTALL
  Rename the folder to ~modAardShatter, or delete it, and remove the
  AardShatter.xml line from both filelists.

LANGUAGES
  Menu labels ship as ru and en w3strings, id-space 4471.
"""

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _dirs, files in os.walk(MOD):
        for fn in files:
            p = os.path.join(base, fn)
            rel = os.path.join("modAardShatter", os.path.relpath(p, MOD))
            z.write(p, rel)
    z.write(os.path.join(CFG, "AardShatter.xml"),
            os.path.join("bin", "config", "r4game", "user_config_matrix", "pc",
                         "AardShatter.xml"))
    z.writestr("README.txt", README.replace("\n", "\r\n"))

print("архив :", OUT)
print("размер:", os.path.getsize(OUT), "байт")
with zipfile.ZipFile(OUT) as z:
    for n in z.namelist():
        print("   ", n)
