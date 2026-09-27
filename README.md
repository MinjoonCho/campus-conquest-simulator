# Campus Conquest Offline Arena

공식 개발 도구의 엔진과 러너를 그대로 사용해 봇을 반복 대전시키는 오프라인 환경이다. 시간 제한을 강제하거나 측정만 할 수 있고, 단판·다중 시드·진영 교대·병렬 시리즈·라운드 로빈을 CLI 또는 로컬 웹 화면에서 실행한다. Codex·Claude가 자동으로 사용할 때는 [AI_GUIDE.md](AI_GUIDE.md)를 읽는다.

## 빠른 시작

Python 3.11 이상만 필요하다. 프로젝트 루트에서 실행한다.

```bash
python3 scripts/setup_official.py
python3 -m arena doctor --json
python3 -m unittest discover -s tests -v
```

## 봇 등록

`--command`는 셸에서 실행할 명령, `--cwd`는 그 명령이 시작될 폴더다.

```bash
python3 -m arena bots add --id alpha --name Alpha --command "python3 main.py" --cwd /absolute/path/alpha --language python --json
python3 -m arena bots add --id beta --name Beta --command "./main" --cwd /absolute/path/beta --language cpp --json
python3 -m arena bots validate --id alpha --json
python3 -m arena bots list --json
```

등록한 명령은 지정한 작업 폴더에서 실행된다. Arena는 봇을 격리하는 보안 샌드박스가 아니므로 신뢰할 수 있는 프로그램만 등록한다.

## 대전 실행

단판:

```bash
python3 -m arena match --bot-y alpha --bot-k beta --seed 42 --json
```

공식 시간 조건으로 여러 시드와 양 진영을 시험한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:100 --swap-sides --jobs 4 --jsonl
```

세 개 이상 봇의 전체 리그:

```bash
python3 -m arena tournament --bots alpha beta gamma --seeds 0:20 --swap-sides --jobs 4 --json
```

`--seeds`는 `0,3,9` 또는 `0:100:2` 형식을 받는다. 중단된 시리즈는 결과의 `run_id`와 원래 조건으로 재개한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:100 --swap-sides --resume RUN_ID --json
```

## 시간 정책

- `strict`: 첫 턴 3000ms, 이후 300ms를 실제로 강제한다. 기본값이다.
- `observe`: 시간 초과 여부는 기록하되 안전 제한까지 응답을 기다린다.
- `off`: 경쟁 시간 위반을 판정하지 않고 실행시간만 측정한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:20 --timing observe --safety-timeout-ms 10000 --json
```

세 모드 모두 멈추지 않는 봇을 종료하는 안전 제한이 있다. `strict`, 3000/300ms, 160턴, 공식 규칙을 모두 만족할 때만 결과가 `official_comparable=true`로 표시된다.

## 웹 화면

```bash
python3 -m arena serve --host 127.0.0.1 --port 8765
```

`http://127.0.0.1:8765`에서 봇 등록, 경기 설정, 실행 기록과 턴별 리플레이를 볼 수 있다. 서버는 루프백 주소만 허용한다.

## 결과와 저장 위치

```bash
python3 -m arena runs list --json
python3 -m arena runs show --id RUN_ID --json
```

기본 저장 위치는 `workspace/`다.

- `arena.sqlite3`: 봇, 실행, 경기 메타데이터
- `replays/RUN_ID/*.json`: 공식 형식 리플레이
- `telemetry/RUN_ID/*.json`: 팀·턴·소요시간·시간 위반

저장 위치를 분리하려면 `python3 -m arena --workspace /path ...`처럼 전역 옵션을 하위 명령 앞에 둔다.

## 문제 해결

- `invalid official tool root`: `python3 scripts/setup_official.py`를 다시 실행한다.
- `bot executable not found`: 실행 파일이나 인터프리터 경로를 확인한다.
- 즉시 몰수패: `runs show`의 `forfeit.cause`와 텔레메트리를 확인한다.
- 출력이 멈춤: 봇이 매 턴 마지막에 `END`를 출력하고 flush하는지 확인한다.

원본 PDF와 ZIP은 수정하지 않는다. 생성되는 DB·리플레이·텔레메트리는 `workspace/` 아래에 저장되고 Git에는 포함되지 않는다.
