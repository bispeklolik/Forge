# -*- coding: utf-8 -*-
"""
Переписывает подписи настроек так, чтобы их понимал человек, не писавший мод.

Правило: каждая строка отвечает на три вопроса — ЧЬЯ это настройка (мутация,
знак, комплект), ЧТО произойдёт, и ЧТО означают числа. В меню игры всплывающих
подсказок нет, поэтому подпись обязана быть самодостаточной.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LOCS = ["en", "ru", "pl", "de", "fr", "es", "esmx", "it",
        "br", "cz", "hu", "tr", "jp", "kr", "cn", "zh", "ar"]

NEW = {

"insc_rate": [
 "Insectoid: toxicity burn rate (10 = as coded, 25 = as described)",
 "Инсектоид: скорость снятия токсичности (10 — как в игре, 25 — как в описании)",
 "Insektoid: tempo usuwania toksyczności (10 = jak w kodzie, 25 = jak w opisie)",
 "Insektoid: Tempo des Toxizitätsabbaus (10 = wie im Code, 25 = wie beschrieben)",
 "Insectoïde : vitesse de purge de toxicité (10 = réel, 25 = annoncé)",
 "Insectoide: velocidad de purga de toxicidad (10 = real, 25 = descrito)",
 "Insectoide: velocidad de purga de toxicidad (10 = real, 25 = descrito)",
 "Insettoide: velocità di rimozione tossicità (10 = reale, 25 = dichiarato)",
 "Insetoide: velocidade de remoção de toxicidade (10 = real, 25 = descrito)",
 "Hmyzák: rychlost odbourávání toxicity (10 = skutečnost, 25 = popis)",
 "Rovar: méregtelenítés sebessége (10 = valós, 25 = leírt)",
 "Böceksi: toksisite giderme hızı (10 = kodda, 25 = açıklamada)",
 "インセクトイド: 毒性の除去速度 (10 = 実際, 25 = 説明どおり)",
 "곤충형: 독성 제거 속도 (10 = 실제, 25 = 설명대로)",
 "虫类: 毒性清除速度 (10 = 实际, 25 = 描述值)",
 "蟲類: 毒性清除速度 (10 = 實際, 25 = 描述值)",
 "الحشري: سرعة إزالة السمية (10 = الفعلي، 25 = الموصوف)",
],

"mutf_fixdesc": [
 "Show real numbers in mutation descriptions",
 "Показывать в описаниях мутаций настоящие числа",
 "Pokaż prawdziwe liczby w opisach mutacji",
 "Echte Zahlen in Mutationsbeschreibungen zeigen",
 "Afficher les vrais chiffres dans les descriptions de mutations",
 "Mostrar cifras reales en las descripciones de mutaciones",
 "Mostrar cifras reales en las descripciones de mutaciones",
 "Mostra i valori reali nelle descrizioni delle mutazioni",
 "Mostrar números reais nas descrições das mutações",
 "Zobrazit skutečná čísla v popisech mutací",
 "Valós számok a mutációk leírásában",
 "Mutasyon açıklamalarında gerçek sayıları göster",
 "変異の説明に実際の数値を表示",
 "돌연변이 설명에 실제 수치 표시",
 "在突变描述中显示真实数值",
 "在突變描述中顯示真實數值",
 "إظهار الأرقام الحقيقية في أوصاف الطفرات",
],

"insc_dmgredon": [
 "Insectoid: restore the removed damage reduction",
 "Инсектоид: вернуть вырезанное снижение урона",
 "Insektoid: przywróć usuniętą redukcję obrażeń",
 "Insektoid: entfernte Schadensreduktion zurückholen",
 "Insectoïde : rétablir la réduction de dégâts supprimée",
 "Insectoide: restaurar la reducción de daño eliminada",
 "Insectoide: restaurar la reducción de daño eliminada",
 "Insettoide: ripristina la riduzione danni rimossa",
 "Insetoide: restaurar a redução de dano removida",
 "Hmyzák: obnovit odstraněné snížení poškození",
 "Rovar: az eltávolított sebzéscsökkentés visszaállítása",
 "Böceksi: kaldırılan hasar azaltmayı geri getir",
 "インセクトイド: 削除されたダメージ軽減を復活",
 "곤충형: 삭제된 피해 감소 복원",
 "虫类: 恢复被移除的伤害减免",
 "蟲類: 恢復被移除的傷害減免",
 "الحشري: إعادة تقليل الضرر المحذوف",
],

"insc_dmgredperc": [
 "   ...how much weaker repeat hits are, %",
 "   ...насколько слабее бьют повторные удары, %",
 "   ...o ile słabsze są kolejne trafienia, %",
 "   ...wie viel schwächer Folgetreffer sind, %",
 "   ...combien les coups suivants sont plus faibles, %",
 "   ...cuánto más débiles son los golpes seguidos, %",
 "   ...cuánto más débiles son los golpes seguidos, %",
 "   ...quanto sono più deboli i colpi successivi, %",
 "   ...quanto mais fracos ficam os golpes seguintes, %",
 "   ...o kolik slabší jsou další zásahy, %",
 "   ...mennyivel gyengébbek az ismételt találatok, %",
 "   ...tekrar eden vuruşlar ne kadar zayıf, %",
 "   ...連続被弾がどれだけ弱まるか, %",
 "   ...연속 피격이 얼마나 약해지는지, %",
 "   ...连续受击减弱多少, %",
 "   ...連續受擊減弱多少, %",
 "   ...كم تضعف الضربات المتكررة، %",
],

"insc_dmgredwin": [
 "   ...how many seconds it lasts",
 "   ...сколько секунд это держится",
 "   ...ile sekund to trwa",
 "   ...wie viele Sekunden es anhält",
 "   ...combien de secondes cela dure",
 "   ...cuántos segundos dura",
 "   ...cuántos segundos dura",
 "   ...quanti secondi dura",
 "   ...quantos segundos dura",
 "   ...kolik sekund to trvá",
 "   ...hány másodpercig tart",
 "   ...kaç saniye sürer",
 "   ...何秒間続くか",
 "   ...몇 초 동안 지속되는지",
 "   ...持续多少秒",
 "   ...持續多少秒",
 "   ...كم ثانية يستمر",
],

"mutf_signbypass": [
 "Specter: raise the Sign bonus toward the promised +50% (0 = as in game)",
 "Призрак: доводить бонус знаков до обещанных +50% (0 — как в игре)",
 "Zjawa: podnieś premię do Znaków do obiecanych +50% (0 = jak w grze)",
 "Spektral: Zeichen-Bonus auf die versprochenen +50% anheben (0 = wie im Spiel)",
 "Spectre : porter le bonus de Signes aux +50% promis (0 = tel quel)",
 "Espectro: elevar la bonificación de Signos al +50% prometido (0 = como está)",
 "Espectro: elevar la bonificación de Signos al +50% prometido (0 = como está)",
 "Spettro: porta il bonus ai Segni al +50% promesso (0 = come nel gioco)",
 "Espectro: elevar o bônus de Sinais aos +50% prometidos (0 = como está)",
 "Přízrak: zvýšit bonus ke Znamením na slíbených +50% (0 = jako ve hře)",
 "Kísértet: a jelbónusz emelése az ígért +50%-ra (0 = ahogy a játékban)",
 "Hayalet: İşaret bonusunu vaat edilen +50% düzeyine çıkar (0 = oyundaki gibi)",
 "スペクター: 印の効果を約束の+50%に近づける (0 = ゲームのまま)",
 "스펙터: 표식 보너스를 약속된 +50%까지 상향 (0 = 게임 그대로)",
 "幽灵: 将法印加成提升至承诺的 +50% (0 = 保持原样)",
 "幽靈: 將法印加成提升至承諾的 +50% (0 = 保持原樣)",
 "الطيف: رفع مكافأة الإشارات إلى +50% الموعودة (0 = كما في اللعبة)",
],

"ssht_shatterscale": [
 "   ...how fast the chance grows with wounds (100 = normal)",
 "   ...насколько быстро шанс растёт с ранами (100 — обычно)",
 "   ...jak szybko szansa rośnie z ranami (100 = normalnie)",
 "   ...wie schnell die Chance mit Wunden steigt (100 = normal)",
 "   ...à quelle vitesse la chance croît avec les blessures (100 = normal)",
 "   ...con qué rapidez crece la probabilidad con las heridas (100 = normal)",
 "   ...con qué rapidez crece la probabilidad con las heridas (100 = normal)",
 "   ...quanto in fretta cresce la probabilità con le ferite (100 = normale)",
 "   ...quão rápido a chance cresce com os ferimentos (100 = normal)",
 "   ...jak rychle šance roste se zraněním (100 = normálně)",
 "   ...milyen gyorsan nő az esély a sebekkel (100 = normál)",
 "   ...şans yaralarla ne kadar hızlı artar (100 = normal)",
 "   ...傷が増えるほど確率が上がる速さ (100 = 標準)",
 "   ...부상에 따라 확률이 오르는 속도 (100 = 보통)",
 "   ...概率随伤势增长的速度 (100 = 正常)",
 "   ...機率隨傷勢增長的速度 (100 = 正常)",
 "   ...سرعة نمو الفرصة مع الجراح (100 = عادي)",
],

}


def main():
    p = os.path.join(HERE, "spec.py")
    t = io.open(p, encoding="utf-8").read()
    done, missing = 0, []

    for key, texts in NEW.items():
        if len(texts) != len(LOCS):
            missing.append(key + " (не 17 строк)"); continue
        m = re.search(r'"%s": \{.*?\n\},\n' % re.escape(key), t, re.S)
        if not m:
            missing.append(key + " (не найден)"); continue
        block = '"%s": {\n' % key
        for loc, txt in zip(LOCS, texts):
            if "|" in txt:
                missing.append(key + "/" + loc + " (вертикальная черта)"); continue
            block += ' "%s": "%s",\n' % (loc, txt)
        block += "},\n"
        t = t[:m.start()] + block + t[m.end():]
        done += 1

    # ⛔ писать только через временный файл: открытие на 'w' стирает оригинал
    tmp = p + ".tmp"
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(t)
    os.replace(tmp, p)

    print("переписано ключей:", done)
    print("проблемы:", missing or "нет")

    import spec
    bad = [(k, l) for k in NEW for l in spec.LOCALES if not spec.TR[k].get(l)]
    print("пропущенных локалей:", bad or "нет")
    print()
    print("=== как теперь выглядит меню «Починка мутаций» ===")
    m = [x for x in spec.MODS if x["mod"] == "modW3EERedux_Mutations"][0]
    print("   %s" % spec.TR[m["menu_key"]]["ru"])
    for vid, key, dt, default in m["vars"]:
        print("   %-6s %s" % (default, spec.TR[key]["ru"]))


main()
