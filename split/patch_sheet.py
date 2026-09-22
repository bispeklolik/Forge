# -*- coding: utf-8 -*-
"""
Добавляет честную мощь знаков в окне характеристик.

GetTotalSpellPower(displayOnly) применяет затухание ТОЛЬКО когда displayOnly
равно false (playerWitcher.ws:10641). Окно характеристик зовёт его с true
(CharacterStatsPopup.ws:459) и потому печатает сырое число до затухания.

Живой вызов этой функции во всей сборке ровно ОДИН — то самое окно. Остальные
два закомментированы. Значит обёртка не может задеть бой ни при каких условиях.
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src", "Mutations.ws")
SPEC = os.path.join(HERE, "spec.py")

WRAPPER = '''

// ---------------------------------------------------------------------------
// The character sheet's "Sign Intensity" line
//
// GetTotalSpellPower applies the compression only when displayOnly is FALSE
// (playerWitcher.ws:10641). The character sheet calls it with TRUE
// (CharacterStatsPopup.ws:459), so the number on screen is the raw total from
// before the curve - 180% on screen is 144% in combat.
//
// That one call is the ONLY live caller of this function in the whole compile
// set; the other two are commented out. So correcting it here cannot touch
// combat, only the number the player reads.
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function GetTotalSpellPower( optional displayOnly : bool ) : SAbilityAttributeValue
{
	var sp      : SAbilityAttributeValue;
	var bypass  : float;
	var without : float;

	sp = wrappedMethod( displayOnly );

	if( !displayOnly )
		return sp;

	if( !MUTF_Bool('Enabled', true) || !MUTF_Bool('SheetHonest', true) )
		return sp;

	without = sp.valueMultiplicative;
	sp.valueMultiplicative = MUTF_Compress( sp.valueMultiplicative );

	// If the player raised the bypass, combat delivers more than the plain
	// curve would, and the sheet has to say so too.
	bypass = MUTF_SignBypass();
	if( bypass > 0.f && IsMutationActive( EPMT_Mutation1 ) )
	{
		without = MUTF_Compress( MaxF( 0.f, without - 0.5f ) );
		if( without * 1.5f > sp.valueMultiplicative )
			sp.valueMultiplicative = sp.valueMultiplicative + bypass * ( without * 1.5f - sp.valueMultiplicative );
	}

	return sp;
}
'''

SETTING_OLD = '''            ("SignBypass",   "mutf_signbypass","SLIDER;0;100;100", "0"),'''
SETTING_NEW = '''            ("SignBypass",   "mutf_signbypass","SLIDER;0;100;100", "0"),
            ("SheetHonest",  "mutf_sheet",     "TOGGLE",           "true"),'''

LOCS = ["en", "ru", "pl", "de", "fr", "es", "esmx", "it",
        "br", "cz", "hu", "tr", "jp", "kr", "cn", "zh", "ar"]

SHEET = [
 "Character sheet: show Sign Intensity after falloff",
 "Окно персонажа: показывать мощь знаков с учётом затухания",
 "Karta postaci: pokaż Moc Znaków po osłabieniu",
 "Charakterbogen: Zeichenintensität nach Abschwächung zeigen",
 "Fiche de personnage : afficher l'Intensité des Signes après atténuation",
 "Hoja de personaje: mostrar la Intensidad de Signos tras el decaimiento",
 "Hoja de personaje: mostrar la Intensidad de Signos tras el decaimiento",
 "Scheda personaggio: mostra l'Intensità dei Segni dopo l'attenuazione",
 "Ficha do personagem: mostrar Intensidade de Sinais após a queda",
 "Karta postavy: zobrazit Sílu Znamení po útlumu",
 "Karakterlap: a jelerő mutatása a csökkenés után",
 "Karakter sayfası: İşaret Gücünü azalma sonrası göster",
 "キャラクター画面: 減衰後の印の強さを表示",
 "캐릭터 화면: 감쇠 적용된 표식 강도 표시",
 "角色面板: 显示衰减后的法印强度",
 "角色面板: 顯示衰減後的法印強度",
 "صفحة الشخصية: إظهار قوة الإشارات بعد التضاؤل",
]


def main():
    # 1. обёртка в мод
    t = io.open(SRC, encoding="utf-8").read()
    if "GetTotalSpellPower" in t:
        print("[--] обёртка уже есть")
    else:
        t = t.rstrip("\n") + "\n" + WRAPPER
        tmp = SRC + ".tmp"
        io.open(tmp, "w", encoding="utf-8", newline="\n").write(t)
        os.replace(tmp, SRC)
        print("[ok] обёртка добавлена")

    # 2. настройка + подпись
    s = io.open(SPEC, encoding="utf-8").read()
    if "mutf_sheet" in s:
        print("[--] настройка уже есть")
        return

    if s.count(SETTING_OLD) != 1:
        print("!! не найдено место для настройки"); return
    s = s.replace(SETTING_OLD, SETTING_NEW, 1)

    block = '"mutf_sheet": {\n'
    for loc, txt in zip(LOCS, SHEET):
        block += ' "%s": "%s",\n' % (loc, txt)
    block += "},\n\n"
    s = s.replace('"mmpk_menu": {', block + '"mmpk_menu": {', 1)

    tmp = SPEC + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(s)
    os.replace(tmp, SPEC)
    print("[ok] настройка и подпись добавлены")

    import sys, re
    sys.path.insert(0, HERE)
    import spec
    m = [x for x in spec.MODS if x["mod"] == "modW3EERedux_Mutations"][0]
    miss = [k for k in spec.keys_of(m) if k not in spec.TR]
    print("настроек:", len(m["vars"]), " без перевода:", miss or "нет")
    src = io.open(SRC, encoding="utf-8").read()
    print("обёрток:", len(re.findall(r"@wrapMethod", src)),
          " вызовов оригинала:", len(re.findall(r"wrappedMethod\s*\(", src)))


main()
