with open("01_practice.txt", "w", encoding="utf-8") as f:
    f.write("첫 번째 쓰기 연습\n")

with open("01_practice.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content, end="")