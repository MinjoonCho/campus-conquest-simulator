# 원격 PC Codex / Claude 인계서

이 폴더는 Campus Conquest 봇을 평가하기 위한 완성된 오프라인 Arena를 포함한다. 먼저 [AI 운영 가이드](docs/AGENT_GUIDE.md)를 끝까지 읽고 그 명령을 기준으로 작업한다.

## 원격 PC에서 처음 할 일

```bash
python3 scripts/setup_official.py
python3 -m arena doctor --json
python3 vendor/official/bots/dist/starter/run_tests.py --self-test
python3 -m unittest discover -s tests -v
```

그 다음 GPU, CPU, RAM, Python 버전과 드라이버를 기록한다. 공식 테스트와 Arena 테스트가 모두 통과하기 전에는 대규모 학습을 시작하지 않는다.

## 원본과 규칙

`깃발대항전_게임규칙서.pdf`, `yk-development-tools.zip`, `yk-python-sample.zip`, `yk-cpp-sample.zip`은 수정하거나 재패키징하지 않는다. `vendor/official`도 수정하지 않는다.

규칙 해석의 우선순위는 공식 PDF, 공식 도구의 문서와 엔진, Arena 문서 순서다. 불일치는 최소 재현 사례와 함께 보고한다.

## 원격 PC 역할

- CPU: 공식 엔진 기반 대량 대전, 진영 교대, 홀드아웃 시드 평가
- GPU: 배치 정책 추론, 자가대전 학습, 카운터 정책 연구
- Arena: 모든 후보를 같은 프로토콜과 시간 조건으로 비교하고 리플레이·텔레메트리 보존

강화학습 정책은 가능하면 상위 목표나 가치 평가를 출력하고 합법 명령 생성은 결정론적 계층이 맡는다. 모델 제출이 규정이나 300ms 제한에 맞지 않으면 교사 정책으로 사용해 평가식·오프닝·상태기계·탐색 우선순위로 증류한다.

비공개 API 접근, 상대 프로세스나 명령 탈취, 취약점 악용은 하지 않는다. 학습 가중치 제출 가능 여부가 공식적으로 확인되기 전에는 제출 가능하다고 가정하지 않는다.

## 기준 실험

```bash
python3 -m arena series --bot-a champion --bot-b candidate --seeds 10000:10200 --swap-sides --jobs 8 --timing observe --jsonl
python3 -m arena series --bot-a champion --bot-b candidate --seeds 20000:20100 --swap-sides --jobs 8 --timing strict --jsonl
python3 -m arena tournament --bots baseline champion candidate counter --seeds 30000:30100 --swap-sides --jobs 8 --jsonl
```

병렬도는 처리량을 측정한 뒤 조정한다. 시간 적합성은 시스템 부하가 안정된 strict 실행으로 판단한다.

## 산출물과 협업

`workspace/arena.sqlite3`, `workspace/replays`, `workspace/telemetry`는 실험 산출물이다. 큰 리플레이, 체크포인트, 데이터셋은 Git에 넣지 않는다. 코드·설정·봇 버전·시드 범위·run ID를 함께 기록한다.

Arena 자체를 바꿨다면 새 실패 테스트를 먼저 추가하고 전체 테스트와 `git diff --check`를 통과시킨다. 자세한 CLI는 [사용자 가이드](docs/USER_GUIDE.md), 설정 필드는 [설정 참조](docs/CONFIG_REFERENCE.md), 내부 경계는 [구성 문서](docs/ARCHITECTURE.md)를 따른다.
