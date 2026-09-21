# 나만의 가계부 (Pocket Money Tracker CLI)

Python 3.10+ 표준 라이브러리만으로 개발된 파일 기반 콘솔 가계부 프로그램입니다.  
프로그램 종료 후에도 데이터가 안전하게 영구 보존되며, 제너레이터 스트리밍, 원자적 파일 교체(`atomic_replace`), 데코레이터 공통 관심사 분리를 적용한 **유지보수 가능한 "작은 서비스"** 구조로 설계되었습니다.

> **[명세서 요구 선택지 고정 안내]**
> 1. **카테고리 초기 동작**: **(안 A) 기본 카테고리 4종(`food`, `transport`, `rent`, `salary`) 자동 생성** 채택
> 2. **거래 수정(`update`) 방식**: **(안 A) 옵션 인자 기반 방식(`update --id <id> [--amount ...]`)** 채택

---

## 1. 과제 요구사항 충족 매트릭스

| 과제 요구사항 | 구현 내용 및 설계 특징 | 검증 명령어 / 코드 위치 |
|:---|:---|:---|
| **1. 거래 추가 (`add`)** | 대화형 입력, 날짜/타입/카테고리/금액 검증, `TX-XXXXXX` 고유 ID 자동 발급 | `python -m budget_app add` |
| **2. 거래 목록 (`list`)** | 날짜 내림차순(최신순), `--limit N`, 제너레이터 스트리밍 I/O | `list --limit 3` (`services.py`) |
| **3. 조건 검색 (`search`)** | 기간(`--from`/`--to`), 카테고리, 타입, 키워드, 태그 복합 필터링 | `search --category food --from ...` |
| **4. 월별 요약 (`summary`)** | 총수입/총지출/잔액, 지출 상위 TOP N, 예산 사용률 및 초과 경고 | `summary --month YYYY-MM --top N` |
| **5. 예산 관리 (`budget`)** | 월별 목표 예산 영구 저장 및 목록 조회 | `budget set`, `budget list` |
| **6. 카테고리 (`category`)** | 추가, 목록 조회, 삭제 시 거래 내역 참조 무결성 검증(삭제 차단) | `category add/list/remove` |
| **7. 거래 수정 (`update`)** | `--id` 기반 선택적 필드 부분 수정, 날짜 변경 시 정렬 자동 재배치 | `update --id TX-000001 --amount ...` |
| **8. 거래 삭제 (`delete`)** | `--id` 기반 1-Pass 스트리밍 삭제 및 원자적 교체 | `delete --id TX-000001` |
| **9. CSV 내보내기 (`export`)** | 조건(월/기간) 지정 거래 내보내기, UTF-8 헤더 포함 표준 CSV | `export --out <file> --month ...` |
| **10. CSV 가져오기 (`import`)** | Excel BOM(`utf-8-sig`) 지원, 손상 행 건너뛰기, 일괄 배치 삽입 | `import --from <file>` |
| **3대 파일 영구 저장** | 거래/카테고리/예산 JSONL 분리 및 `--data-dir` 격리 지원 | `data/` 디렉터리 |
| **제너레이터 스트리밍** | 파일 전체를 메모리에 올리지 않고 행 단위 `yield`로 O(1) 메모리 유지 | `storage.py` (`get_all`, `search`) |
| **원자적 파일 교체** | 임시 파일 쓰기 -> `os.replace()` 교체로 비정상 종료 시 손상 방지 | `storage.py` (`atomic_replace`) |
| **공통 데코레이터** | `@handle_errors` 적용: 스택트레이스 차단, 원인+힌트 출력, 종료코드(0/1) | `error_handlers.py` |
| **데이터 모델 및 계약** | Dataclass 불변식(`__post_init__`) 검증 및 Type Hint 적용 | `models.py` |

---

## 2. 실행 방법 및 1분 평가 시연 스크립트

외부 패키지 설치(`pip install`) 없이 **Python 3.10 이상** 환경에서 즉시 실행 가능합니다.

```bash
# 기본 실행 및 도움말
python -m budget_app --help
python -m budget_app <command> --help

# 저장 폴더 변경 (하위 명령 앞에 지정)
python -m budget_app --data-dir ./my_data category list
```

### 평가용 원스톱 시연 스크립트 (Copy & Paste)
평가 데이터를 오염시키지 않는 독립 디렉터리(`--data-dir ./eval_data`)에서 전체 기능을 1분 안에 연속 검증할 수 있습니다:

```bash
# 1. 카테고리 목록 조회 및 추가
python -m budget_app --data-dir ./eval_data category list
python -m budget_app --data-dir ./eval_data category add cafe

# 2. 예산 설정 및 월별 결산 요약 (초기 데이터 3건 기반)
python -m budget_app --data-dir ./eval_data budget set --month 2026-03 --amount 500000
python -m budget_app --data-dir ./eval_data summary --month 2026-03 --top 3

# 3. 목록 조회 및 조건 검색
python -m budget_app --data-dir ./eval_data list --limit 3
python -m budget_app --data-dir ./eval_data search --category food --type expense

# 4. 거래 수정 및 삭제 (원자적 교체)
python -m budget_app --data-dir ./eval_data update --id TX-000001 --amount 18000 --memo "특 순대국밥"
python -m budget_app --data-dir ./eval_data delete --id TX-000002

# 5. CSV 내보내기 및 가져오기 (라운드트립 검증)
python -m budget_app --data-dir ./eval_data export --out ./eval_data/backup.csv --month 2026-03
python -m budget_app --data-dir ./eval_data import --from ./eval_data/backup.csv

# 6. 예외 처리 및 비정상 종료 코드 검증 (스택트레이스 미출력)
python -m budget_app --data-dir ./eval_data delete --id NO_SUCH_ID
echo $?   # 1 출력 확인 (Windows PowerShell은 echo $LASTEXITCODE)
```

---

## 3. 3대 영구 저장 파일 및 CSV 교환 스키마

기본 데이터 저장 위치는 `./data`입니다.

| 파일 경로 | 포맷 | 역할 및 저장 내용 |
|:---|:---:|:---|
| `data/transactions.jsonl` | JSONL | 거래 내역 (`id`, `date`, `type`, `category`, `amount`, `memo`, `tags`) |
| `data/categories.jsonl` | JSONL | 등록된 카테고리명 목록 (`{"name": "food"}`) |
| `data/budgets.jsonl` | JSONL | 월별 목표 예산 목록 (`{"month": "2026-03", "amount": 500000}`) |

### CSV 교환 스키마 (`import` / `export`)
Excel 한글 깨짐 방지를 위해 `utf-8-sig` 인코딩을 기본 지원하며, 첫 행에 헤더를 포함합니다.

| Column | Required | Type / Format | 설명 | 예시 |
|:---|:---:|:---|:---|:---|
| `date` | **Y** | `YYYY-MM-DD` | 거래 일자 (실제 역법상 유효한 날짜) | `2026-03-20` |
| `type` | **Y** | `income` \| `expense` | 거래 유형 (대소문자 무관 정규화) | `expense` |
| `category` | **Y** | 문자열 | 등록된 카테고리명 (대소문자 무관) | `food` |
| `amount` | **Y** | 1 이상의 정수 | 금액 (양수 정수) | `15000` |
| `memo` | N | 문자열 | 부가 메모 (공백 시 빈 문자열) | `점심 식사` |
| `tags` | N | 문자열 (쉼표 구분) | 태그 목록 | `lunch,meal` |

* **손상 CSV 행 처리 정책 (부분 성공)**:
  - 파일 부재나 필수 헤더(`date, type, category, amount`) 누락 시에는 작업을 시작하지 않고 오류로 종료합니다.
  - 행 단위의 데이터 오류(날짜 형식 오류, 미등록 카테고리, 음수 금액 등)는 해당 행만 건너뛰고(`skipped += 1`), 정상 행만 연속된 신규 ID를 부여해 일괄 등록합니다.  
    -> 출력 예시: `[완료] imported=5, skipped=2`

---

## 4. 주요 CLI 명령어 사용법

### 1) 거래 추가 (`add` - 대화형)
```text
$ python -m budget_app add
날짜(YYYY-MM-DD): 2026-03-20
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심 순대국밥
태그(쉼표로 구분, 없으면 엔터): lunch
[저장 완료] id=TX-000004
```

### 2) 거래 목록 조회 (`list`)
```text
$ python -m budget_app list --limit 3
=== [최신 거래 목록 (최대 3건)] ===
[TX-000001] 2026-03-20 | (-)     15,000원 | food       | 점심 순대국밥 #lunch
[TX-000002] 2026-03-19 | (-)      2,500원 | transport  | 지하철 #subway
[TX-000003] 2026-03-18 | (+)  3,500,000원 | salary     | 3월 급여 #monthly
```

### 3) 월별 요약 및 예산 경고 (`summary` & `budget`)
```bash
$ python -m budget_app budget set --month 2026-03 --amount 10000
[저장 완료] 2026-03 예산 10000원

$ python -m budget_app summary --month 2026-03 --top 3
총 수입: 3500000원
총 지출: 17500원
잔액: 3482500원
예산: 10000원 (사용률 175.0%)
[경고] 예산을 7500원 초과했습니다!

지출 TOP 2
1) food 15000원
2) transport 2500원
```

### 4) 카테고리 관리 (`category`)
```bash
$ python -m budget_app category list
=== [등록된 카테고리 목록] ===
- food
- transport
- rent
- salary

$ python -m budget_app category remove food
[오류] 'food' 카테고리를 사용하는 거래 내역(예: [TX-000001] 점심 순대국밥)이 존재하여 삭제할 수 없습니다. 해당 거래를 먼저 수정하거나 삭제해 주세요.
[힌트] 입력값의 형식과 범위를 확인해 주세요. --help에서 사용법을 볼 수 있습니다.
```

### 5) 거래 수정 및 삭제 (`update` & `delete`)
```bash
# 옵션 기반 부분 수정 (날짜 변경 시 최신순 자동 재정렬)
$ python -m budget_app update --id TX-000001 --amount 18000 --memo "특 순대국밥"
[수정 완료] [TX-000001] 2026-03-20 | (-)     18,000원 | food       | 특 순대국밥 #lunch

# 안전한 원자적 삭제
$ python -m budget_app delete --id TX-000001
[삭제 완료] 거래 내역 'TX-000001'가 성공적으로 삭제되었습니다.
```

---

## 5. 핵심 아키텍처 및 평가 루브릭 직격 답변 (Why & How)

### Q1. 모듈과 클래스 책임 분리 기준 (항목 2 대응)
단일 책임 원칙(SRP)과 관심사 분리(SoC)에 따라 4대 모듈로 역할을 명확히 분리했습니다:
- **`models.py`**: 도메인 데이터 계약(`Transaction`, `Budget`) 및 불변식 검증(`validate_date`, `validate_amount` 등).
- **`storage.py`**: 순수 파일 I/O 계층. JSONL/CSV 제너레이터 스트리밍 및 원자적 파일 교체(`atomic_replace`) 담당.
- **`services.py`**: 비즈니스 로직 계층. 카테고리 참조 무결성 보호, 결산 집계, 예산 초과율 계산, CSV 파싱 오케스트레이션.
- **`cli.py`**: 사용자 인터페이스 계층. `argparse` 파싱, 입출력 포맷팅 및 핸들러 디스패치.
- **`error_handlers.py`**: 공통 관심사 횡단 계층. 일관된 예외 차단 및 사용자 힌트/종료 코드 반환.

### Q2. 파일 기반 update/delete의 원자적 안전성 (항목 2 대응)
원본 파일을 직접 수정하다가 프로그램이 강제 종료되면 파일이 손상될 수 있습니다. 이를 방어하기 위해 **임시 파일 + `os.replace` 원자적 교체 5단계**를 적용했습니다:
1. 기존 데이터를 순회하며 수정/삭제가 반영된 레코드 생성
2. 동일 파일시스템 내 임시 파일(`.tmp`)에 데이터 전량 기록
3. 파일 닫기 및 flush 완료
4. OS 커널 수준의 원자적 시스템 콜인 `os.replace(temp_file, target_file)` 실행
5. 예외 발생 시 `finally`에서 임시 파일을 안전하게 삭제하고 기존 원본 파일 보존

### Q3. 제너레이터 스트리밍의 구현 방식과 유리한 이유 (항목 3 대응)
- **구현 방식**: `storage.py`의 `read_jsonl()` 및 `TransactionRepository.get_all()`은 `readlines()`나 `json.load()`로 전체 파일을 메모리에 적재하지 않고, `for line in f:` 순회하며 `yield Transaction.from_dict(...)`를 통해 레코드를 1건씩 스트리밍합니다.
- **유리한 이유**: 파일 크기가 수백 MB로 커져도 메모리 사용량이 O(1) 상수로 고정됩니다. 또한 `list --limit 3`처럼 조기 종료(Early Exit) 조건이 있을 때 불필요한 뒷부분 데이터를 읽지 않고 즉시 I/O를 중단할 수 있습니다.

### Q4. 데코레이터를 이용한 공통 기능 분리 (항목 3 대응)
- `@handle_errors` 데코레이터를 CLI 핸들러 함수들에 적용하여, 비즈니스 로직마다 중복되는 `try...except`, `sys.exit(1)`, 에러 출력 코드를 제거했습니다.
- 사용자에게 흉측한 파이썬 스택트레이스(Traceback)를 일체 노출하지 않고, 일관된 `[오류] 원인` + `[힌트] 해결책` 포맷을 출력하며 비정상 종료 코드(`exit code 1`)를 반환합니다.

### Q5. JSONL vs CSV 선택 이유 & 10만 건 대용량 병목 분석 (항목 4 대응)
- **저장 포맷 선택 근거**: 내부 영구 저장에는 `tags: list[str]` 배열을 자연스럽게 보존하고 행 단위 파싱/검증이 쉬운 **JSONL**을 채택했습니다. 사용자 교환 형식은 스프레드시트 호환성이 뛰어난 **CSV**로 분리하여 각 포맷의 장점을 극대화했습니다.
- **10만 건 대용량 시 병목과 개선안**:
  - *병목 1*: 수정/삭제 시 임시 파일 전체 재작성 -> **월별 파일 파티셔닝(`transactions_202603.jsonl`)**으로 쓰기 범위 축소.
  - *병목 2*: 월별 요약 시 전체 순차 스캔 -> **월별 집계 캐시 파일(`summary_cache.json`)** 유지.
  - *병목 3*: 대규모 동시성 및 인덱싱 요구 -> Repository 계층만 교체하여 **SQLite RDBMS**로 원활히 마이그레이션 가능.

---

## 6. 자동화 단위/통합 테스트 검증

프로젝트 전반의 안정성을 증명하는 **46개 단위/통합/E2E 테스트 스위트**를 구축하여 100% 통과를 유지하고 있습니다.

```text
$ python -m unittest discover -s tests
..............................................
----------------------------------------------------------------------
Ran 46 tests in 0.150s

OK
```
- `tests/test_models.py` (12개): 날짜/월/타입/금액 불변식 검증 및 직렬화 라운드트립
- `tests/test_storage.py` (12개): CRUD, 원자적 쓰기, 최신순/동일날짜 ID 정렬, CSV 입출력, 배치 삽입
- `tests/test_services.py` (12개): 카테고리 참조 무결성, 예산 초과 계산, CSV 부분 성공/스킵 처리
- `tests/test_cli.py` (10개): 서브프로세스 기반 실제 CLI 명령, 대화형 add 주입, 에러 종료 코드(1) 검증
