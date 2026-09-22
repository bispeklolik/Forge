# -*- coding: utf-8 -*-
"""Заводит мод «Честные числа» в описании сборки."""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "spec.py")

LOCS = ["en", "ru", "pl", "de", "fr", "es", "esmx", "it",
        "br", "cz", "hu", "tr", "jp", "kr", "cn", "zh", "ar"]

MOD = '''    dict(
        mod="modW3EERedux_HonestNumbers", group="W3EERedux_HonestNumbers",
        oldmod=None, oldgroup=None, src="HonestNumbers.ws",
        idspace=4479, priority=15, menu_key="hnum_menu",
        title="W3EE Redux - Honest Numbers",
        vars=[
            ("Enabled",    "hnum_enabled",    "TOGGLE", "true"),
            ("SignRows",   "hnum_signrows",   "TOGGLE", "true"),
            ("Durability", "hnum_durability", "TOGGLE", "true"),
        ],
    ),
'''

TR = {
"hnum_menu": [
 "Honest Numbers",
 "Честные числа",
 "Uczciwe Liczby",
 "Ehrliche Zahlen",
 "Chiffres Honnêtes",
 "Cifras Honestas",
 "Cifras Honestas",
 "Numeri Onesti",
 "Números Honestos",
 "Poctivá Čísla",
 "Őszinte Számok",
 "Dürüst Sayılar",
 "正直な数値",
 "정직한 수치",
 "诚实的数值",
 "誠實的數值",
 "أرقام صادقة",
],
"hnum_enabled": [
 "Honest numbers enabled",
 "Честные числа включены",
 "Uczciwe liczby włączone",
 "Ehrliche Zahlen aktiv",
 "Chiffres honnêtes activés",
 "Cifras honestas activadas",
 "Cifras honestas activadas",
 "Numeri onesti attivi",
 "Números honestos ativados",
 "Poctivá čísla zapnuta",
 "Őszinte számok bekapcsolva",
 "Dürüst sayılar açık",
 "正直な数値を有効化",
 "정직한 수치 활성화",
 "启用诚实数值",
 "啟用誠實數值",
 "تفعيل الأرقام الصادقة",
],
"hnum_signrows": [
 "Sign rows: show what each Sign really fires at",
 "Строки знаков: показывать, на чём знак бьёт на самом деле",
 "Wiersze Znaków: pokaż realną moc każdego Znaku",
 "Zeichen-Zeilen: echte Wirkung jedes Zeichens zeigen",
 "Lignes de Signes : afficher la puissance réelle de chaque Signe",
 "Filas de Signos: mostrar la potencia real de cada Signo",
 "Filas de Signos: mostrar la potencia real de cada Signo",
 "Righe dei Segni: mostra la potenza reale di ogni Segno",
 "Linhas de Sinais: mostrar a potência real de cada Sinal",
 "Řádky Znamení: zobrazit skutečnou sílu každého Znamení",
 "Jel-sorok: az egyes jelek valós erejének mutatása",
 "İşaret satırları: her İşaretin gerçek gücünü göster",
 "印の行: 各印の実際の強さを表示",
 "표식 항목: 각 표식의 실제 위력 표시",
 "法印各行: 显示每个法印的真实威力",
 "法印各行: 顯示每個法印的真實威力",
 "صفوف الإشارات: إظهار القوة الحقيقية لكل إشارة",
],
"hnum_durability": [
 "Sword damage: count blade wear, as combat does",
 "Урон мечей: учитывать износ клинка, как в бою",
 "Obrażenia mieczy: uwzględnij zużycie ostrza, jak w walce",
 "Schwertschaden: Klingenabnutzung einrechnen, wie im Kampf",
 "Dégâts des épées : compter l'usure de la lame, comme en combat",
 "Daño de espadas: contar el desgaste de la hoja, como en combate",
 "Daño de espadas: contar el desgaste de la hoja, como en combate",
 "Danno delle spade: conta l'usura della lama, come in combattimento",
 "Dano das espadas: contar o desgaste da lâmina, como em combate",
 "Poškození mečů: započítat opotřebení čepele jako v boji",
 "Kardsebzés: a penge kopásának beszámítása, mint harcban",
 "Kılıç hasarı: savaştaki gibi bıçak aşınmasını hesaba kat",
 "剣のダメージ: 戦闘同様に刃の摩耗を反映",
 "검 피해량: 전투와 동일하게 칼날 마모 반영",
 "剑伤害: 像战斗中一样计入刀刃磨损",
 "劍傷害: 像戰鬥中一樣計入刀刃磨損",
 "ضرر السيوف: احتساب تآكل النصل كما في القتال",
],
}


def main():
    t = io.open(SPEC, encoding="utf-8").read()
    if "modW3EERedux_HonestNumbers" in t:
        print("[--] мод уже описан"); return

    anchor = "    # Чистое исправление бага"
    if t.count(anchor) != 1:
        print("!! якорь не найден"); return
    t = t.replace(anchor, MOD + anchor, 1)

    block = ""
    for key, texts in TR.items():
        block += '"%s": {\n' % key
        for loc, txt in zip(LOCS, texts):
            block += ' "%s": "%s",\n' % (loc, txt)
        block += "},\n\n"
    t = t.replace('"mmpk_menu": {', block + '"mmpk_menu": {', 1)

    tmp = SPEC + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(t)
    os.replace(tmp, SPEC)
    print("[ok] мод и подписи добавлены")

    sys.path.insert(0, HERE)
    import spec
    m = [x for x in spec.MODS if x["mod"] == "modW3EERedux_HonestNumbers"][0]
    print("модов всего:", len(spec.MODS),
          " настроек:", len(m["vars"]),
          " без перевода:", [k for k in spec.keys_of(m) if k not in spec.TR] or "нет")


main()
