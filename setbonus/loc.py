# -*- coding: utf-8 -*-
"""
Подписи мода на всех 17 языках игры — одно место на оба сборщика.

⚠️ НАЗВАНИЯ КОМПЛЕКТОВ (Кот, Грифон, Темерия…) здесь НЕ переводятся, и это решение,
а не недоделка. В файлах игры чистого названия школы не существует: есть только имена
вещей целиком («Доспех Школы Кота»), из которых слово-название механически не
выдирается — в каждом языке своё склонение. Выдумывать их самому — значит разойтись с
тем, как комплект называется в самой игре, а это хуже английского слова.

Поэтому переводится ОПРАВА: «Рунный камень: …», «Чертёж рунного камня: …» и описания.
Название школы остаётся в английском виде — так, как его знает моддерское сообщество.

Языки: ar br cn cz de en es esmx fr hu it jp kr pl ru tr zh
"""

# Имя камня. %s — название комплекта.
NAME = {
    "ar":   "حجر رونية: %s",
    "br":   "Pedra rúnica: %s",
    "cn":   "符文石：%s",
    "cz":   "Runový kámen: %s",
    "de":   "Runenstein: %s",
    "en":   "Runestone: %s",
    "es":   "Piedra rúnica: %s",
    "esmx": "Piedra rúnica: %s",
    "fr":   "Pierre runique : %s",
    "hu":   "Rúnakő: %s",
    "it":   "Pietra runica: %s",
    "jp":   "ルーン石：%s",
    "kr":   "룬 스톤: %s",
    "pl":   "Kamień runiczny: %s",
    "ru":   "Рунный камень: %s",
    "tr":   "Rün taşı: %s",
    "zh":   "符文石：%s",
}

# Имя чертежа. %s — название комплекта.
SC_NAME = {
    "ar":   "مخطط حجر رونية: %s",
    "br":   "Diagrama de pedra rúnica: %s",
    "cn":   "符文石图纸：%s",
    "cz":   "Nákres runového kamene: %s",
    "de":   "Runenstein-Bauplan: %s",
    "en":   "Runestone diagram: %s",
    "es":   "Diagrama de piedra rúnica: %s",
    "esmx": "Diagrama de piedra rúnica: %s",
    "fr":   "Plan de pierre runique : %s",
    "hu":   "Rúnakő terve: %s",
    "it":   "Progetto di pietra runica: %s",
    "jp":   "ルーン石の図面：%s",
    "kr":   "룬 스톤 도면: %s",
    "pl":   "Rysunek kamienia runicznego: %s",
    "ru":   "Чертёж рунного камня: %s",
    "tr":   "Rün taşı şeması: %s",
    "zh":   "符文石圖紙：%s",
}

# Простое «Чертёж: …» — для заготовки и камня очищения, у которых название уже
# содержит слово «рунный камень». Полная форма SC_NAME дала бы «Чертёж рунного
# камня: Рунный камень очищения».
SC_SIMPLE = {
    "ar":   "مخطط: %s",
    "br":   "Diagrama: %s",
    "cn":   "图纸：%s",
    "cz":   "Nákres: %s",
    "de":   "Bauplan: %s",
    "en":   "Diagram: %s",
    "es":   "Diagrama: %s",
    "esmx": "Diagrama: %s",
    "fr":   "Plan : %s",
    "hu":   "Terv: %s",
    "it":   "Progetto: %s",
    "jp":   "図面：%s",
    "kr":   "도면: %s",
    "pl":   "Rysunek: %s",
    "ru":   "Чертёж: %s",
    "tr":   "Şema: %s",
    "zh":   "圖紙：%s",
}

# Описание камня школы.
DESC = {
    "ar":   "حجر رونية لطقم. ضعه على قطعة مرتداة فتُحتسب ضمن ذلك الطقم كأنها صُنعت له. الحجر لا يُستهلك.",
    "br":   "Pedra rúnica de conjunto. Aplicada a uma peça equipada, faz com que ela conte para esse conjunto, como se tivesse sido forjada para ele. A pedra não é consumida.",
    "cn":   "套装符文石。用于已装备的物品后，该物品将计入这一套装，如同为其锻造。符文石不会被消耗。",
    "cz":   "Runový kámen sady. Použitý na nasazený předmět způsobí, že se počítá do této sady, jako by pro ni byl ukován. Kámen se nespotřebuje.",
    "de":   "Set-Runenstein. Auf ein angelegtes Teil angewendet, zählt dieses fortan zu diesem Set, als wäre es dafür geschmiedet worden. Der Stein wird nicht verbraucht.",
    "en":   "A set runestone. Applied to a worn item, it makes that item count towards that set, as though it had been forged for it. The stone is not consumed.",
    "es":   "Piedra rúnica de conjunto. Aplicada a una pieza equipada, hace que cuente para ese conjunto, como si hubiera sido forjada para él. La piedra no se consume.",
    "esmx": "Piedra rúnica de conjunto. Aplicada a una pieza equipada, hace que cuente para ese conjunto, como si hubiera sido forjada para él. La piedra no se consume.",
    "fr":   "Pierre runique de panoplie. Appliquée à une pièce équipée, elle la fait compter dans cette panoplie, comme si elle avait été forgée pour elle. La pierre n'est pas consommée.",
    "hu":   "Szett-rúnakő. Egy viselt tárgyra alkalmazva az a tárgy ehhez a szetthez fog számítani, mintha hozzá kovácsolták volna. A kő nem használódik el.",
    "it":   "Pietra runica di completo. Applicata a un oggetto indossato, lo fa contare per quel completo, come se fosse stato forgiato per esso. La pietra non viene consumata.",
    "jp":   "セット用のルーン石。装備中の装備に使うと、その装備はこのセットの一部として数えられる。ルーン石は消費されない。",
    "kr":   "세트 룬 스톤. 착용 중인 장비에 사용하면 그 장비가 해당 세트로 계산됩니다. 룬 스톤은 소모되지 않습니다.",
    "pl":   "Kamień runiczny kompletu. Użyty na założonym przedmiocie sprawia, że liczy się on do tego kompletu, jakby został dla niego wykuty. Kamień nie zostaje zużyty.",
    "ru":   "Рунный камень комплекта. Применяется к надетому предмету и делает его частью этого комплекта — как если бы вещь была для него выкована. Камень не тратится.",
    "tr":   "Set rün taşı. Kuşanılmış bir parçaya uygulandığında o parça, sanki bu set için dövülmüş gibi sete dahil sayılır. Taş harcanmaz.",
    "zh":   "套裝符文石。用於已裝備的物品後，該物品將計入這一套裝，如同為其鍛造。符文石不會被消耗。",
}

# Описание чертежа камня.
SC_DESC = {
    "ar":   "مخطط حجر رونية للطقم. يتطلب حجر رونية فارغًا وطقمًا كاملاً بحوزتك. الطقم نفسه لا يُستهلك.",
    "br":   "Diagrama de uma pedra rúnica de conjunto. Requer uma pedra rúnica vazia e um conjunto completo em sua posse. O conjunto em si não é consumido.",
    "cn":   "套装符文石的图纸。需要一枚空白符文石，以及持有一整套该套装。套装本身不会被消耗。",
    "cz":   "Nákres runového kamene sady. Vyžaduje prázdný runový kámen a kompletní sadu ve vlastnictví. Samotná sada se nespotřebuje.",
    "de":   "Bauplan für einen Set-Runenstein. Erfordert einen leeren Runenstein und ein vollständiges Set im Besitz. Das Set selbst wird nicht verbraucht.",
    "en":   "Diagram for a set runestone. Requires an empty runestone and a complete set in your possession. The set itself is not consumed.",
    "es":   "Diagrama de una piedra rúnica de conjunto. Requiere una piedra rúnica vacía y un conjunto completo en tu poder. El conjunto no se consume.",
    "esmx": "Diagrama de una piedra rúnica de conjunto. Requiere una piedra rúnica vacía y un conjunto completo en tu poder. El conjunto no se consume.",
    "fr":   "Plan d'une pierre runique de panoplie. Nécessite une pierre runique vierge et une panoplie complète en votre possession. La panoplie n'est pas consommée.",
    "hu":   "Szett-rúnakő terve. Egy üres rúnakövet és egy teljes szettet igényel a birtokodban. Maga a szett nem használódik el.",
    "it":   "Progetto di una pietra runica di completo. Richiede una pietra runica vuota e un completo intero in tuo possesso. Il completo non viene consumato.",
    "jp":   "セット用ルーン石の図面。空のルーン石と、そのセット一式の所持が必要。セット自体は消費されない。",
    "kr":   "세트 룬 스톤 도면. 빈 룬 스톤과 해당 세트 전체를 소지해야 합니다. 세트 자체는 소모되지 않습니다.",
    "pl":   "Rysunek kamienia runicznego kompletu. Wymaga pustego kamienia runicznego i pełnego kompletu w ekwipunku. Sam komplet nie zostaje zużyty.",
    "ru":   "Чертёж рунного камня комплекта. Требует пустой рунный камень и полный комплект на руках. Сам комплект не расходуется.",
    "tr":   "Set rün taşının şeması. Boş bir rün taşı ve elinizde eksiksiz bir set gerektirir. Setin kendisi harcanmaz.",
    "zh":   "套裝符文石的圖紙。需要一枚空白符文石，以及持有一整套該套裝。套裝本身不會被消耗。",
}

# Заготовка.
EMPTY_NAME = {
    "ar": "حجر رونية فارغ", "br": "Pedra rúnica vazia", "cn": "空白符文石",
    "cz": "Prázdný runový kámen", "de": "Leerer Runenstein", "en": "Empty Runestone",
    "es": "Piedra rúnica vacía", "esmx": "Piedra rúnica vacía",
    "fr": "Pierre runique vierge", "hu": "Üres rúnakő", "it": "Pietra runica vuota",
    "jp": "空のルーン石", "kr": "빈 룬 스톤", "pl": "Pusty kamień runiczny",
    "ru": "Пустой рунный камень", "tr": "Boş rün taşı", "zh": "空白符文石",
}

EMPTY_DESC = {
    "ar":   "قطعة خام بلا خصائص. لا نفع لها بذاتها، لكنها أساس حجر رونية الطقم.",
    "br":   "Uma peça bruta sem propriedades próprias. Inútil por si só, mas é a base de uma pedra rúnica de conjunto.",
    "cn":   "没有任何属性的坯料。本身毫无用处，却是套装符文石的基础。",
    "cz":   "Polotovar bez vlastností. Sám o sobě k ničemu, ale je základem runového kamene sady.",
    "de":   "Ein Rohling ohne eigene Eigenschaften. Für sich nutzlos, aber Grundlage eines Set-Runensteins.",
    "en":   "A blank with no properties of its own. Useless as it is, but it is what a set runestone is made from.",
    "es":   "Una pieza en bruto sin propiedades. Inútil por sí sola, pero es la base de una piedra rúnica de conjunto.",
    "esmx": "Una pieza en bruto sin propiedades. Inútil por sí sola, pero es la base de una piedra rúnica de conjunto.",
    "fr":   "Une ébauche sans propriétés. Inutile telle quelle, mais c'est la base d'une pierre runique de panoplie.",
    "hu":   "Nyers kő, saját tulajdonságok nélkül. Önmagában haszontalan, de ebből készül a szett-rúnakő.",
    "it":   "Un grezzo privo di proprietà. Inutile così com'è, ma è la base di una pietra runica di completo.",
    "jp":   "何の特性も持たない素材。それ自体は役に立たないが、セット用ルーン石の材料となる。",
    "kr":   "아무 속성도 없는 원석. 그 자체로는 쓸모없지만, 세트 룬 스톤의 재료가 됩니다.",
    "pl":   "Półfabrykat bez żadnych właściwości. Sam w sobie bezużyteczny, ale to z niego powstaje kamień runiczny kompletu.",
    "ru":   "Заготовка без свойств. Сама по себе бесполезна, но служит основой для рунного камня комплекта.",
    "tr":   "Kendine ait özelliği olmayan bir taslak. Tek başına işe yaramaz, ama set rün taşı bundan yapılır.",
    "zh":   "沒有任何屬性的坯料。本身毫無用處，卻是套裝符文石的基礎。",
}

# Камень очищения.
CLEAN_NAME = {
    "ar": "حجر رونية للتطهير", "br": "Pedra rúnica de purificação", "cn": "净化符文石",
    "cz": "Očistný runový kámen", "de": "Läuternder Runenstein", "en": "Cleansing Runestone",
    "es": "Piedra rúnica de purificación", "esmx": "Piedra rúnica de purificación",
    "fr": "Pierre runique de purification", "hu": "Tisztító rúnakő",
    "it": "Pietra runica di purificazione", "jp": "浄化のルーン石", "kr": "정화의 룬 스톤",
    "pl": "Oczyszczający kamień runiczny", "ru": "Рунный камень очищения",
    "tr": "Arındırma rün taşı", "zh": "淨化符文石",
}

CLEAN_DESC = {
    "ar":   "يزيل عن القطعة المرتداة الطقم المنقول إليها. طقمها الأصلي، إن وُجد، يعود. الحجر لا يُستهلك.",
    "br":   "Remove de uma peça equipada o conjunto que lhe foi transferido. O conjunto original da peça, se houver, volta. A pedra não é consumida.",
    "cn":   "移除已装备物品上被转移来的套装归属。该物品原本的套装（若有）会恢复。符文石不会被消耗。",
    "cz":   "Odstraní z nasazeného předmětu přenesenou příslušnost k sadě. Vlastní sada předmětu se vrátí. Kámen se nespotřebuje.",
    "de":   "Entfernt von einem angelegten Teil die übertragene Set-Zugehörigkeit. Das eigene Set des Teils kehrt zurück. Der Stein wird nicht verbraucht.",
    "en":   "Strips a transferred set from a worn item. The item's own set, if it had one, comes back. The stone is not consumed.",
    "es":   "Elimina de una pieza equipada el conjunto transferido. El conjunto propio de la pieza, si lo tenía, vuelve. La piedra no se consume.",
    "esmx": "Elimina de una pieza equipada el conjunto transferido. El conjunto propio de la pieza, si lo tenía, vuelve. La piedra no se consume.",
    "fr":   "Retire d'une pièce équipée la panoplie qui lui a été transférée. Sa panoplie d'origine, le cas échéant, revient. La pierre n'est pas consommée.",
    "hu":   "Eltávolítja a viselt tárgyról az átruházott szett-hovatartozást. A tárgy saját szettje, ha volt, visszatér. A kő nem használódik el.",
    "it":   "Rimuove da un oggetto indossato il completo trasferito. Il completo originale dell'oggetto, se presente, ritorna. La pietra non viene consumata.",
    "jp":   "装備中の装備から、移し替えられたセットの所属を取り除く。その装備が元々持っていたセットは戻る。ルーン石は消費されない。",
    "kr":   "착용 중인 장비에서 옮겨 붙인 세트를 제거합니다. 장비 본래의 세트가 있었다면 되돌아옵니다. 룬 스톤은 소모되지 않습니다.",
    "pl":   "Usuwa z założonego przedmiotu przeniesioną przynależność do kompletu. Własny komplet przedmiotu, jeśli go miał, wraca. Kamień nie zostaje zużyty.",
    "ru":   "Снимает с надетой вещи перенесённый сетовый бонус. Собственный комплект вещи при этом возвращается к ней. Камень не тратится.",
    "tr":   "Kuşanılmış bir parçadan aktarılmış set aidiyetini kaldırır. Parçanın kendi seti varsa geri döner. Taş harcanmaz.",
    "zh":   "移除已裝備物品上被轉移來的套裝歸屬。該物品原本的套裝（若有）會恢復。符文石不會被消耗。",
}

# Раздел настроек: ключ -> {язык: подпись}
MENU = {
    "sbt_menu": {
        "ar": "نقل مزايا الأطقم", "br": "Transferência de bônus de conjunto", "cn": "套装加成转移",
        "cz": "Přenos bonusů sad", "de": "Set-Boni übertragen", "en": "Set Bonus Transfer",
        "es": "Transferencia de bonus de conjunto", "esmx": "Transferencia de bonus de conjunto",
        "fr": "Transfert de bonus de panoplie", "hu": "Szettbónusz-átvitel",
        "it": "Trasferimento bonus di completo", "jp": "セットボーナスの移し替え",
        "kr": "세트 보너스 이전", "pl": "Przenoszenie bonusów kompletu",
        "ru": "Перенос сетовых бонусов", "tr": "Set bonusu aktarımı", "zh": "套裝加成轉移",
    },
    "sbt_consume": {
        "ar": "يُستهلك الحجر عند الاستخدام", "br": "A pedra é consumida ao usar", "cn": "使用时消耗符文石",
        "cz": "Kámen se při použití spotřebuje", "de": "Stein wird bei Gebrauch verbraucht",
        "en": "Runestone is consumed on use", "es": "La piedra se consume al usarla",
        "esmx": "La piedra se consume al usarla", "fr": "La pierre est consommée à l'usage",
        "hu": "A kő használatkor elhasználódik", "it": "La pietra si consuma all'uso",
        "jp": "使用時にルーン石を消費する", "kr": "사용 시 룬 스톤 소모",
        "pl": "Kamień zużywa się przy użyciu", "ru": "Камень тратится при использовании",
        "tr": "Taş kullanımda harcanır", "zh": "使用時消耗符文石",
    },
    "sbt_setpieces": {
        "ar": "السماح على قطع الأطقم الأصلية", "br": "Permitir em peças de conjunto originais",
        "cn": "允许用于原本的套装部件", "cz": "Povolit na skutečných dílech sad",
        "de": "Auf echten Set-Teilen erlauben", "en": "Allow on genuine set pieces",
        "es": "Permitir en piezas de conjunto originales", "esmx": "Permitir en piezas de conjunto originales",
        "fr": "Autoriser sur les vraies pièces de panoplie", "hu": "Engedélyezés valódi szettdarabokon",
        "it": "Consenti sui pezzi di completo autentici", "jp": "本来のセット装備にも使用を許可",
        "kr": "원래 세트 장비에도 허용", "pl": "Zezwalaj na oryginalnych częściach kompletu",
        "ru": "Разрешать на вещах из комплектов", "tr": "Gerçek set parçalarında izin ver",
        "zh": "允許用於原本的套裝部件",
    },
    "sbt_swords": {
        "ar": "السماح على السيوف", "br": "Permitir em espadas", "cn": "允许用于剑",
        "cz": "Povolit na mečích", "de": "Auf Schwertern erlauben", "en": "Allow on swords",
        "es": "Permitir en espadas", "esmx": "Permitir en espadas", "fr": "Autoriser sur les épées",
        "hu": "Engedélyezés kardokon", "it": "Consenti sulle spade", "jp": "剣にも使用を許可",
        "kr": "검에도 허용", "pl": "Zezwalaj na mieczach", "ru": "Разрешать на мечах",
        "tr": "Kılıçlarda izin ver", "zh": "允許用於劍",
    },
    "sbt_messages": {
        "ar": "إظهار الرسائل", "br": "Mostrar mensagens", "cn": "显示提示信息",
        "cz": "Zobrazovat zprávy", "de": "Meldungen anzeigen", "en": "Show messages",
        "es": "Mostrar mensajes", "esmx": "Mostrar mensajes", "fr": "Afficher les messages",
        "hu": "Üzenetek megjelenítése", "it": "Mostra i messaggi", "jp": "メッセージを表示",
        "kr": "메시지 표시", "pl": "Pokazuj komunikaty", "ru": "Показывать сообщения",
        "tr": "Mesajları göster", "zh": "顯示提示訊息",
    },
    "sbt_grant": {
        "ar": "منح مخططات الأحجار", "br": "Conceder diagramas das pedras", "cn": "赠予符文石图纸",
        "cz": "Dát nákresy kamenů", "de": "Runenstein-Baupläne aushändigen",
        "en": "Grant runestone diagrams", "es": "Entregar diagramas de las piedras",
        "esmx": "Entregar diagramas de las piedras", "fr": "Fournir les plans des pierres",
        "hu": "Rúnakő-tervek adása", "it": "Fornisci i progetti delle pietre",
        "jp": "ルーン石の図面を渡す", "kr": "룬 스톤 도면 지급",
        "pl": "Przekaż rysunki kamieni", "ru": "Выдавать чертежи камней",
        "tr": "Rün taşı şemalarını ver", "zh": "贈予符文石圖紙",
    },
    "sbt_ownedpower": {
        "ar": "قوة المزية من الطقم الذي تملكه", "br": "Força do bônus pelo conjunto que você tem",
        "cn": "加成强度取决于你已集齐的套装", "cz": "Síla bonusu podle sady, kterou vlastníš",
        "de": "Bonusstärke nach dem Set, das du besitzt", "en": "Bonus strength from the set you own",
        "es": "Fuerza del bonus según el conjunto que posees",
        "esmx": "Fuerza del bonus según el conjunto que posees",
        "fr": "Puissance du bonus selon la panoplie possédée",
        "hu": "A bónusz ereje a birtokolt szett szerint",
        "it": "Forza del bonus dal completo che possiedi", "jp": "ボーナスの強さは所持セットに準じる",
        "kr": "보너스 강도는 보유한 세트에 따름", "pl": "Siła bonusu wg posiadanego kompletu",
        "ru": "Сила бонуса — по собранному комплекту", "tr": "Bonus gücü sahip olduğun sete göre",
        "zh": "加成強度取決於你已集齊的套裝",
    },
}


def pick(table, loc, fallback="en"):
    """Подпись на нужном языке; если её нет — английская."""
    return table.get(loc, table.get(fallback, ""))


# Бонусы школ — ДВЕ таблицы, потому что Redux ПЕРЕПИСЫВАЕТ сетовые бонусы целиком:
# ванильный Грифон — это Ирден и знаки, редуксовый — снижение сопротивлений эфирным
# уроном. Одна таблица на обе сборки врала бы одной из них (пойман пользователем по
# скриншоту). Числа намеренно НЕ называются: они зависят от тира, порогов и мода
# тиров, любое конкретное число тут лгало бы.
#
# Ванильные тексты — по строкам базовой игры (1177852 Кот, 1177855 Грифон, 1177857
# Медведь, 1177864 Волк, 1177866 Мантикора, 1212115 Вампир).
SCHOOL_BONUS_VANILLA = {
    "sbt_st_feline": {
        "ru": "Бонус: удары в спину бьют сильнее и оглушают, тратя адреналин.",
        "en": "Bonus: attacks from behind hit harder and stun, spending adrenaline.",
    },
    "sbt_st_griffin": {
        "ru": "Бонус: ловушки Ирден шире, а внутри них быстрее копится энергия, "
              "мощнее знаки и слабее входящий урон.",
        "en": "Bonus: Yrden traps are wider; inside them stamina regenerates faster, "
              "signs hit harder and incoming damage is reduced.",
    },
    "sbt_st_ursine": {
        "ru": "Бонус: умения, связанные со Знаком Квен, наносят больше урона.",
        "en": "Bonus: Quen-related skills deal more damage.",
    },
    "sbt_st_wolven": {
        "ru": "Бонус: каждое кровотечение на противнике добавляет урона мечу — "
              "тем больше, чем больше частей комплекта надето.",
        "en": "Bonus: every bleeding effect on the enemy adds sword damage — "
              "more for each set piece worn.",
    },
    "sbt_st_manticore": {
        "ru": "Бонус: у всех алхимических предметов больше зарядов.",
        "en": "Bonus: every alchemy item gets extra charges.",
    },
    "sbt_st_vampire": {
        "ru": "Бонус: убийство противника восстанавливает здоровье — "
              "тем больше, чем больше частей комплекта надето.",
        "en": "Bonus: killing an enemy restores health — more for each set piece worn.",
    },
    "sbt_st_viper": {
        "ru": "⚠️ В ванильной игре у этого комплекта сетового бонуса нет вовсе — "
              "камень пометит вещь, но бонуса не даст.",
        "en": "Note: in the vanilla game this set has no set bonus at all — the stone "
              "will mark the item, but there is nothing to grant.",
    },
    "sbt_st_netflix": {
        "ru": "Бонус: знаки возвращают адреналин, а зелья и отвары действуют сильнее.",
        "en": "Bonus: signs give back adrenaline, and potions and decoctions are stronger.",
    },
}




# Редуксовые тексты — по строкам modReduxW3EE (skill_desc_<школа>_set_ability1/2,
# сопоставление ключей к хешам сделано САМИМ кодировщиком w3strings: закодировали
# ключи-кандидаты, декодировали обратно, получили их хеши — приём «оракул хешей»).
SCHOOL_BONUS_REDUX = {
    "sbt_st_feline": {
        "ru": "Бонус: после уклонения атаки бьют в спину больнее и калечат, а "
              "увечье замедляет и ослабляет противника.",
        "en": "Bonus: after a dodge your attacks hit harder from behind and maim; "
              "a maimed enemy is slower and weaker.",
    },
    "sbt_st_griffin": {
        "ru": "Бонус: эфирный урон навсегда снижает сопротивления противника, а "
              "внутри круга Ирдена — замедление времени, энергия и мощь знаков.",
        "en": "Bonus: elemental damage permanently strips enemy resistances; inside "
              "your Yrden circle — slowed time, stamina regen and sign power.",
    },
    "sbt_st_ursine": {
        "ru": "Бонус: парирование ломает стойкость врага и возвращает выносливость, "
              "а собственная стойкость ослабляет пробитие брони и входящий урон.",
        "en": "Bonus: parries break enemy poise and restore stamina; your own poise "
              "blunts armour piercing and incoming damage.",
    },
    "sbt_st_wolven": {
        "ru": "Бонус: кровотечения дают адреналин, избыток адреналина лечит и "
              "возвращает выносливость, а его потолок выше.",
        "en": "Bonus: bleeds generate adrenaline, excess adrenaline heals and "
              "restores stamina, and its cap is raised.",
    },
    "sbt_st_manticore": {
        "ru": "Бонус: дальний урон и сила атаки растут за каждый эффект статуса на "
              "враге, а эффекты интоксикации считаются от её полного значения.",
        "en": "Bonus: ranged damage and attack power grow per status effect on the "
              "enemy; toxicity effects use its absolute value.",
    },
    "sbt_st_vampire": {
        "ru": "Бонус: враги в ближнем бою могут получить кровотечение, а убийство "
              "кровоточащего врага восстанавливает здоровье.",
        "en": "Bonus: melee attackers may start bleeding, and killing a bleeding "
              "enemy restores health.",
    },
    "sbt_st_viper": {
        "ru": "Бонус: шанс критического удара растёт за каждый стак отравления "
              "(Аксий их накладывает), и на клинок ложится дополнительное масло.",
        "en": "Bonus: crit chance grows per poison stack (Axii applies them), and "
              "your blade holds an extra oil.",
    },
    "sbt_st_netflix": {
        "ru": "Бонус: адреналин восстанавливает энергию, знаки приносят адреналин, "
              "а зелья и отвары действуют сильнее.",
        "en": "Bonus: adrenaline restores stamina, signs generate adrenaline, and "
              "potions and decoctions are stronger.",
    },
}


def bonus_line(key, loc, vanilla=False):
    """Строка про бонус школы — из СВОЕЙ таблицы для каждой сборки. Кроме русского —
    английская: тексты писались по строкам игры, переводить их самому значило бы
    разойтись с ними."""
    table = SCHOOL_BONUS_VANILLA if vanilla else SCHOOL_BONUS_REDUX
    tbl = table.get(key)
    if not tbl:
        return ""
    return tbl.get("ru" if loc == "ru" else "en", "")
