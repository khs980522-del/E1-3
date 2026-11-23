# =============================================
# Mini NPU Simulator
# =============================================
import json
import time

EPSILON = 1e-9   # 두 점수 차이가 이보다 작으면 "동점"으로 본다
REPEAT = 10      # 성능 측정 반복 횟수


# ---------------------------------------------
# [1단계] 데이터 구조: n×n 2차원 배열
# ---------------------------------------------

def create_matrix(n):
    """0.0으로 채운 n×n 2차원 리스트를 만든다."""
    return [[0.0] * n for _ in range(n)]


def set_value(matrix, i, j, value):
    """matrix의 (i행, j열) 위치에 value를 저장한다."""
    matrix[i][j] = value


def get_value(matrix, i, j):
    """matrix의 (i행, j열) 위치의 값을 읽어온다."""
    return matrix[i][j]


# ---------------------------------------------
# [1단계] 핵심 부품: MAC 연산과 판정
# ---------------------------------------------

def mac(pattern, filter_):
    """MAC 연산: 같은 위치끼리 곱하고(Multiply) 전부 더한다(Accumulate)."""
    n = len(pattern)
    total = 0.0
    for i in range(n):          # 행
        for j in range(n):      # 열
            # get_value()와 같은 동작이지만, 수백 번 반복되는 곳이라
            # 함수 호출 비용을 줄이려고 직접 인덱스로 읽는다.
            total += pattern[i][j] * filter_[i][j]
    return total


def judge(score_a, score_b, label_a, label_b):
    """두 점수를 비교해서 판정한다. 차이가 EPSILON보다 작으면 동점."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return label_a
    return label_b


def measure_mac_time(pattern, filter_, repeat=REPEAT, func=mac):
    """MAC 연산만 repeat번 반복해서 평균 시간(ms)을 구한다. (입출력 시간은 제외)
    func에 mac_flat을 넘기면 1차원 버전의 시간을 잰다."""
    start = time.perf_counter()
    for _ in range(repeat):
        func(pattern, filter_)
    end = time.perf_counter()
    return (end - start) / repeat * 1000   # 초 → 밀리초


# ---------------------------------------------
# [보너스 1] 1차원 배열 최적화
# ---------------------------------------------

def flatten(matrix):
    """n×n 2차원 리스트를 길이 n²의 1차원 리스트로 편다.
    예: [[1,2],[3,4]] → [1,2,3,4]   (위치 [i][j] → [i*n + j])"""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(flat_pattern, flat_filter):
    """1차원 MAC: 반복문 하나, 인덱스 하나로 끝난다."""
    total = 0.0
    for k in range(len(flat_pattern)):
        total += flat_pattern[k] * flat_filter[k]
    return total


# ---------------------------------------------
# [2단계] 모드 1: 사용자 입력 (3x3)
# ---------------------------------------------

def read_matrix(title, n=3):
    """n줄을 입력받아 n×n 2차원 리스트로 돌려준다. 형식이 틀리면 처음부터 다시 받는다."""
    while True:
        print(f"{title} ({n}줄 입력, 공백 구분)")
        matrix = create_matrix(n)
        ok = True
        for i in range(n):
            parts = input().split()
            # 검증 1: 한 줄에 숫자가 n개인지
            if len(parts) != n:
                ok = False
                break
            # 검증 2: 모두 숫자로 바꿀 수 있는지
            try:
                row = [float(p) for p in parts]
            except ValueError:
                ok = False
                break
            for j in range(n):
                set_value(matrix, i, j, row[j])   # (i, j) 위치에 저장

        if ok:
            return matrix
        print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요. 다시 입력해 주세요.\n")


def print_section(title):
    print("\n#---------------------------------------")
    print(f"# {title}")
    print("#---------------------------------------")


def run_mode1():
    print_section("[1] 필터 입력")
    print("필터 입력 방식: 1. 직접 입력  2. 자동 생성 (A=Cross, B=X)")
    while True:
        how = input("선택: ").strip()
        if how in ("1", "2"):
            break
        print("1 또는 2를 입력하세요.")

    if how == "1":
        filter_a = read_matrix("필터 A")
        print()
        filter_b = read_matrix("필터 B")
    else:
        filter_a = make_cross(3)   # 보너스 2: 패턴 생성기 재활용
        filter_b = make_x(3)
        print("필터 A (자동 생성 Cross)")
        print_matrix(filter_a)
        print("필터 B (자동 생성 X)")
        print_matrix(filter_b)
    print("✓ 필터 A, B 저장 완료")

    print_section("[2] 패턴 입력")
    pattern = read_matrix("패턴")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    avg_ms = measure_mac_time(pattern, filter_a)
    result = judge(score_a, score_b, "A", "B")

    print_section("[3] MAC 결과")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT}회): {avg_ms:.4f} ms")
    if result == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {result}")

    # 사용자가 입력한 패턴과 필터 그대로 측정한 3x3 성능
    print_section(f"[4] 성능 분석 (평균/{REPEAT}회)")
    print_perf_table([(3, avg_ms)])


# ---------------------------------------------
# [3단계] 모드 2: data.json 분석
# ---------------------------------------------

# 여러 가지 표기를 표준 라벨 2개(Cross, X)로 통일하는 표
LABEL_MAP = {
    "+": "Cross",
    "cross": "Cross",
    "x": "X",
}


def normalize_label(raw):
    """'+', 'cross', 'x' 같은 표기를 표준 라벨 'Cross' 또는 'X'로 바꾼다. 모르는 표기면 None."""
    key = str(raw).strip().lower()   # 대소문자, 앞뒤 공백 차이를 없앤다
    return LABEL_MAP.get(key)


def is_square(matrix, n):
    """matrix가 n×n 크기의 2차원 리스트인지 검사한다."""
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
    return True


def load_filters(data):
    """data['filters']를 {5: {'Cross': [...], 'X': [...]}, 13: {...}, ...} 형태로 정리한다."""
    filters = {}
    for size_key, pair in data.get("filters", {}).items():   # 예: "size_5"
        try:
            n = int(size_key.split("_")[1])
        except (IndexError, ValueError):
            print(f"✗ {size_key}: 키 형식이 잘못됨 (size_N 이어야 함)")
            continue

        normalized = {}
        for label_key, matrix in pair.items():               # 예: "cross", "x"
            label = normalize_label(label_key)
            if label is None:
                print(f"✗ {size_key}: 알 수 없는 필터 키 '{label_key}'")
                continue
            if not is_square(matrix, n):
                print(f"✗ {size_key}: '{label_key}' 필터가 {n}x{n}이 아님")
                continue
            normalized[label] = matrix

        if "Cross" in normalized and "X" in normalized:
            filters[n] = normalized
            print(f"✓ {size_key:<8} 필터 로드 완료 (Cross, X)")
        else:
            print(f"✗ {size_key}: Cross/X 필터가 모두 있어야 함")
    return filters


def analyze_patterns(data, filters):
    """패턴마다 MAC → 판정 → PASS/FAIL. 결과를 리스트로 모아 돌려준다."""
    results = []   # (케이스 이름, PASS 여부, 실패 사유)

    for case_id, case in data.get("patterns", {}).items():   # 예: "size_5_1"
        print(f"--- {case_id} ---")

        # 1) 키에서 N 꺼내기: "size_13_2" → ["size", "13", "2"] → 13
        try:
            n = int(case_id.split("_")[1])
        except (IndexError, ValueError):
            reason = "키 형식 오류 (size_N_idx 이어야 함)"
            print(f"FAIL ({reason})")
            results.append((case_id, False, reason))
            continue

        # 2) 해당 크기의 필터가 있는지
        if n not in filters:
            reason = f"size_{n} 필터 없음"
            print(f"FAIL ({reason})")
            results.append((case_id, False, reason))
            continue

        # 3) 패턴 크기가 필터 크기와 같은지
        pattern = case.get("input")
        if not is_square(pattern, n):
            reason = f"패턴 크기가 {n}x{n}이 아님 (필터와 불일치)"
            print(f"FAIL ({reason})")
            results.append((case_id, False, reason))
            continue

        # 4) expected 라벨 정규화
        expected = normalize_label(case.get("expected"))
        if expected is None:
            reason = f"알 수 없는 expected 값 '{case.get('expected')}'"
            print(f"FAIL ({reason})")
            results.append((case_id, False, reason))
            continue

        # 5) MAC 연산 + 판정
        score_cross = mac(pattern, filters[n]["Cross"])
        score_x = mac(pattern, filters[n]["X"])
        result = judge(score_cross, score_x, "Cross", "X")

        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")

        if result == expected:
            print(f"판정: {result} | expected: {expected} | PASS")
            results.append((case_id, True, ""))
        elif result == "UNDECIDED":
            reason = f"동점(UNDECIDED) 처리 규칙에 따라 FAIL (|차이| < {EPSILON})"
            print(f"판정: {result} | expected: {expected} | FAIL (동점 규칙)")
            results.append((case_id, False, reason))
        else:
            reason = f"판정 {result} ≠ expected {expected}"
            print(f"판정: {result} | expected: {expected} | FAIL")
            results.append((case_id, False, reason))

    return results


def run_mode2(path="data.json"):
    # 파일 읽기 (파일이 없거나 JSON 문법이 틀려도 프로그램이 죽지 않게)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"오류: {path} 파일을 찾을 수 없습니다. main.py와 같은 폴더에 두세요.")
        return
    except json.JSONDecodeError as e:
        print(f"오류: {path}의 JSON 형식이 잘못되었습니다. ({e})")
        return

    print_section("[1] 필터 로드")
    filters = load_filters(data)

    print_section("[2] 패턴 분석 (라벨 정규화 적용)")
    results = analyze_patterns(data, filters)

    print_section(f"[3] 성능 분석 (평균/{REPEAT}회)")
    print_performance([3, 5, 13, 25])

    print_section(f"[3-1] 최적화 전/후 비교 (2차원 vs 1차원, 평균/{COMPARE_REPEAT}회)")
    print_optimization_compare([3, 5, 13, 25])

    print_section("[4] 결과 요약")
    print_summary(results)


# ---------------------------------------------
# [4단계] 성능 분석 + 결과 요약
# ---------------------------------------------

def make_cross(n):
    """n×n 십자가 패턴을 만든다. (가운데 행과 가운데 열이 1)"""
    mid = n // 2
    return [[1.0 if (i == mid or j == mid) else 0.0 for j in range(n)] for i in range(n)]


def make_x(n):
    """n×n X 패턴을 만든다. (두 대각선이 1)"""
    return [[1.0 if (i == j or i + j == n - 1) else 0.0 for j in range(n)] for i in range(n)]


def print_performance(sizes):
    """크기별로 MAC 평균 시간과 연산 횟수(N²)를 표로 출력한다."""
    rows = []
    for n in sizes:
        pattern = make_cross(n)   # 측정용 입력은 자동 생성 (같은 조건으로 비교하기 위해)
        filter_ = make_x(n)
        rows.append((n, measure_mac_time(pattern, filter_)))
    print_perf_table(rows)


def print_perf_table(rows):
    """(크기 N, 평균 시간 ms) 목록을 "크기 / 평균 시간 / 연산 횟수(N²)" 표로 출력한다."""
    print(f"{'크기':<8}{'평균 시간(ms)':>14}{'연산 횟수(N²)':>14}")
    print("-" * 40)
    for n, avg_ms in rows:
        print(f"{f'{n}x{n}':<8}{avg_ms:>14.4f}{n * n:>14}")


def print_summary(results):
    """전체/통과/실패 개수와 실패 케이스 목록을 출력한다."""
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print("\n실패 케이스:")
        for case_id, ok, reason in results:
            if not ok:
                print(f"- {case_id}: {reason}")
    print('\n(상세 원인 분석 및 복잡도 설명은 README.md의 "결과 리포트" 섹션 참고)')


# ---------------------------------------------
# [보너스] 최적화 비교 + 패턴 생성기 모드
# ---------------------------------------------

COMPARE_REPEAT = 1000   # 비교용 반복 횟수 (10회는 너무 짧아 오차가 커서 늘림. 두 방식 모두 같은 횟수)


def print_optimization_compare(sizes):
    """같은 입력, 같은 반복 횟수로 2차원 MAC과 1차원 MAC의 시간을 비교한다."""
    print(f"{'크기':<8}{'2차원(ms)':>12}{'1차원(ms)':>12}{'속도 향상':>10}")
    print("-" * 44)
    for n in sizes:
        pattern = make_cross(n)
        filter_ = make_x(n)
        flat_p = flatten(pattern)   # 변환은 측정 구간 밖에서 미리 해둔다
        flat_f = flatten(filter_)

        t_2d = measure_mac_time(pattern, filter_, COMPARE_REPEAT, mac)
        t_1d = measure_mac_time(flat_p, flat_f, COMPARE_REPEAT, mac_flat)

        # 두 방식의 점수가 같은지도 확인 (최적화해도 결과는 같아야 한다)
        same = abs(mac(pattern, filter_) - mac_flat(flat_p, flat_f)) < EPSILON
        speedup = t_2d / t_1d if t_1d > 0 else 0
        print(f"{f'{n}x{n}':<8}{t_2d:>12.5f}{t_1d:>12.5f}{speedup:>9.2f}x"
              + ("" if same else "  (점수 불일치!)"))


def print_matrix(matrix):
    """행렬을 ■ □ 모양으로 보여준다. (0이 아니면 ■)"""
    n = len(matrix)
    for i in range(n):
        cells = []
        for j in range(n):
            cells.append("■" if get_value(matrix, i, j) != 0 else "□")   # (i, j) 위치를 읽음
        print(" ".join(cells))


def read_size():
    """패턴 크기 N을 입력받는다. 십자가 가운데가 정확히 생기도록 3 이상의 홀수만 허용."""
    while True:
        text = input("크기 N 입력 (3 이상 홀수, 예: 7): ").strip()
        try:
            n = int(text)
        except ValueError:
            print("숫자를 입력하세요.")
            continue
        if n >= 3 and n % 2 == 1:
            return n
        print("3 이상의 홀수를 입력하세요. (짝수는 가운데 줄이 없어서 십자가가 대칭이 안 됨)")


def run_mode3():
    print_section("[1] 패턴 생성")
    n = read_size()
    while True:
        kind = input("생성할 패턴 (1. Cross  2. X): ").strip()
        if kind in ("1", "2"):
            break
        print("1 또는 2를 입력하세요.")

    pattern = make_cross(n) if kind == "1" else make_x(n)
    label = "Cross" if kind == "1" else "X"
    print(f"\n생성된 {n}x{n} {label} 패턴")
    print_matrix(pattern)

    print_section("[2] MAC 결과 (필터도 자동 생성)")
    score_cross = mac(pattern, make_cross(n))
    score_x = mac(pattern, make_x(n))
    print(f"Cross 필터 점수: {score_cross}")
    print(f"X 필터 점수: {score_x}")
    print(f"판정: {judge(score_cross, score_x, 'Cross', 'X')} (생성한 패턴: {label})")

    print_section(f"[3] 성능 분석 (평균/{REPEAT}회)")
    print_performance([n])

    print_section(f"[4] 최적화 전/후 비교 (평균/{COMPARE_REPEAT}회)")
    print_optimization_compare([n])


# ---------------------------------------------
# 프로그램 시작
# ---------------------------------------------

def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. 패턴 생성기 (보너스)")

    while True:
        choice = input("선택: ").strip()
        if choice == "1":
            run_mode1()
            break
        elif choice == "2":
            run_mode2()
            break
        elif choice == "3":
            run_mode3()
            break
        else:
            print("1, 2, 3 중에서 입력하세요.")


if __name__ == "__main__":
    main()
