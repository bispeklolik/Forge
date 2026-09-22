// TSSBProbe.ws  --  ОДНОРАЗОВЫЙ ЗОНД, удалить после проверки.
//
// Проверяет ровно один вопрос, от которого зависит вся схема мода
// «Tier-Scaled Set Bonuses»: можно ли из обёртки на ОДНОМ классе дотянуться
// до поля или метода, добавленного ДРУГОМУ классу.
//
// Прецедентов в сборке нет ни одного (проверено на 2143 файлах .ws), поэтому
// строить на этом вслепую нельзя. Зонд компилируется — приём работает.
// Зонд не компилируется — ошибка назовёт строку, и станет ясно, что именно
// из четырёх вариантов недоступно.
//
//   A  чтение и запись @addField, добавленного W3PlayerWitcher, снаружи
//   B  вызов @addMethod, добавленного W3PlayerWitcher, снаружи
//   C  то же для поля, добавленного КЛАССУ ИЗ W3EE (W3Effect_Poise)
//   D  то же для метода, добавленного классу из W3EE
//
// Игровое поведение зонд не меняет: он только читает и пишет свои же поля.


// Оба варианта объявления сразу: без модификатора и public. В примере самой
// CDPR добавленный метод объявлен public, но про поля документация молчит,
// а ванильные классы читаются снаружи и без модификатора. Проверяем оба,
// чтобы при отказе сразу было видно, дело в видимости или в самом приёме.

@addField(W3PlayerWitcher)
var TSSB_probeBare : int;

@addField(W3PlayerWitcher)
public var TSSB_probePublic : int;

@addMethod(W3PlayerWitcher)
public function TSSB_ProbeMethod() : int
{
	return TSSB_probeBare + TSSB_probePublic + 1;
}

@addField(W3Effect_Poise)
public var TSSB_probePoise : float;

@addMethod(W3Effect_Poise)
public function TSSB_ProbePoiseMethod() : float
{
	return TSSB_probePoise;
}


// Хозяин обёртки — ЧУЖОЙ класс. В этом весь смысл проверки.
@wrapMethod(W3DamageManagerProcessor) function CanDismember( wasFrozen : bool, out dismemberExplosion : bool, out weaponName : name ) : bool
{
	var witcher : W3PlayerWitcher;
	var poise   : W3Effect_Poise;
	var acc     : float;

	witcher = GetWitcherPlayer();
	if( witcher )
	{
		witcher.TSSB_probeBare = 1;                     // A, без модификатора
		witcher.TSSB_probePublic = 2;                   // A, public
		acc = (float)witcher.TSSB_ProbeMethod();        // B

		poise = (W3Effect_Poise)witcher.GetBuff(EET_Poise);
		if( poise )
		{
			poise.TSSB_probePoise = acc;                // C
			acc = poise.TSSB_ProbePoiseMethod();        // D
		}
	}

	return wrappedMethod( wasFrozen, dismemberExplosion, weaponName );
}
