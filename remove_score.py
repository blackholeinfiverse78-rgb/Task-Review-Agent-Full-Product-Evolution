with open("evaluation_engine/rule_engine.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("score", "val")
with open("evaluation_engine/rule_engine.py", "w", encoding="utf-8") as f:
    f.write(c)
print("Removed score from rule_engine.py")
