// TierBonuses.ws  --  Tier-Scaled Set Bonuses, an add-on for W3EE Redux
//
// In stock W3EE the SECOND bonus of an armour set - the "grandmaster bonus" -
// only switches on with a full grandmaster set. Until then half the set does
// nothing at all, which makes every lower tier feel like filler.
//
// This unlocks the second bonus on EVERY tier, but weakens it in proportion to
// the average tier of the equipped pieces. The ADDED part of a bonus is scaled,
// never the absolute value: the Wolf adrenaline cap is 100 + 50*power, so 120 at
// tier 1 and 150 at grandmaster. Grandmaster is pinned at full strength, so a
// complete set always behaves exactly like unmodded W3EE.
//
// The set bonus DESCRIPTIONS are rewritten to show the real scaled numbers.
// Stock W3EE pushes fixed literals into them, so the tooltip promises 150 while
// the game gives 120 - that mismatch is what this mod exists to end.
//
// Nothing here is written to the save. No file of W3EE is copied or edited.


// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function TSSB_Str( varName : name, fallback : string ) : string
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue('W3EERedux_TierBonuses', varName);
	if( s == "" )
		return fallback;

	return s;
}

function TSSB_Int( varName : name, fallback : int ) : int
{
	var s : string;

	s = TSSB_Str(varName, "");
	if( s == "" )
		return fallback;

	return StringToInt(s);
}

function TSSB_Bool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = TSSB_Str(varName, "");
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}


// ---------------------------------------------------------------------------
// State
//
// All of it lives on W3PlayerWitcher and none of it is 'saved'. The player
// entity is rebuilt on every load, so the cache comes back invalid by itself and
// a save made with this mod is byte-identical to one made without it.
//
// TSSB_poiseOpen is a SEPARATE bool rather than a zero sentinel on the scale:
// zero is a legal power (a tier slider at 0%), and using it as "closed" would
// make the bracket silently run at full grandmaster strength - the exact
// opposite of what the player asked for.
// ---------------------------------------------------------------------------

@addField(W3PlayerWitcher)
public var TSSB_tier : int;

@addField(W3PlayerWitcher)
public var TSSB_tierValid : bool;

@addField(W3PlayerWitcher)
public var TSSB_poiseScale : float;

@addField(W3PlayerWitcher)
public var TSSB_poiseOpen : bool;

@addField(W3PlayerWitcher)
public var TSSB_signAdr : bool;

// Кэш для «силы по собранному комплекту». Считать приходится обходом трёх
// хранилищ, а спрашивают до шести раз подряд — почти всегда про один и тот же
// комплект. Сбрасывается там же, где и TSSB_tierValid.
@addField(W3PlayerWitcher)
public var TSSB_ownedCode : int;

@addField(W3PlayerWitcher)
public var TSSB_ownedTier : int;

@addField(W3PlayerWitcher)
public var TSSB_ownedValid : bool;


// ---------------------------------------------------------------------------
// Tier of the equipped set
// ---------------------------------------------------------------------------

// Читает настройку ЧУЖОГО мода — рунных камней. Группа названа строкой, поэтому
// зависимости не возникает: без того мода группы нет, вернётся пусто и возьмётся
// значение по умолчанию.
function TSSB_StoneBool( varName : name, fallback : bool ) : bool
{
	var s : string;

	s = theGame.GetInGameConfigWrapper().GetVarValue( 'SetBonusTransfer', varName );
	if( s == "" )
		return fallback;

	if( s == "true" || s == "1" )
		return true;

	return false;
}

// Код комплекта (нумерация мода рунных камней) -> ярлык вещей этого комплекта.
// Перечислены ТОЛЬКО те, которые этот мод масштабирует. Всё остальное — пустая
// строка, то есть «не масштабируем, полная сила»:
//   Мантикора  — её вторая строка меняет не число, а форму расчёта;
//   Змея       — у брони нет ступеней вовсе, «EP1 Witcher Armor» сразу верхняя;
//   реликтовые — ступеней не существует.
@addMethod(W3PlayerWitcher)
public function TSSB_TagForCode( code : int ) : name
{
	switch( code )
	{
		case 1:	return 'LynxSet';
		case 2:	return 'GryphonSet';
		case 3:	return 'BearSet';
		case 4:	return 'WolfSet';
		case 8:	return 'NetflixSet';
	}
	return '';
}

// Ступень вещи ПО ИМЕНИ. Ярлык гроссмейстера здесь намеренно не используется:
// в ветке Новой игры+ игра вешает его на ВСЕ ступени, и тогда любая вещь читалась
// бы как верхняя, а мод молча превращался в пустышку.
//
// У четырёх школ лестница из пяти ступеней, причём нагрудник и мечи начинают её с
// БЕЗНОМЕРНОГО имени («Bear Armor» -> lvl1, «Bear Armor 4» -> lvl5), а сапоги,
// перчатки и штаны нумерованы с единицы. Отсюда поправка на единицу.
//
// У Netflix лестница короче — три ступени вместо пяти. Сдвигаем её вверх, иначе
// полный комплект Netflix навсегда застрял бы на слабейшем множителе.
@addMethod(W3PlayerWitcher)
public function TSSB_TierFromName( itemName : string, cat : name, code : int ) : int
{
	var tier : int;

	tier = StringToInt( StrRight( itemName, 1 ) );

	if( code == 8 )
		return Clamp( tier + 3, 3, 5 );

	// «Starting Armor 1» и «Long Steel Sword 1» носят ярлык Волка, хотя комплектом
	// не являются. Без этой оговорки стартовая куртка читалась бы как вторая
	// ступень и била бы настоящую первую.
	if( ( cat == 'armor' || cat == 'steelsword' || cat == 'silversword' )
		&& !StrContains( itemName, 'Starting' ) && !StrContains( itemName, 'Red Wolf' ) )
		tier += 1;

	return Clamp( tier, 1, 5 );
}

// Проходит по одному хранилищу и оставляет ЛУЧШУЮ ступень в каждом разделе.
// Лучшую, а не все подряд: у игрока может лежать и старьё, и дубли.
@addMethod(W3PlayerWitcher)
public function TSSB_CollectTiers( comp : CInventoryComponent, tag : name, code : int,
	out cats : array< name >, out best : array< int > )
{
	var items : array< SItemUniqueId >;
	var cat   : name;
	var i, j, t : int;
	var found : bool;

	if( !comp )
		return;

	items = comp.GetItemsByTag( tag );

	for( i = 0; i < items.Size(); i += 1 )
	{
		if( !comp.IsIdValid( items[i] ) )
			continue;

		// Вещь, помеченную камнем, в счёт НЕ берём: она не часть комплекта, а его
		// получатель. Иначе расчёт стал бы кусать сам себя.
		if( comp.GetItemModifierInt( items[i], 'SBT_Set', 0 ) > 0 )
			continue;

		cat = comp.GetItemCategory( items[i] );
		t = TSSB_TierFromName( NameToString( comp.GetItemName( items[i] ) ), cat, code );

		found = false;
		for( j = 0; j < cats.Size(); j += 1 )
		{
			if( cats[j] == cat )
			{
				found = true;
				if( t > best[j] )
					best[j] = t;
				break;
			}
		}

		if( !found )
		{
			cats.PushBack( cat );
			best.PushBack( t );
		}
	}
}

// Ступень комплекта, который игрок РЕАЛЬНО собрал, где бы вещи ни лежали.
//
// Правило: берём лучшее по каждому разделу, из этого — N лучших, усредняем.
// N — порог второй строки бонуса из настроек игры (ползунок, у кого-то 4, у
// кого-то 6). Делитель именно порог, а не число разделов: бонус сам требует ровно
// N частей, значит и сила его считается по тем же N. Иначе игрок наказывался бы за
// то, чего игра у него и не спрашивает.
@addMethod(W3PlayerWitcher)
public function TSSB_OwnedSetTier( code : int ) : int
{
	var tag   : name;
	var horse : W3HorseManager;
	var cats  : array< name >;
	var best  : array< int >;
	var i, need, sum, cnt, top, topIdx : int;

	if( TSSB_ownedValid && TSSB_ownedCode == code )
		return TSSB_ownedTier;

	tag = TSSB_TagForCode( code );
	if( tag == '' )
		return 5;

	TSSB_CollectTiers( GetInventory(), tag, code, cats, best );

	// Сумки Плотвы и стационарный тайник — ОДНО хранилище, отдельно тайник искать
	// не нужно. Менеджер бывает null: при загрузке сейва он появляется не сразу.
	horse = GetHorseManager();
	if( horse )
		TSSB_CollectTiers( horse.GetInventoryComponent(), tag, code, cats, best );

	// Порог берём у игры, а не зашиваем: в Redux это ползунок в меню.
	//
	// Запасной источник — ванильный параметр ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS
	// (в ванили 6, в W3EE 4). Он есть и там, и там, и нужен на случай, если
	// ползунок вернёт ноль: делить на единицу означало бы взять ОДНУ лучшую вещь и
	// объявить её силой всего комплекта — тихо и слишком щедро.
	need = Options().SetBonusCountSecond();
	if( need < 1 )
		need = theGame.params.ITEMS_REQUIRED_FOR_MAJOR_SET_BONUS;
	if( need < 1 )
		need = 6;

	sum = 0;
	cnt = 0;
	while( cnt < need && best.Size() > 0 )
	{
		top = -1;
		topIdx = -1;
		for( i = 0; i < best.Size(); i += 1 )
		{
			if( best[i] > top )
			{
				top = best[i];
				topIdx = i;
			}
		}
		if( topIdx < 0 )
			break;

		sum += top;
		cnt += 1;
		best.Erase( topIdx );
	}

	// Ничего не нашли — ведём себя как без мода. Молча обнулять нельзя: ноль в
	// TSSB_Power означает ПОЛНУЮ силу, то есть прямо противоположное задуманному.
	if( cnt <= 0 )
		return 5;

	TSSB_ownedTier = Clamp( RoundMath( ((float)sum) / ((float)cnt) ), 1, 5 );
	TSSB_ownedCode = code;
	TSSB_ownedValid = true;

	return TSSB_ownedTier;
}

// 1..5 for one equipped set piece, 0 if it is not a set piece at all.
@addMethod(W3PlayerWitcher)
public function TSSB_PieceTier( item : SItemUniqueId ) : int
{
	var invComp  : CInventoryComponent;
	var itemName : string;
	var cat      : name;
	var code     : int;

	invComp = GetInventory();
	if( !invComp )
		return 0;

	if( !invComp.IsIdValid(item) )
		return 0;

	// ⬇️ РАНЬШЕ всех прочих проверок. Вещь, помеченная рунным камнем, частью
	// комплекта не является — на проверке IsItemSetItem она бы вылетела, — но
	// бонус несёт, и сила его должна идти от того комплекта, что игрок собрал.
	//
	// Связь с модом камней — через ЧИСЛО на вещи, а не через вызов его функций:
	// 'SBT_Set' это данные, компилятор их нигде не разрешает, и без того мода
	// ключа просто никто не писал — вернётся ноль.
	code = invComp.GetItemModifierInt( item, 'SBT_Set', 0 );
	if( code > 0 )
	{
		if( !TSSB_StoneBool( 'PowerFromOwnedSet', true ) )
			return 5;

		return TSSB_OwnedSetTier( code );
	}

	if( !invComp.IsItemSetItem(item) )
		return 0;

	// Змея идёт полной силой всегда: у её брони ступеней не существует —
	// «EP1 Witcher Armor» одна и сразу верхняя.
	if( invComp.ItemHasTag( item, 'ViperSet' ) )
		return 5;

	itemName = NameToString( invComp.GetItemName(item) );
	cat      = invComp.GetItemCategory( item );

	if( StrContains( itemName, 'Netflix' ) )
		return TSSB_TierFromName( itemName, cat, 8 );

	return TSSB_TierFromName( itemName, cat, 0 );
}

// Averages the six equipment slots. Deliberately does NOT mark the cache valid
// when it found nothing: an empty or unreadable inventory must be retried, not
// frozen at a guess. Freezing it would hand out the full grandmaster bonus while
// the player wears rags.
@addMethod(W3PlayerWitcher)
public function TSSB_RefreshTier()
{
	var item          : SItemUniqueId;
	var sum, count, t : int;

	sum = 0;
	count = 0;

	if( GetItemEquippedOnSlot( EES_SteelSword, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}
	if( GetItemEquippedOnSlot( EES_SilverSword, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}
	if( GetItemEquippedOnSlot( EES_Armor, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}
	if( GetItemEquippedOnSlot( EES_Gloves, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}
	if( GetItemEquippedOnSlot( EES_Pants, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}
	if( GetItemEquippedOnSlot( EES_Boots, item ) )
	{
		t = TSSB_PieceTier(item);
		if( t > 0 ) { sum += t; count += 1; }
	}

	if( count <= 0 )
	{
		TSSB_tier = 5;              // nothing found: behave as stock for now...
		return;                     // ...but do NOT cache it, retry next time
	}

	TSSB_tier = RoundMath( ((float)sum) / ((float)count) );
	TSSB_tierValid = true;
}

// 0.0 .. 1.0 . One means "full strength", which is also what a disabled mod and
// a grandmaster set return, so every call site below can simply skip its work.
@addMethod(W3PlayerWitcher)
public function TSSB_Power() : float
{
	var pct : int;

	if( !TSSB_Bool('Enabled', true) )
		return 1.f;

	if( !TSSB_tierValid )
		TSSB_RefreshTier();

	if( TSSB_tier >= 5 || TSSB_tier <= 0 )
		return 1.f;

	if( TSSB_tier == 1 )
		pct = TSSB_Int('Tier1', 40);
	else if( TSSB_tier == 2 )
		pct = TSSB_Int('Tier2', 55);
	else if( TSSB_tier == 3 )
		pct = TSSB_Int('Tier3', 70);
	else
		pct = TSSB_Int('Tier4', 85);

	return ((float)Clamp(pct, 0, 100)) / 100.f;
}

@addMethod(W3PlayerWitcher)
public function TSSB_BonusToSetType( bonus : EItemSetBonus ) : EItemSetType
{
	switch( bonus )
	{
		case EISB_Lynx_1:
		case EISB_Lynx_2:			return EIST_Lynx;
		case EISB_Gryphon_1:
		case EISB_Gryphon_2:		return EIST_Gryphon;
		case EISB_Bear_1:
		case EISB_Bear_2:			return EIST_Bear;
		case EISB_Wolf_1:
		case EISB_Wolf_2:			return EIST_Wolf;
		// ⛔ Красный Волк (Мантикора) намеренно НЕ здесь. Его вторая строка —
		// это токсичность, и ни одна её величина из скрипта не масштабируется:
		// часть меняет не число, а саму форму расчёта (проценты становятся
		// абсолютом). Разблокируй мы его, комплект первого тира получал бы
		// ПОЛНЫЙ гроссмейстерский бонус, пока все прочие семейства сидят на 40%.
		// Пусть работает как в оригинале — только на гроссмейстерском сете.
		case EISB_Viper1:
		case EISB_Viper2:			return EIST_Viper;
		case EISB_Netflix_1:
		case EISB_Netflix_2:		return EIST_Netflix;
		default:					return EIST_Undefined;
	}
}


// ---------------------------------------------------------------------------
// The unlock
// ---------------------------------------------------------------------------

@wrapMethod(W3PlayerWitcher) function IsSetBonusActive( bonus : EItemSetBonus ) : bool
{
	var fam : EItemSetType;

	if( TSSB_Bool('Enabled', true) )
	{
		fam = TSSB_BonusToSetType( bonus );
		if( fam != EIST_Undefined && bonus == ItemSetTypeToItemSetBonus( fam, 2 ) )
			return GetSetPartsEquipped( fam ) >= Options().SetBonusCountSecond();
	}

	return wrappedMethod( bonus );
}

// Without this a lower-tier (Minor) set hands a Minor type to the tooltip code,
// which then has no second bonus to describe at all.
@wrapMethod(W3PlayerWitcher) function ItemSetTypeToItemSetBonus( setType : EItemSetType, nr : int ) : EItemSetBonus
{
	var t : EItemSetType;

	t = setType;
	if( nr == 2 && TSSB_Bool('Enabled', true) && IsMinorSetType( setType ) )
		t = GetSetTypeMajor( setType );

	return wrappedMethod( t, nr );
}

// The one funnel every equip and unequip already passes through. Invalidating
// here is what makes the strength follow the gear without a reload.
@wrapMethod(W3PlayerWitcher) function ManageActiveSetBonuses( setType : EItemSetType )
{
	var adr : W3Effect_CombatAdrenaline;

	TSSB_tierValid = false;
	TSSB_ownedValid = false;

	wrappedMethod( setType );

	// The adrenaline cap is computed ONCE when the effect starts, not per use,
	// so without this the cap keeps the strength the gear had at the start of
	// the fight. That bug is in stock W3EE too.
	adr = GetAdrenalineEffect();
	if( adr )
		adr.TSSB_RefreshMax();
}


// ---------------------------------------------------------------------------
// Bear - four sites, two wrappers
//
// All four read the same two poise getters, and GetMissingPoiseWithMult calls
// GetCurrentPoise internally. Scaling both independently would multiply the
// weakening by itself, so the "missing" wrapper closes the bracket around its
// own call to the original.
// ---------------------------------------------------------------------------

@wrapMethod(W3Effect_Poise) function GetCurrentPoise() : float
{
	var v       : float;
	var witcher : W3PlayerWitcher;

	v = wrappedMethod();

	witcher = GetWitcherPlayer();
	if( witcher && witcher.TSSB_poiseOpen )
		v = v * witcher.TSSB_poiseScale;

	return v;
}

@wrapMethod(W3Effect_Poise) function GetMissingPoiseWithMult() : float
{
	var v       : float;
	var wasOpen : bool;
	var witcher : W3PlayerWitcher;

	witcher = GetWitcherPlayer();
	if( witcher )
	{
		wasOpen = witcher.TSSB_poiseOpen;
		witcher.TSSB_poiseOpen = false;     // "missing" must come from REAL poise
	}

	v = wrappedMethod();

	if( witcher )
	{
		witcher.TSSB_poiseOpen = wasOpen;

		// Both call sites in the whole compile set are Bear second-bonus sites
		// (W3EE - Combat.ws:1239 and W3EE - Effects.ws:3839), but gate on the
		// bonus anyway so this stays correct if W3EE grows a third caller.
		if( witcher.IsSetBonusActive(EISB_Bear_2) )
			v = v * witcher.TSSB_Power();
	}

	return v;
}

@wrapMethod(W3EECombatHandler) function CounterAndParry( playerVictim : CR4Player, actorAttacker : CActor, out attackAction : W3Action_Attack, out action : W3DamageAction )
{
	var witcher : W3PlayerWitcher;
	var power   : float;

	witcher = (W3PlayerWitcher)playerVictim;
	if( witcher )
	{
		power = witcher.TSSB_Power();
		if( power < 0.999f && witcher.IsSetBonusActive(EISB_Bear_2) )
		{
			witcher.TSSB_poiseScale = power;
			witcher.TSSB_poiseOpen = true;
		}
	}

	wrappedMethod( playerVictim, actorAttacker, attackAction, action );

	if( witcher )
		witcher.TSSB_poiseOpen = false;
}

@wrapMethod(W3DamageManagerProcessor) function CalculateDamage( dmgInfo : SRawDamage, powerMod : SAbilityAttributeValue ) : float
{
	var res     : float;
	var power   : float;
	var witcher : W3PlayerWitcher;

	witcher = (W3PlayerWitcher)playerVictim;
	if( witcher )
	{
		power = witcher.TSSB_Power();
		if( power < 0.999f && witcher.IsSetBonusActive(EISB_Bear_2) )
		{
			witcher.TSSB_poiseScale = power;
			witcher.TSSB_poiseOpen = true;
		}
	}

	res = wrappedMethod( dmgInfo, powerMod );

	if( witcher )
		witcher.TSSB_poiseOpen = false;

	return res;
}


// ---------------------------------------------------------------------------
// Gryphon - the extra slow inside Yrden
//
// The value never leaves the original as a return; it goes straight into
// SetTimeScale. That is a keyed SET on a named source, not an accumulation, so
// re-issuing it afterwards overwrites cleanly instead of stacking.
// ---------------------------------------------------------------------------

@wrapMethod(W3EECombatHandler) function EnchantedGlyphsSkill( yrden : W3YrdenEntity, activate : bool, entity : CEntity )
{
	var witcher   : W3PlayerWitcher;
	var wasActive : bool;
	var power     : float;

	witcher   = (W3PlayerWitcher)entity;
	wasActive = isSlowdownActive;

	wrappedMethod( yrden, activate, entity );

	if( !wasActive && isSlowdownActive && witcher && witcher.IsSetBonusActive( EISB_Gryphon_1 ) )
	{
		power = witcher.TSSB_Power();
		if( power < 0.999f )
		{
			// 0.15 base + 0.10 from the set: W3EE - Combat.ws:2710 and :2713.
			// The only two W3EE magnitudes in this mod that cannot be recovered
			// at runtime and so have to be written out here.
			theGame.SetTimeScale( 1.f - 0.15f - 0.1f * power,
			                      theGame.GetTimescaleSource( ETS_Yrden ),
			                      theGame.GetTimescalePriority( ETS_Yrden ) );
		}
	}
}


// ---------------------------------------------------------------------------
// Viper - extra potency of the second oil
//
// oilPotency is a local, but its only effect is to scale the two arrays of the
// returned struct linearly. Correcting the result by the ratio of the two
// factors reproduces the in-place edit exactly.
// ---------------------------------------------------------------------------

@wrapMethod(W3EECombatHandler) function InitializeOilInfo( playerAttacker : CR4Player ) : SOilInfo
{
	var oilInfos : SOilInfo;
	var witcher  : W3PlayerWitcher;
	var weaponId : SItemUniqueId;
	var oils     : array<W3Effect_Oil>;
	var power, skill, ratio : float;
	var i, n     : int;

	oilInfos = wrappedMethod( playerAttacker );

	witcher = (W3PlayerWitcher)playerAttacker;
	if( !witcher )
		return oilInfos;

	power = witcher.TSSB_Power();
	if( power >= 0.999f )
		return oilInfos;

	if( !witcher.IsSetBonusActive( EISB_Viper1 ) )
		return oilInfos;

	weaponId = witcher.GetInventory().GetCurrentlyHeldWeapon();
	oils     = witcher.GetInventory().GetOilsAppliedOnItem( weaponId );
	if( oils.Size() < 2 )
		return oilInfos;

	// stock: 0.50 base + 0.25 from the set, plus 0.05 per skill level
	// (W3EE - Combat.ws:4188-4190)
	skill = 0.05f * playerAttacker.GetSkillLevel( S_Alchemy_s07 );
	ratio = ( 0.50f + 0.25f * power + skill ) / ( 0.50f + 0.25f + skill );

	n = Min( oilInfos.attributeValues.Size(), oilInfos.attributeValuesOriginal.Size() );
	for( i = 0; i < n; i += 1 )
	{
		oilInfos.attributeValuesOriginal[i] = oilInfos.attributeValuesOriginal[i] * ratio;
		oilInfos.attributeValues[i]         = oilInfos.attributeValues[i]         * ratio;
	}

	return oilInfos;
}


// ---------------------------------------------------------------------------
// Wolf - the adrenaline cap
// ---------------------------------------------------------------------------

@addMethod(W3Effect_CombatAdrenaline)
public function TSSB_RefreshMax()
{
	maxAdrenaline = GetMaximumAdrenaline();
	pointPool = ClampF( pointPool, 0.f, maxAdrenaline );
	currentAdrenaline = ClampF( currentAdrenaline, 0.f, maxAdrenaline );
}

@wrapMethod(W3Effect_CombatAdrenaline) function GetMaximumAdrenaline() : float
{
	var maxAdr : float;

	maxAdr = wrappedMethod();

	if( !playerWitcher )
		return maxAdr;

	if( !playerWitcher.IsSetBonusActive( EISB_Wolf_2 ) )
		return maxAdr;

	// stock returns 150: a flat 50 on top of the base 100. Scale only the 50.
	return maxAdr - 50.f * ( 1.f - playerWitcher.TSSB_Power() );
}


// ---------------------------------------------------------------------------
// Netflix - adrenaline granted per sign cast
//
// Scaled by pre-multiplying the argument rather than correcting afterwards: the
// original clamps at the cap and feeds toxicity back through the gain
// multiplier, so the result is not recoverable from outside.
// The flag window keeps every other caller of AddAdrenalineWithMult untouched.
// ---------------------------------------------------------------------------

@wrapMethod(W3SignEntity) function ManagePlayerStamina()
{
	var witcher : W3PlayerWitcher;

	witcher = (W3PlayerWitcher)( GetActualOwner().GetPlayer() );
	if( witcher )
		witcher.TSSB_signAdr = true;

	wrappedMethod();

	if( witcher )
		witcher.TSSB_signAdr = false;
}

@wrapMethod(W3Effect_CombatAdrenaline) function AddAdrenalineWithMult( value : float )
{
	var v       : float;
	var witcher : W3PlayerWitcher;

	v = value;

	witcher = GetWitcherPlayer();
	if( witcher && witcher.TSSB_signAdr && witcher.IsSetBonusActive(EISB_Netflix_2) )
		v = v * witcher.TSSB_Power();

	wrappedMethod( v );
}


// ---------------------------------------------------------------------------
// Lynx - the debuff put on the enemy
//
// One wrapper fixes both patched lines: the damage multiplier is applied to the
// NPC's own stats, and the animation speed is a product of all causers, so a
// corrective causer lands on exactly the same final value.
// The two arm-injury callers pass 0.9 and must not be touched.
// ---------------------------------------------------------------------------

@wrapMethod(CNewNPC) function CatReduceDamage( amount : float )
{
	var witcher   : W3PlayerWitcher;
	var power, correction : float;

	wrappedMethod( amount );

	if( AbsF( amount - 0.95f ) > 0.001f )
		return;

	witcher = GetWitcherPlayer();
	if( !witcher )
		return;

	if( !witcher.IsSetBonusActive( EISB_Lynx_2 ) )
		return;

	power = witcher.TSSB_Power();
	if( power >= 0.999f )
		return;

	correction = ( 1.f - 0.05f * power ) / 0.95f;

	npcStats.damageValue *= correction;
	SetAnimationSpeedMultiplier( correction );
}


// ---------------------------------------------------------------------------
// Honest tooltips
//
// W3EE builds every set bonus description in code, pushing fixed numbers into a
// localized string. Those numbers know nothing about the scaling, so the Wolf
// tooltip promises 150 while the game gives 120. A wrapper only sees the
// finished string, so the affected descriptions are rebuilt here.
//
// Only the numbers this mod actually scales are touched. The rest are copied
// through untouched - lying in the other direction would be no better.
// ---------------------------------------------------------------------------

@addMethod(W3PlayerWitcher)
public function TSSB_Num( cur : float, grandmaster : float, decimals : int ) : string
{
	var mult : float;
	var now, gm : string;

	mult = PowF( 10.f, decimals );
	now  = NoTrailZeros( ((float)RoundMath( cur * mult )) / mult );

	if( !TSSB_Bool('DescGM', true) || AbsF( cur - grandmaster ) < 0.0001f )
		return now;

	gm = NoTrailZeros( ((float)RoundMath( grandmaster * mult )) / mult );
	return now + " (" + gm + ")";
}

// ⚠️ Ключи ниже объявлены и в modReduxW3EE, и в modW3EE, с РАЗНЫМ числом
// параметров. Наши количества сходятся с версией Redux, которая побеждает по
// порядку загрузки (modReduxW3EE Priority=10 против modW3EE Priority=20; наш
// мод — 15). Поменяется порядок — числа поедут по позициям, и описание станет
// врать хуже, чем если бы мы его не трогали. Число $S$ в каждой строке указано
// рядом с case.
@addMethod(W3PlayerWitcher)
public function TSSB_ScaledDesc( bonus : EItemSetBonus ) : string
{
	var params : array<string>;
	var key, s : string;
	var power, gainMult : float;
	var family : EItemSetType;
	var fullyScaled : bool;
	var adr    : W3Effect_CombatAdrenaline;

	power = TSSB_Power();
	if( power >= 0.999f )
		return "";                  // grandmaster or switched off: stock text is right

	// Rewrite ONLY for a family the player is actually wearing.
	//
	// The game builds this text for ANY item the cursor touches - a shop, a stash,
	// a chest, the crafting preview for something not owned yet - but our strength
	// comes from the gear currently EQUIPPED, not from the item under the cursor.
	// Without this gate, hovering a grandmaster cuirass while wearing tier 1 would
	// promise the tier-1 numbers for an item that gives full strength. That was the
	// most frequent lie in the mod: once per hover, in every menu.
	family = TSSB_BonusToSetType( bonus );
	if( family == EIST_Undefined )
		return "";
	if( GetSetPartsEquipped( family ) <= 0 )
		return "";

	// True only where EVERY number in the sentence is one we scale. Where a
	// description mixes scaled and untouched clauses, the "strength" line at the
	// bottom would be read as applying to all of them - so it is not printed.
	fullyScaled = false;

	switch( bonus )
	{
	case EISB_Lynx_2:               // 1 параметр. Единственная живая величина, ослаблена.
		key = "skill_desc_lynx_set_ability2";
		params.PushBack( TSSB_Num( 5.f * power, 5.f, 2 ) );
		fullyScaled = true;
		break;

	case EISB_Gryphon_1:            // 3 параметра. Ослаблен только первый.
		key = "skill_desc_gryphon_set_ability1";
		params.PushBack( TSSB_Num( 10.f * power, 10.f, 1 ) );
		params.PushBack( "20" );    // регенерация энергии: производящего кода нет вовсе
		params.PushBack( "20" );    // интенсивность: тоже
		break;

	case EISB_Bear_2:               // 4 параметра, все четыре ослаблены.
		key = "skill_desc_bear_set_ability2";
		params.PushBack( TSSB_Num( 0.2f * power, 0.2f, 3 ) );
		params.PushBack( TSSB_Num( 0.3f * power, 0.3f, 3 ) );
		params.PushBack( TSSB_Num( 0.2f * power, 0.2f, 3 ) );
		params.PushBack( TSSB_Num( 0.3f * power, 0.3f, 3 ) );
		fullyScaled = true;
		break;

	case EISB_Wolf_2:               // 2 параметра. Ослаблен только потолок адреналина.
		key = "skill_desc_wolf_set_ability2";
		// Округление вниз: полоска в бою показывает FloorF от потолка, и без
		// этого на 2 и 4 тире описание обещало бы 127.5 против 127 на экране.
		params.PushBack( TSSB_Num( FloorF( 100.f + 50.f * power ), 150.f, 0 ) );
		params.PushBack( "5" );     // срез сопротивления кровотечению: не ослабляется
		break;

	case EISB_Viper1:               // 2 параметра. Ослаблена только потенция масел.
		key = "skill_desc_viper_set_ability2";
		params.PushBack( TSSB_Num( 50.f * power, 50.f, 1 ) );
		params.PushBack( "25" );    // переливание крита: до него из скрипта не дотянуться
		break;

	case EISB_Netflix_2:            // 3 параметра. Ослаблен только адреналин за знак.
		key = "skill_desc_netflix_set_ability2";
		gainMult = 1.f;
		adr = GetAdrenalineEffect();
		if( adr )
			gainMult = MaxF( adr.GetAdrenalineGainMult(), 1.f );
		params.PushBack( TSSB_Num( 5.f * power * gainMult, 5.f * gainMult, 0 ) );
		params.PushBack( "50" );    // зелья и отвары: подмена способности в XML,
		params.PushBack( "100" );   // из скрипта не масштабируется вообще
		break;

	default:
		return "";
	}

	s = GetLocStringByKeyExtWithParams( key,,,params );

	// Строка про силу — только там, где ослаблено ВСЁ предложение. У Грифона,
	// Волка, Гадюки и Netflix часть обещаний работает на полную силу и на первом
	// тире, и общая подпись «40%» прочиталась бы как относящаяся к ним тоже.
	// Хуже всего был бы Netflix: игрок увидел бы 40% над обещанием +50% зельям и
	// +100% отварам, которые на деле приходят целиком.
	if( fullyScaled && TSSB_Bool('DescNote', true) )
		s = s + "<br>" + GetLocStringByKeyExt("tssb_note") + " " + IntToString( RoundMath( power * 100.f ) ) + "%";

	return s;
}

@wrapMethod(W3PlayerWitcher) function GetSetBonusTooltipDescription( bonus : EItemSetBonus ) : string
{
	var scaled : string;

	scaled = TSSB_ScaledDesc( bonus );
	if( scaled != "" )
		return scaled;

	return wrappedMethod( bonus );
}


// ---------------------------------------------------------------------------
// Проверка руками
//
// Без неё правило проверить нечем: тир считается из трёх хранилищ разом, и любая
// ошибка в нём была бы тихой - бонус просто оказался бы не той силы, без единого
// сообщения. В этом проекте тихий сбой - самая частая беда.
// ---------------------------------------------------------------------------

exec function sbttier()
{
	var w     : W3PlayerWitcher;
	var horse : W3HorseManager;
	var cats  : array< name >;
	var best  : array< int >;
	var codes : array< int >;
	var msg   : string;
	var i, j, code : int;

	w = GetWitcherPlayer();
	if( !w ) return;

	codes.PushBack( 1 );
	codes.PushBack( 2 );
	codes.PushBack( 3 );
	codes.PushBack( 4 );
	codes.PushBack( 8 );

	msg = "need " + Options().SetBonusCountSecond();
	if( w.GetHorseManager() )
		msg = msg + "  horse: yes<br>";
	else
		msg = msg + "  horse: NULL<br>";

	for( j = 0; j < codes.Size(); j += 1 )
	{
		code = codes[j];
		cats.Clear();
		best.Clear();

		w.TSSB_CollectTiers( w.GetInventory(), w.TSSB_TagForCode( code ), code, cats, best );
		horse = w.GetHorseManager();
		if( horse )
			w.TSSB_CollectTiers( horse.GetInventoryComponent(), w.TSSB_TagForCode( code ), code, cats, best );

		msg = msg + w.TSSB_TagForCode( code ) + " = " + w.TSSB_OwnedSetTier( code ) + "  [";
		for( i = 0; i < cats.Size(); i += 1 )
			msg = msg + " " + cats[i] + ":" + best[i];
		msg = msg + " ]<br>";
	}

	theGame.GetGuiManager().ShowNotification( msg, 30000 );
}
