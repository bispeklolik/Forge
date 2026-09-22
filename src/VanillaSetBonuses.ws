// VanillaSetBonuses.ws  --  сетовые бонусы для ЧИСТОЙ ванили, без W3EE Redux
//
// ⚠️ ЭТО ДРУГОЙ МОД, А НЕ ПОРТ. Наш Tier-Scaled Set Bonuses ослабляет редуксовые
// механики — стойкость, адреналин, обработчик боя. Ничего этого в ванили нет.
// Общего у двух модов только замысел и «калькулятор ступени».
//
// ЧТО НЕ ТАК В ВАНИЛИ
//   1. Комплект вообще не считается, пока вещь не гроссмейстерская: счётчик
//      частей пропускает всё без ярлыка 'SetBonusPiece' (playerWitcher.ws:10235).
//      То есть нижние ступени дают НОЛЬ, а не ослабленный бонус.
//   2. Пороги жёсткие — 3 части на младший бонус и 6 на старший
//      (gameParams.ws:340-341). Присвоить их из мода нельзя: это const-поля, и
//      значение задаётся строкой default в теле класса.
//
// ЧТО ДЕЛАЕТ ЭТОТ МОД — три перехвата, и всё:
//   1. UpdateItemSetBonuses  -> нижние ступени начинают считаться
//   2. IsSetBonusActive      -> пороги берутся из ползунков мода
//   3. GetSetPartsEquipped   -> сила бонуса падает пропорционально ступени
//
// ПОЧЕМУ ТРЕТЬЕГО ПЕРЕХВАТА ХВАТАЕТ НА ВСЁ МАСШТАБИРОВАНИЕ.
// Ваниль сама умножает силу трёх бонусов на число надетых частей:
//   Волк    damageManagerProcessor.ws:1092   bonusCount *= GetSetPartsEquipped(Wolf)
//   Кот     damageManagerProcessor.ws:1110   damageBonus *= GetSetPartsEquipped(Lynx)
//   Медведь quenEntity.ws:317                valueMultiplicative *= GetSetPartsEquipped(Bear)
// Вернув из этого метода уменьшенное число, мы ослабляем все три разом, не трогая
// ни одного чужого файла.
//
// ⚠️ У этого приёма есть видимое следствие: строку «N/6» в подсказке рисует тот же
// метод (guiTooltipComponent.ws:844). При включённом ослаблении там будет стоять
// уменьшенное число. Это честно — оно и показывает, во сколько игра ценит комплект, —
// но к этому надо быть готовым. Настройка ScalePower выключает ослабление целиком.
//
// НИЧЕГО НЕ ПИШЕТСЯ В СОХРАНЕНИЕ. Ни один файл игры не копируется и не правится.


// ------------------------------------------------------------- настройки ---
//
// ⚠️ Имя группы продублировано здесь и в XML раздела настроек. Переименуете там,
// не переименовав здесь, — все настройки молча свалятся в значения по умолчанию.

function VSB_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue( 'VanillaSetBonuses', varName );
	if( s == "" )
		return fallback;

	return s;
}

function VSB_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = VSB_Str( varName, "" );
	if( s == "" )
		return fallback;

	return StringToInt( s );
}

function VSB_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = VSB_Str( varName, "" );
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}

// Пороги. Значения по умолчанию — ванильные, то есть при свежей установке мод
// ничего не меняет, пока игрок сам не подвинет ползунок.
function VSB_MinorCount() : int
{
	return Max( 1, VSB_Int( 'MinorCount', theGame.params.ITEMS_REQUIRED_FOR_MINOR_SET_BONUS ) );
}

function VSB_MajorCount() : int
{
	return Max( 1, VSB_Int( 'MajorCount', theGame.params.ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS ) );
}


// ----------------------------------------------------------------- состояние ---
//
// Ничего не помечено как saved: сущность игрока пересобирается при каждой загрузке,
// кэш возвращается недействительным сам, и сохранение остаётся байт-в-байт таким же,
// как без мода.

@addField( W3PlayerWitcher ) public var VSB_tier : int;
@addField( W3PlayerWitcher ) public var VSB_tierType : int;
@addField( W3PlayerWitcher ) public var VSB_tierValid : bool;
@addField( W3PlayerWitcher ) public var VSB_didRestore : bool;


// ------------------------------------------------------ ступень и её вес ---

// Тип комплекта -> ярлык его вещей. Все восемь есть в ванили (gameParams.ws:292-299).
@addMethod( W3PlayerWitcher ) function VSB_TagForType( setType : EItemSetType ) : name
{
	switch( setType )
	{
		case EIST_Lynx:		return 'LynxSet';
		case EIST_Gryphon:	return 'GryphonSet';
		case EIST_Bear:		return 'BearSet';
		case EIST_Wolf:		return 'WolfSet';
		case EIST_RedWolf:	return 'RedWolfSet';
		case EIST_Vampire:	return 'VampireSet';
		case EIST_Viper:	return 'ViperSet';
		case EIST_Netflix:	return 'NetflixSet';
	}
	return '';
}

// Ступень вещи ПО ИМЕНИ.
//
// Ярлык гроссмейстера для этого не годится: в ветке Новой игры+ игра вешает его на
// ВСЕ ступени, и тогда любая вещь читалась бы как верхняя, а мод молча превращался
// бы в пустышку.
//
// У четырёх школ нагрудник и мечи начинают лестницу с БЕЗНОМЕРНОГО имени
// («Bear Armor» -> lvl1, «Bear Armor 4» -> lvl5), а сапоги, перчатки и штаны
// нумерованы с единицы — отсюда поправка. У Netflix лестница короче, три ступени,
// её сдвигаем вверх, иначе полный комплект застрял бы на слабейшем множителе.
@addMethod( W3PlayerWitcher ) function VSB_TierFromName( itemName : string, cat : name ) : int
{
	var tier : int;

	tier = StringToInt( StrRight( itemName, 1 ) );

	if( StrContains( itemName, 'Netflix' ) )
		return Clamp( tier + 3, 3, 5 );

	// «Starting Armor 1» носит ярлык Волка, комплектом не являясь. Без оговорки
	// стартовая куртка читалась бы как вторая ступень и била бы настоящую первую.
	if( ( cat == 'armor' || cat == 'steelsword' || cat == 'silversword' )
		&& !StrContains( itemName, 'Starting' ) && !StrContains( itemName, 'Red Wolf' ) )
		tier += 1;

	return Clamp( tier, 1, 5 );
}

// Средняя ступень НАДЕТОГО комплекта. Считается по шести слотам снаряжения: сила
// бонуса должна следовать за тем, что на игроке, а не за складом.
@addMethod( W3PlayerWitcher ) function VSB_WornTier( setType : EItemSetType ) : int
{
	var slots : array< EEquipmentSlots >;
	var item  : SItemUniqueId;
	var tag   : name;
	var i, sum, cnt : int;

	if( VSB_tierValid && VSB_tierType == (int)setType )
		return VSB_tier;

	tag = VSB_TagForType( setType );
	if( tag == '' )
		return 5;

	slots.PushBack( EES_SteelSword );
	slots.PushBack( EES_SilverSword );
	slots.PushBack( EES_Armor );
	slots.PushBack( EES_Gloves );
	slots.PushBack( EES_Pants );
	slots.PushBack( EES_Boots );

	for( i = 0; i < slots.Size(); i += 1 )
	{
		if( !GetItemEquippedOnSlot( slots[i], item ) )
			continue;
		if( !inv.IsIdValid( item ) || !inv.ItemHasTag( item, tag ) )
			continue;

		sum += VSB_TierFromName( NameToString( inv.GetItemName( item ) ),
			inv.GetItemCategory( item ) );
		cnt += 1;
	}

	// Ничего не нашли — ведём себя как без мода. Обнулять нельзя: ноль означал бы
	// «ослабить до предела» там, где просто нечего мерить.
	if( cnt <= 0 )
		return 5;

	VSB_tier = Clamp( RoundMath( ((float)sum) / ((float)cnt) ), 1, 5 );
	VSB_tierType = (int)setType;
	VSB_tierValid = true;

	return VSB_tier;
}

// 0.0 .. 1.0. Единица — полная сила: столько же отдают выключённый мод и
// гроссмейстерский комплект, поэтому все места вызова могут просто не считать.
@addMethod( W3PlayerWitcher ) function VSB_Power( setType : EItemSetType ) : float
{
	var pct, tier : int;

	if( !VSB_Bool( 'ScalePower', true ) )
		return 1.f;

	tier = VSB_WornTier( setType );
	if( tier >= 5 || tier <= 0 )
		return 1.f;

	if( tier == 1 )
		pct = VSB_Int( 'Tier1', 40 );
	else if( tier == 2 )
		pct = VSB_Int( 'Tier2', 55 );
	else if( tier == 3 )
		pct = VSB_Int( 'Tier3', 70 );
	else
		pct = VSB_Int( 'Tier4', 85 );

	return ((float)Clamp( pct, 0, 100 )) / 100.f;
}


// --------------------------------------------- 1. нижние ступени считаются ---
//
// Ванильный UpdateItemSetBonuses первым же условием отбрасывает вещь без ярлыка
// 'SetBonusPiece' и выходит. Поэтому нижние ступени дают ноль.
//
// Мы не переписываем его логику, а ставим вещи недостающий ярлык ПЕРЕД вызовом
// оригинала — дальше игра считает сама, и вместе со счётчиком верно отрабатывают
// подсказки, звуковые банки и обучение. Приём тот же, что в моде рунных камней.
@wrapMethod( W3PlayerWitcher ) function UpdateItemSetBonuses( item : SItemUniqueId, increment : bool )
{
	if( VSB_Bool( 'CountAllTiers', true )
		&& inv.IsIdValid( item )
		&& inv.IsItemSetItem( item )
		&& !inv.ItemHasTag( item, theGame.params.ITEM_SET_TAG_BONUS ) )
	{
		inv.AddItemTag( item, theGame.params.ITEM_SET_TAG_BONUS );
	}

	VSB_tierValid = false;

	wrappedMethod( item, increment );
}

// Ярлыки НЕ переживают сохранение — это измерено, а не предположено. Счётчик
// переживает (он saved), но если после загрузки снять вещь, ярлыка на ней уже нет,
// оригинал выйдет по первому же условию и счётчик не уменьшится. Отсюда дрейф.
//
// Поэтому после каждой загрузки возвращаем ярлыки надетым вещам.
@wrapMethod( W3PlayerWitcher ) function OnSpawned( spawnData : SEntitySpawnData )
{
	var slots : array< EEquipmentSlots >;
	var item  : SItemUniqueId;
	var i     : int;

	wrappedMethod( spawnData );

	if( !VSB_Bool( 'CountAllTiers', true ) )
		return;

	slots.PushBack( EES_SteelSword );
	slots.PushBack( EES_SilverSword );
	slots.PushBack( EES_Armor );
	slots.PushBack( EES_Gloves );
	slots.PushBack( EES_Pants );
	slots.PushBack( EES_Boots );

	for( i = 0; i < slots.Size(); i += 1 )
	{
		if( !GetItemEquippedOnSlot( slots[i], item ) )
			continue;
		if( inv.IsIdValid( item ) && inv.IsItemSetItem( item ) )
			inv.AddItemTag( item, theGame.params.ITEM_SET_TAG_BONUS );
	}

	VSB_didRestore = true;
	VSB_tierValid = false;
}


// ------------------------------------------------ 2. свои пороги бонусов ---
//
// Присвоить ITEMS_REQUIRED_FOR_* нельзя: это const-поля, значение задаётся строкой
// default в теле класса, и правка потребовала бы полной замены gameParams.ws — то
// есть конфликта с каждым модом, который трогает тот же файл.
//
// Зато вся игра решает «бонус включён» ровно в одном месте, и его можно обернуть.
// Обратной функции «бонус -> тип комплекта» в ванили нет, поэтому таблица своя.
// Счётчик частей БЕЗ нашего ослабления. Нужен порогу: обёртка GetSetPartsEquipped
// ниже возвращает уменьшенное число, и если сравнивать порог с ним, комплект первой
// ступени не включил бы бонус вовсе — ослабление превратилось бы в запрет.
@addMethod( W3PlayerWitcher ) function VSB_RawParts( setType : EItemSetType ) : int
{
	return amountOfSetPiecesEquipped[ setType ];
}

@addMethod( W3PlayerWitcher ) function VSB_TypeForBonus( bonus : EItemSetBonus ) : EItemSetType
{
	switch( bonus )
	{
		case EISB_Lynx_1:
		case EISB_Lynx_2:		return EIST_Lynx;
		case EISB_Gryphon_1:
		case EISB_Gryphon_2:	return EIST_Gryphon;
		case EISB_Bear_1:
		case EISB_Bear_2:		return EIST_Bear;
		case EISB_Wolf_1:
		case EISB_Wolf_2:		return EIST_Wolf;
		case EISB_RedWolf_1:
		case EISB_RedWolf_2:	return EIST_RedWolf;
		case EISB_Vampire:		return EIST_Vampire;
		case EISB_Netflix_1:
		case EISB_Netflix_2:	return EIST_Netflix;
	}
	return EIST_Undefined;
}

// Младший бонус или старший. Ваниль различает их не полем, а тем, с каким порогом
// сравнивает, поэтому список приходится держать здесь.
@addMethod( W3PlayerWitcher ) function VSB_IsMajorBonus( bonus : EItemSetBonus ) : bool
{
	switch( bonus )
	{
		case EISB_Lynx_2:
		case EISB_Gryphon_2:
		case EISB_Bear_2:
		case EISB_Wolf_2:
		case EISB_RedWolf_2:
		case EISB_Netflix_2:
			return true;
	}
	return false;
}

@wrapMethod( W3PlayerWitcher ) function IsSetBonusActive( bonus : EItemSetBonus ) : bool
{
	var setType : EItemSetType;
	var need : int;

	setType = VSB_TypeForBonus( bonus );
	if( setType == EIST_Undefined )
		return wrappedMethod( bonus );

	if( VSB_IsMajorBonus( bonus ) )
		need = VSB_MajorCount();
	else
		need = VSB_MinorCount();

	// Оригинал не зовём намеренно: наш ответ замещает его целиком, и это ЕДИНСТВЕННОЕ
	// место в игре, решающее «бонус активен». Проверено обходом всех вызовов.
	//
	// ⚠️ Сравниваем с СЫРЫМ счётчиком, а не с GetSetPartsEquipped: тот уже ослаблен,
	// и порог по нему превратил бы ослабление в запрет.
	return VSB_RawParts( setType ) >= need;
}


// ---------------------------------------------- 3. сила падает со ступенью ---
//
// Ваниль сама умножает силу трёх бонусов на число надетых частей — см. шапку файла.
// Вернув уменьшенное число, мы ослабляем их все разом.
//
// ⚠️ Округление вверх, а не вниз: у комплекта первой ступени из четырёх частей
// 4 * 0.4 = 1.6, и округление вниз дало бы единицу — бонус, неотличимый от одной
// надетой вещи. Вверх даёт двойку, то есть ослабление есть, но не в ноль.
//
// ⚠️ Порог активации это НЕ затрагивает: обёртка IsSetBonusActive выше сравнивает с
// сырым счётчиком через VSB_RawParts. Иначе ослабление превратилось бы в запрет.
@wrapMethod( W3PlayerWitcher ) function GetSetPartsEquipped( setType : EItemSetType ) : int
{
	var raw : int;
	var power : float;

	raw = wrappedMethod( setType );
	if( raw <= 0 )
		return raw;

	power = VSB_Power( setType );
	if( power >= 0.999f )
		return raw;

	return Max( 1, CeilF( ((float)raw) * power ) );
}


// ----------------------------------------------------------- проверка руками ---
//
// Без неё правило проверить нечем: и порог, и ослабление молчат — бонус просто
// оказывается не той силы, без единого сообщения.

exec function vsbinfo()
{
	var w : W3PlayerWitcher;
	var types : array< EItemSetType >;
	var msg : string;
	var i : int;

	w = GetWitcherPlayer();
	if( !w ) return;

	types.PushBack( EIST_Lynx );
	types.PushBack( EIST_Gryphon );
	types.PushBack( EIST_Bear );
	types.PushBack( EIST_Wolf );
	types.PushBack( EIST_RedWolf );
	types.PushBack( EIST_Netflix );

	msg = "VSB  minor:" + VSB_MinorCount() + " major:" + VSB_MajorCount();
	msg = msg + "  restored:" + w.VSB_didRestore + "<br>";

	for( i = 0; i < types.Size(); i += 1 )
	{
		msg = msg + w.VSB_TagForType( types[i] )
			+ "  parts:" + w.VSB_RawParts( types[i] )
			+ " -> " + w.GetSetPartsEquipped( types[i] )
			+ "  tier:" + w.VSB_WornTier( types[i] ) + "<br>";
	}

	theGame.GetGuiManager().ShowNotification( msg, 30000 );
}
