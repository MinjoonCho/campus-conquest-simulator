# 설정 참조

## 공통 경로

전역 옵션은 하위 명령 앞에 둔다.

| 옵션 | 기본값 | 의미 |
|---|---:|---|
| `--workspace` | `workspace` | DB, 리플레이, 텔레메트리 저장 폴더 |
| `--official-root` | `vendor/official` | 압축을 푼 공식 개발 도구 |

## 경기 설정

| CLI 옵션 | 기본값 | 의미 |
|---|---:|---|
| `--timing` | `strict` | `strict`, `observe`, `off` |
| `--first-turn-ms` | `3000` | 첫 응답 예산(ms) |
| `--turn-ms` | `300` | 일반 턴 응답 예산(ms) |
| `--safety-timeout-ms` | `60000` | 멈추지 않는 봇을 종료할 한도 |
| `--max-turns` | `160` | 최대 경기 턴 |
| `--seeds` | 필수 | 쉼표 목록 또는 `START:STOP[:STEP]` |
| `--swap-sides` | 꺼짐 | 같은 시드의 Y/K 교대 경기 추가 |
| `--repetitions` | `1` | 시드 묶음 반복 횟수 |
| `--jobs` | `1` | 동시 경기 수 |
| `--resume` | 없음 | 기존 시리즈의 미완료 job만 실행 |

병렬도가 지나치면 시간 측정 자체가 왜곡될 수 있다. 기본 출력은 들여쓰기 JSON, `--json`은 단일 압축 JSON, `--jsonl`은 진행 행과 마지막 결과 행이다.

## JSON 구성 모델

Python 자동화는 `arena.config.load_run_config(path)`로 다음 구조를 읽을 수 있다.

```json
{
  "workspace": "workspace",
  "official_root": "vendor/official",
  "timing": {"mode": "strict", "first_turn_ms": 3000, "turn_ms": 300, "safety_timeout_ms": 60000},
  "ruleset": {"mode": "official", "balance_overrides": {}},
  "games": {"max_turns": 160, "seeds": [0], "swap_sides": true, "repetitions": 1},
  "execution": {"jobs": 1, "on_bot_error": "forfeit"},
  "artifacts": {"replay_policy": "all"}
}
```

`official` 규칙셋은 밸런스 덮어쓰기를 거부한다. `custom`은 실험용이며 공식 비교 대상이 아니다. CLI와 웹은 공식 규칙 경로를 사용하고 사용자 밸런스는 Python API에서만 명시적으로 구성한다.

`replay_policy`는 `all`, `failures`, `none`을 받는다. 현재 `none`만 저장을 끄며 `failures`는 호환 예약값으로 모든 리플레이를 저장한다.
