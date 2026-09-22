# Technical notes — Tier-Scaled Set Bonuses

Written for other Witcher 3 modders. The mod itself is small; what took the work was
learning how to change numbers that sit **in the middle of somebody else's function**
without copying their file. That problem is general, so this document is mostly about the
techniques, and only incidentally about set bonuses.

Everything here was verified against a live Next-Gen 4.0x install with W3EE Redux. Where
something is an assumption, it says so.

---

## 1. The constraint

Script extensions (`@wrapMethod`, `@addMethod`, `@addField`, `@replaceMethod`) let you
change another mod's behaviour without touching its files. That is the whole reason to use
them: a copied file silently loses its changes when the other mod updates, and Script Merger
fights you forever. A wrapper either compiles or fails loudly by name.

But a wrapper sees only three things:

- the **arguments** it was called with,
- the **return value** of the original,
- the **fields of the class** it is attached to.

It cannot reach into the middle of the original and change an expression. And that is
exactly where balance numbers live. A typical target looks like this:

```
if( witcher.IsSetBonusActive(EISB_Bear_2) )
    baseSpeed += poise.GetMissingPoiseWithMult() * 0.002f;
```

`baseSpeed` is a local. There is no argument to adjust and, often, no return value that
carries it. The naive conclusion is "not reachable, must copy the file". That conclusion is
usually wrong.

Of nine such sites in this mod, **eight were reachable** without touching a W3EE file. One
was dropped, and only because it turned out to be dead code.

## 2. Technique 1 — post-correction

**Use when:** the value you need to change is (or reaches) the return value of a wrappable
function.

Do not reimplement the original. Let it run at full strength, then correct the result by the
difference you know.

Worked example — Viper multi-oil potency. Stock:

```
oilPotency *= 0.75f + 0.05f * skill;      // with the set bonus
oilPotency *= 0.50f + 0.05f * skill;      // without it
```

We want `0.50 + 0.25 * power + 0.05 * skill`. `oilPotency` is a local, but its only effect
is to scale two arrays inside the returned struct, linearly. So:

```
ratio = ( 0.50f + 0.25f * power + skill ) / ( 0.50f + 0.25f + skill );
```

and multiply the returned arrays by `ratio`. Arithmetically identical to editing the line.

**Prove linearity before you trust this.** If the original clamps, floors, or feeds the
value back through anything, the delta is not recoverable afterwards. The Netflix adrenaline
site looked like a post-correction candidate and is not: the original clamps at the
adrenaline cap and feeds toxicity back through a gain multiplier. That one needed technique
3 instead.

## 3. Technique 2 — the bracket

**Use when:** the value is not returned, but is *read* through a getter you can also wrap.

Wrap the getter so it scales its result **only while a window is open**, and have the outer
function open the window around its own call to the original.

```
@wrapMethod(W3Effect_Poise) function GetCurrentPoise() : float
{
    var v : float;
    v = wrappedMethod();
    if( witcher && witcher.TSSB_poiseOpen )
        v = v * witcher.TSSB_poiseScale;
    return v;
}

@wrapMethod(W3EECombatHandler) function CounterAndParry( ... )
{
    ...open the bracket...
    wrappedMethod( ... );
    ...close it...
}
```

The original then computes `poise * 0.003 * power` by itself, bit for bit, and you have
duplicated none of its constants. That last part matters more than it sounds: a hardcoded
copy of somebody else's balance number is a silent bug waiting for their next patch.

### ⛔ Two ways the bracket bites

**Nested getters compound.** `GetMissingPoiseWithMult()` internally calls
`GetCurrentPoise()`. Scale both independently and the weakening multiplies by itself —
55% becomes 30%, only on the code paths where one calls the other, which is exactly the kind
of bug that survives testing. The inner wrapper must **close the bracket around its own
call** and re-open it afterwards.

**Zero is a legal value.** The first design used `poiseScale == 0` to mean "bracket closed".
But zero is a perfectly legal strength — it is what a slider dragged to 0% produces. A
player asking for *no bonus* would have silently received the **full grandmaster** bonus.
Use a separate boolean. Never overload a value that lives in the same domain as your data.

## 4. Technique 3 — the flag window

**Use when:** you need to change an *argument* of a call, and the callee is shared.

Wrap the callee to pre-multiply its argument, but only while a flag is set; set the flag in a
wrapper around the specific caller you care about.

```
@wrapMethod(W3SignEntity) function ManagePlayerStamina()
{
    witcher.TSSB_signAdr = true;
    wrappedMethod();
    witcher.TSSB_signAdr = false;
}

@wrapMethod(W3Effect_CombatAdrenaline) function AddAdrenalineWithMult( value : float )
{
    if( witcher && witcher.TSSB_signAdr && witcher.IsSetBonusActive(EISB_Netflix_2) )
        value = value * witcher.TSSB_Power();
    wrappedMethod( value );
}
```

**Before you do this, enumerate every other caller of the callee.** `AddAdrenalineWithMult`
has four; three are unreachable from inside the window. That has to be verified, not assumed
— and it is worth adding a second guard (here, the set bonus check) so the wrapper stays
correct if the other mod grows a fifth caller.

### The discriminator variant

Sometimes the callee itself tells you which caller it is serving. `CNewNPC.CatReduceDamage`
is called three times in W3EE: once by the Lynx set bonus with `0.95`, twice by arm injuries
with `0.9`. Discriminating on the argument value is enough, and it fixes both patched lines
from a single wrapper.

## 5. Where to keep state

All of it goes on `W3PlayerWitcher` via `@addField`, and wrappers on other classes reach it
through `@addMethod` accessors on the same class.

Two facts settled this:

- `@addField(W3PlayerWitcher)` had working precedent in an earlier mod of ours.
- Adding fields to a **W3EE-declared** class had no precedent anywhere.

Given the choice between a proven and an unproven mechanism, take the proven one even if it
costs an indirection.

**Nothing is declared `saved`.** The player entity is rebuilt on every load, so caches come
back invalid by themselves and re-read from the world. A save made with the mod is identical
to one made without it, which is what makes the mod safe to remove mid-playthrough.

### Cross-class access to added members

The official CDPR documentation does not state whether a member added to class A is
reachable from a wrapper on class B. A scan of 2143 `.ws` files in a heavily modded install
found **zero precedents** — which is a statement about that install, not about the language.

The documentation does show `@addMethod(CPlayer) public function ...`, and the WitcherScript
IDE documents added members as ordinary symbols that can collide by name with members from
dependencies. Both imply ordinary member visibility. Declaring everything `public` and
compiling confirmed it.

**It works.** Declare added fields and methods `public` and call them from anywhere.

## 6. Traps

Each of these cost real time. Several were found by adversarial review before ever launching
the game, which is the cheapest place to find them.

1. **`MinI` does not exist.** It is `Min`. Verify every function name against `math.ws` and
   `string.ws` before shipping. A single unknown identifier fails the whole script set and
   the game will not start at all — taking every other mod down with it.
2. **There are no file-scope constants.** `@addField` is the only context where a global
   variable declaration is valid. Inline the literals with a comment naming the source line.
3. **Not everything that looks like a method is one.** `AddCharacterStat` in
   `CharacterStatsPopup.ws` is a file-scope global function; there is no class to attach a
   wrapper to. Check the declaration, not the call site.
4. **Slider `displayType` takes divisions, not positions.** `SLIDER;0;100;100`, not `;101`.
   With 101 the slider steps by 0.99 and the value 40 is unreachable — the preset writes 40,
   the widget jumps to 39.6 the moment it is touched, and `StringToInt` truncates to 39.
5. **A cache must not memorise a guess.** The tier cache originally stored "grandmaster"
   when it found no set pieces and marked itself valid. An empty or briefly unreadable
   inventory would freeze the mod at full strength for the session — the exact inverse of
   the feature. Return the fallback, do not cache it.
6. **One-shot initialisers.** The adrenaline cap is computed once when the combat effect
   starts, not per use. Wrapping the getter is not enough; something has to force a
   recompute when gear changes. Look for the funnel the other mod already uses for equip
   changes — there usually is one.
7. **The options menu shows only 10 entries per page** (9 + Back). The eleventh and beyond
   simply do not appear: no error, no scrollbar, nothing in the log. Six mods each claiming
   a top-level entry pushed two others off the screen. Nest everything under one shared node
   by adding a level to the `displayName` path, and have **every** mod declare the shared
   root key with its own id, so a solo install still shows a named folder.
8. **`.w3strings` id-spaces collide silently.** 4476 was already taken by another installed
   mod. Symptom: labels vanish, and a section whose title will not render may not appear at
   all. Decode the `en.w3strings` of every installed mod and collect the used ranges before
   picking yours.
9. **Loc keys are often defined two or three times** across mods, with different parameter
   counts. Your parameter counts may line up only because of `mods.settings` load order. If
   the order flips, a rewritten description pushes numbers into the wrong placeholders — a
   worse lie than not rewriting at all. Document the dependency in a comment next to the
   switch.
10. **`!` before a cast does not parse.** `if( !(SomeClass)x )` is a syntax error. Assign to
    a local first.
11. **`wrappedMethod()` may appear only once textually per wrapper.** The limit is on call
    sites in the source, not on execution paths — a single call inside an `if` compiles, and
    early returns that never reach it are fine. That is what lets a wrapper fully replace
    behaviour in chosen cases while leaving it alone in all others.

## 7. How the mod actually got built

Worth recording because the order of operations mattered more than the code.

**It started as a fork.** Twenty-one edits made directly inside six W3EE files, plus its
menu. It worked, and it was undeployable: it could not be published, it could not be
uninstalled, and any W3EE update or a Script Merger run would quietly delete it.

**The port was assessed site by site before a line was written.** Nine call sites, each
examined for what its enclosing function was, whether the affected value reached a return,
and how long the function was. Verdicts were allowed to be "dead end" — that honesty is what
kept the design from containing fiction.

**Every signature and every identifier was verified against the game files before writing
code.** Fourteen wrapped methods, twenty-four helper functions and fields. This caught the
nonexistent `MinI` and the not-a-method `AddCharacterStat` at zero cost. The rule that makes
this cheap: *count the live call sites of the exact form you are about to write. Zero
occurrences means that form does not exist.*

**The old edits were reverted in the same operation as the install.** If both the in-file
patch and the mod are live, the scaling applies twice. The revert was written as a targeted
reverse-replacement driven by the stored before/after pairs, not a whole-file restore from
backup, so that unrelated edits in the same files survived. Dry run first: 21 of 21 reverted
cleanly, zero drift.

**Then the descriptions were audited, one family at a time.** This is the part that found
the real bugs, and all three were bugs the author could not have found by playing:

- The rewritten description used the strength of the **worn** gear, but the game builds that
  text for **any** item the cursor touches. Hovering a grandmaster piece in a shop showed
  tier-1 numbers.
- The "tier-scaled strength" line was appended to every rewritten description, but only two
  of six are fully scaled. On Netflix it sat above a promise of +50% potions and +100%
  decoctions that arrive at full strength regardless.
- Manticore was **unlocked but never scaled** — a tier-1 set received the entire grandmaster
  bonus at 100% while every other family sat at 40%.

None of these are compile errors and none of them look wrong in a five-minute playtest.

## 8. Verifying without launching the game

Launching is expensive: a bad identifier means a wall of red text and a restart. Almost
everything can be checked from outside.

- **Identifiers.** Grep every function you call against the game's scripts. Zero hits means
  it does not exist.
- **Signatures.** Grep the declaration of every method you wrap and compare character for
  character, parameter names included.
- **Callers.** For any callee-wrapping or bracket technique, list every caller of the target
  and confirm each one is either intended or excluded by a guard.
- **Name collisions.** Scan the whole compile set for your prefix. Ours appears nowhere
  else across 3629 files.
- **Encoding.** `.ws` is UTF-16 LE with BOM; menu XML is UTF-8 **without** BOM despite
  declaring UTF-16 in its prolog; the two filelists are UTF-16 LE and saving them as UTF-8
  breaks the menus of every installed mod.

## 9. Known open problems

Stated plainly rather than hidden, because a modder reading this may want to solve them.

- **The character screen still shows unscaled numbers in two places.** The Yrden panel
  reports the grandmaster time-slow, and the Bear poise chip-resistance row reads the poise
  getter outside any bracket. Both live in W3EE files this mod does not touch; fixing them
  means wrapping the enclosing UI builders and rewriting finished strings.
- **The Wolf bleed-resistance shred is not scaled.** It could be, but the same value is
  subtracted when a stack lands and added back when it is removed. If the strength changes
  between those two moments — because the player swapped gear — the enemy keeps a permanent
  debuff. Solving it properly means storing the factor that was actually applied.
- **The Gryphon description promises two effects that do not exist** at any tier, in stock
  W3EE. Fixing it means editing W3EE's own strings, which is outside what an add-on should
  do.
