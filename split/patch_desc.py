# -*- coding: utf-8 -*-
"""
Чинит расчёт числа в описании Призрака.

Было: брали текущую интенсивность и вычитали вклад мутации. Когда мутация
ВЫКЛЮЧЕНА, вычитать нечего — её вклада в сумме нет, — и мы уходили вниз по
кривой, где она круче, получая завышенное число. Выключено показывало 14.6%,
включено 7.4%.

Стало: сначала приводим к базе БЕЗ мутации (вычитаем только если она реально
включена), потом считаем разницу «с ней против без неё». Число одинаково в
обоих состояниях, потому что вопрос один: сколько эта мутация даёт.

Плюс: описание считается по СТОКОВОЙ интенсивности. Иначе при поднятом ползунке
обхода сжатия выключенная мутация считалась бы по стоку, а включённая — по
усиленной величине, и они снова разъехались бы.
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src", "Mutations.ws")

OLD_FIELD = """@wrapMethod(W3PlayerWitcher) function GetTotalSignSpellPower( signSkill : ESkill ) : SAbilityAttributeValue
{
	var sp        : SAbilityAttributeValue;
	var bypass    : float;
	var without   : float;
	var fullValue : float;

	sp = wrappedMethod( signSkill );

	bypass = MUTF_SignBypass();
	if( bypass <= 0.f )
		return sp;
"""

NEW_FIELD = """// Set while the tooltip is measuring, so the bypass below stands aside and the
// measurement always starts from the stock value. Without it the number would
// depend on whether the bypass slider happens to be up.
@addField(W3PlayerWitcher)
public var MUTF_descMode : bool;

@wrapMethod(W3PlayerWitcher) function GetTotalSignSpellPower( signSkill : ESkill ) : SAbilityAttributeValue
{
	var sp        : SAbilityAttributeValue;
	var bypass    : float;
	var without   : float;
	var fullValue : float;

	sp = wrappedMethod( signSkill );

	if( MUTF_descMode )
		return sp;

	bypass = MUTF_SignBypass();
	if( bypass <= 0.f )
		return sp;
"""

OLD_DESC = """			if( mutationType == EPMT_Mutation1 && locKey != '' )
			{
				sp = GetTotalSignSpellPower( S_Magic_s01 );
				if( sp.valueMultiplicative > 0.f )
				{
					without = MUTF_WithoutSpecter( sp.valueMultiplicative );
					if( without > 0.f )
					{
						delivered = ( sp.valueMultiplicative / without - 1.f ) * 100.f;

						params.PushBack( "50" );
						params.PushBack( FloatToStringPrec( delivered, 1 ) );
						params.PushBack( "50" );
						return GetLocStringByKeyExtWithParams( NameToString(locKey),,,params );
					}
				}
			}"""

NEW_DESC = """			if( mutationType == EPMT_Mutation1 && locKey != '' )
			{
				// Measure from the STOCK value, with the bypass standing aside.
				MUTF_descMode = true;
				sp = GetTotalSignSpellPower( S_Magic_s01 );
				MUTF_descMode = false;

				// Reduce to the base WITHOUT the mutation. Subtract its +0.5 only
				// if it is actually switched on - otherwise there is nothing there
				// to subtract, and subtracting anyway lands further down the curve
				// where it is steeper, which is what made the tooltip read roughly
				// double while the mutation was off.
				raw = MUTF_Uncompress( sp.valueMultiplicative );
				if( IsMutationActive( EPMT_Mutation1 ) )
					raw = raw - 0.5f;
				if( raw < 0.f )
					raw = 0.f;

				without = MUTF_Compress( raw );
				withIt  = MUTF_Compress( raw + 0.5f );

				// The bypass moves the delivered value toward a true +50%, so the
				// tooltip has to move with it.
				bypass = MUTF_SignBypass();
				if( bypass > 0.f && without * 1.5f > withIt )
					withIt = withIt + bypass * ( without * 1.5f - withIt );

				if( without > 0.f )
				{
					delivered = ( withIt / without - 1.f ) * 100.f;

					params.PushBack( "50" );
					params.PushBack( FloatToStringPrec( delivered, 1 ) );
					params.PushBack( "50" );
					return GetLocStringByKeyExtWithParams( NameToString(locKey),,,params );
				}
			}"""

OLD_VARS = """	var sp       : SAbilityAttributeValue;
	var without, delivered : float;"""

NEW_VARS = """	var sp       : SAbilityAttributeValue;
	var raw, without, withIt, bypass, delivered : float;"""


def main():
    t = io.open(SRC, encoding="utf-8").read()

    for old, new, label in ((OLD_FIELD, NEW_FIELD, "флаг измерения"),
                            (OLD_VARS, NEW_VARS, "локальные переменные"),
                            (OLD_DESC, NEW_DESC, "расчёт описания")):
        if t.count(old) != 1:
            print("!! не найдено ровно один раз:", label, "->", t.count(old))
            return
        t = t.replace(old, new, 1)
        print("[ok]", label)

    tmp = SRC + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(t)
    os.replace(tmp, SRC)

    import re
    print()
    print("обёрток:", len(re.findall(r"@wrapMethod", t)),
          " вызовов оригинала:", len(re.findall(r"wrappedMethod\s*\(", t)),
          " добавленных полей:", len(re.findall(r"@addField", t)))


main()
