

def generator():
    print("1단계")
    yield "사과"

    print("2단계")
    yield "바나나"

    print("3단계")
    yield "포도"

    print("모든 단계 종료")

print("0. generator 생성")
gen = generator()
print(f"gen: {gen}")

# print("1차 next 호출")
# item1 = next(gen)
# print(f"1번 아이템: {item1}")

# print("2차 next 호출")
# item2 = next(gen)
# print(f"2번 아이템: {item2}")

# print("3차 next 호출")
# item3 = next(gen)
# print(f"3번 아이템: {item3}")

# print("3차 next 호출")
# item3 = next(gen)

for fruit in generator():
    print(f"fruit of this turn is {fruit}")