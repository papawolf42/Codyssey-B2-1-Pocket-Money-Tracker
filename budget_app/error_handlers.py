import sys
from functools import wraps


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            print(f"[입력 오류] {error}", file=sys.stderr)
            print("[안내] 입력값을 확인해 주세요. 명령어 뒤에 --help를 붙이면 사용법을 볼 수 있습니다.", file=sys.stderr)
            sys.exit(1)

    return wrapper
