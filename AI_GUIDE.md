# Codex / Claude용 사용 설명서

저장소 루트에서 작업한다. 원본 PDF와 세 ZIP, 압축 해제된 `vendor/official`은 수정하지 않는다. 공식 비교 실험은 `strict`, 첫 턴 3000ms, 일반 턴 300ms, 최대 160턴을 유지한다.

## 최초 점검

```bash
python3 scripts/setup_official.py
python3 -m arena doctor --json
python3 vendor/official/bots/dist/starter/run_tests.py --self-test
python3 -m unittest discover -s tests -v
```

모든 종료 코드가 0이고 doctor JSON의 `status`가 `ok`여야 한다. 실패하면 대량 실험을 시작하지 않는다.

## 봇 등록과 검증

```bash
python3 -m arena --workspace workspace bots add \
  --id candidate \
  --name Candidate \
  --command "python3 main.py" \
  --cwd /absolute/path/candidate \
  --language python \
  --json
python3 -m arena --workspace workspace bots validate --id candidate --json
```

등록 명령은 임의 코드를 실행하므로 신뢰할 수 있는 봇만 사용한다.

## 자동 평가

```bash
python3 -m arena --workspace workspace series \
  --bot-a champion --bot-b candidate \
  --seeds 1000:1200 --swap-sides --jobs 8 --jsonl
```

JSONL은 줄마다 독립 JSON이다. 경기 완료 행의 `event`는 `progress`이며 마지막 행은 `{"event":"result","result":{...}}`다. 마지막 행의 `result.run_id`를 보존한다.

```bash
python3 -m arena --workspace workspace runs show --id RUN_ID --json
```

여러 봇의 라운드 로빈:

```bash
python3 -m arena tournament \
  --bots baseline economy rush candidate \
  --seeds 5000:5100 --swap-sides --jobs 8 --jsonl
```

## 권장 평가 순서

1. `--max-turns 1 --seeds 0`으로 프로토콜과 기동 확인.
2. `--timing observe`로 실제 지연과 300ms 초과 확인.
3. 고정 개발 시드에서 양 진영 교대 회귀 평가.
4. 학습에 쓰지 않은 홀드아웃 시드 평가.
5. 여러 기준 봇과 라운드 로빈 평가.
6. 제출 후보만 공식 조건의 strict 장기 평가.

평균 승률만으로 챔피언을 교체하지 않는다. 진영별 결과, 몰수, 점수차, 홀드아웃 시드와 최악 상대를 함께 본다.

## 산출물

- `workspace/arena.sqlite3`: 실행 메타데이터
- `workspace/replays/<run_id>/`: 공식 리플레이 JSON
- `workspace/telemetry/<run_id>/`: 턴별 시간 JSON

DB를 직접 수정하지 않는다. CLI 또는 로컬 API를 사용한다. 웹 서버 실행 중 사용할 수 있는 API는 다음과 같다.

- `GET /api/health`
- `GET|POST /api/bots`
- `GET|POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/replays/{job_index}`

원격 자동화에서는 브라우저보다 CLI를 우선한다.

## Arena 코드 변경 시

새 동작이나 버그 수정은 실패하는 테스트를 먼저 추가한다. 완료 전 다음을 실행한다.

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

게임 규칙을 새로 구현하지 않는다. 공식 엔진과 다른 고속 학습 환경은 무작위 상태 차등 테스트 없이는 공식 평가 결과로 취급하지 않는다.
