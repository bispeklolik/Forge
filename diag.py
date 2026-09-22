# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply as A

d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "patches.json"), encoding="utf-8"))
six = [p for p in d if p.get("step") == 6]
print("правок шага 6 в json:", len(six))

for p in six:
    path = p["file"]
    text, bom, codec = A.read_file(path, p["encoding"])
    b = p["before"]
    n = text.count(b)
    print("\n--- %s  (%s)" % (p["id"], os.path.basename(path)))
    print("    apply.py: вхождений before =", n, "| codec =", codec, "| bom =", bom[:2])

    # как читал сборщик
    raw = open(path, "rb").read()
    if raw[:2] == b"\xff\xfe":
        mine = raw.decode("utf-16")
    else:
        mine = raw.decode("utf-8")
    print("    сборщик : вхождений before =", mine.count(b))
    print("    тексты одинаковы?", text == mine, "| длины:", len(text), len(mine))

    if n == 0:
        # где расходится
        first = b.split("\r\n")[0]
        print("    первая строка before:", repr(first[:70]))
        print("      её вхождений в apply-тексте:", text.count(first))
        print("      её вхождений в моём тексте :", mine.count(first))
        if "\n" in b and "\r\n" not in b:
            print("      ВНИМАНИЕ: в before нет CRLF, только LF")
        print("    первые 3 несовпадающих символа:")
        for k in range(min(len(text), len(mine))):
            if text[k] != mine[k]:
                print("      позиция", k, repr(text[k-20:k+20]), "vs", repr(mine[k-20:k+20]))
                break
        else:
            print("      посимвольных расхождений нет")
