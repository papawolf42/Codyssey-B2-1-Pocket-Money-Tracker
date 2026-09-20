# 검증1
def safe_file_reader():
    print("파일 열기, 자원 할당")
    try:
        yield "1번 줄 데이터"
        yield "2번 줄 데이터"
        yield "3번 줄 데이터"
        yield "4번 줄 데이터"
    finally:
        print("finally 발동, 파일 안전하게 닫힘")

print("실험 2개만 읽고, break 탈출하기")

for i, line in enumerate(safe_file_reader(), 1):
    print(f"화면 출력: {line}")
    if i == 2:
        print("2개 읽었으니 break")
        break

print("프로그램 종료")


# 검증2
def stream_categorys():
    try:
        with open("data/categories.jsonl", "r", encoding="utf-8") as f:
            print(f"파일 열림 f.closed:{f.closed}")
            for line in f:
                yield line
    finally:
        print(f"파일 닫힘 f.closed: {f.closed}")

gen = stream_categorys()

item1 = next(gen)
print(f"첫번째 아이템 {item1}")
print("gen.close() 호출")
gen.close()