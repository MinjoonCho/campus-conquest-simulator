# Offline Arena 사용자 가이드

## 설치 확인

```bash
python3 scripts/setup_official.py
python3 -m arena doctor --json
```

`{"status":"ok"...}`가 나오면 준비된 것이다. 별도 패키지 설치나 프런트엔드 빌드는 없다.

## 봇 등록

```bash
python3 -m arena bots add \
  --id my-bot \
  --name "My Bot" \
  --command "python3 main.py" \
  --cwd /absolute/path/to/my-bot \
  --language python \
  --json
python3 -m arena bots validate --id my-bot --json
python3 -m arena bots list --json
```

명령은 등록한 작업 폴더에서 실행된다. Windows에서는 `python main.py`처럼 해당 PC에서 실제로 동작하는 명령을 사용한다. Arena는 봇을 격리하는 보안 샌드박스가 아니므로 신뢰할 수 있는 프로그램만 등록한다.

## 대전 실행

```bash
# 단판
python3 -m arena match --bot-y alpha --bot-k beta --seed 42 --json

# 여러 시드, 진영 교대, 4경기 병렬 실행
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:100 --swap-sides --jobs 4 --jsonl

# 세 개 이상 봇의 전체 리그
python3 -m arena tournament --bots alpha beta gamma --seeds 0:20 --swap-sides --jobs 4 --json
```

`--seeds`는 `0,3,9` 또는 Python range와 같은 `0:100:2` 형식을 받는다. 중단된 시리즈는 결과의 `run_id`와 원래의 봇·조건으로 재개한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:100 --swap-sides --resume RUN_ID --json
```

## 시간 정책

- `strict`: 첫 턴 3000ms, 이후 300ms를 실제로 강제한다. 기본값이다.
- `observe`: 같은 기준을 넘었는지 기록하지만 응답은 안전 제한까지 기다린다.
- `off`: 경쟁 시간 위반을 판정하지 않고 실행시간만 측정한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:20 --timing observe --first-turn-ms 3000 --turn-ms 300 --safety-timeout-ms 10000 --json
```

세 모드 모두 멈추지 않는 봇을 종료하기 위한 안전 제한이 있다. `strict`, 정확히 3000/300ms, 최대 160턴, 공식 규칙을 모두 만족할 때만 `official_comparable=true`다.

## 웹 화면

```bash
python3 -m arena serve --host 127.0.0.1 --port 8765
```

`http://127.0.0.1:8765`에서 봇 등록, 시드·반복·병렬도·시간 정책 설정, 실행 기록과 턴별 리플레이 확인이 가능하다. 서버는 루프백 주소만 허용한다.

## 결과 확인

```bash
python3 -m arena runs list --json
python3 -m arena runs show --id RUN_ID --json
```

기본 저장 위치는 `workspace/`다. `arena.sqlite3`에는 메타데이터, `replays/RUN_ID`에는 공식 리플레이, `telemetry/RUN_ID`에는 턴별 시간 측정이 저장된다. 저장 위치를 분리하려면 `python3 -m arena --workspace /path ...`처럼 전역 옵션을 하위 명령 앞에 둔다.

## 문제 해결

- `invalid official tool root`: `python3 scripts/setup_official.py`를 다시 실행한다.
- `bot executable not found`: 명령 첫 항목이 PATH에 있거나 절대 경로인지 확인한다.
- 즉시 몰수패: `runs show`의 `forfeit.cause`와 텔레메트리를 확인한다.
- 출력이 멈춤: 봇이 매 턴 마지막에 `END`와 flush를 수행하는지 확인한다.
