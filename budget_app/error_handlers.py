import sys
from functools import wraps


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            print(f"[오류] {error}", file=sys.stderr)
            print("[힌트] 입력값의 형식과 범위를 확인해 주세요. --help에서 사용법을 볼 수 있습니다.", file=sys.stderr)
            sys.exit(1)
        except OSError as error:
            print(f"[오류] 파일을 읽거나 쓸 수 없습니다: {error}", file=sys.stderr)
            print("[힌트] 데이터 경로와 파일 접근 권한을 확인해 주세요.", file=sys.stderr)
            sys.exit(1)
        except Exception as error:
            print(f"[오류] 예기치 않은 오류가 발생했습니다: {error}", file=sys.stderr)
            print("[힌트] 입력값과 데이터 파일을 확인한 뒤 다시 시도해 주세요.", file=sys.stderr)
            sys.exit(1)

    return wrapper
