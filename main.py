# =============================================
# Mini NPU Simulator
# =============================================

EPSILON = 1e-9  # 두 점수 차이가 이보다 작으면 "동점"으로 본다


# ---------------------------------------------
# [1단계] 핵심 부품
# ---------------------------------------------

def mac(pattern, filter_):
    """MAC 연산: 같은 위치끼리 곱하고(Multiply) 전부 더한다(Accumulate)."""
    n = len(pattern)
    total = 0.0
    for i in range(n):          # 행
        for j in range(n):      # 열
            total += pattern[i][j] * filter_[i][j]
    return total


def judge(score_a, score_b, label_a, label_b):
    """두 점수를 비교해서 판정한다. 차이가 EPSILON보다 작으면 동점."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return label_a
    return label_b


# ---------------------------------------------
# 1단계 테스트 (나중에 지울 부분)
# ---------------------------------------------
if __name__ == "__main__":
    cross = [[0, 1, 0],
             [1, 1, 1],
             [0, 1, 0]]
    x = [[1, 0, 1],
         [0, 1, 0],
         [1, 0, 1]]

    print("십자가 입력 → 십자가 필터:", mac(cross, cross))   # 5.0 이어야 함
    print("십자가 입력 → X 필터:    ", mac(cross, x))       # 1.0 이어야 함
    print("판정:", judge(mac(cross, cross), mac(cross, x), "Cross", "X"))
    print("동점 테스트:", judge(0.9, 0.8999999999999999, "Cross", "X"))
