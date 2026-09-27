# Arena 구성과 데이터 흐름

Arena는 게임 규칙을 복제하지 않는다. 설정과 봇 프로세스를 감싼 뒤 공식 러너에 전달하고 결과를 저장한다.

```text
CLI / 로컬 웹 UI
        │
봇 등록 · 시리즈 · 토너먼트 서비스
        │
시간 측정 래퍼 ── 공식 runner / engine / mapgen
        │
SQLite 메타데이터 + JSON 리플레이/텔레메트리
```

## 주요 모듈

- `arena/models.py`, `arena/config.py`: 설정 검증과 공식 비교 여부
- `arena/bot_registry.py`: 실행 명령과 작업 폴더
- `arena/timing.py`: strict/observe/off와 안전 타임아웃
- `arena/official_adapter.py`: 공식 `run_match`의 단일 경계
- `arena/series.py`: 시드·반복·진영 교대·병렬·재개
- `arena/tournament.py`: 라운드 로빈과 순위 집계
- `arena/storage.py`: SQLite와 원자적 JSON 기록
- `arena/web.py`, `arena/static/`: 루프백 API와 대시보드

`vendor/official`은 제공 ZIP에서 추출한 읽기 전용 기준 구현이다. 상태 전이·명령 파싱·승리 판정·리플레이 생성은 공식 코드에 위임한다.

각 시리즈는 32자리 `run_id`를 가진다. 진영 교대는 동일 시드의 Y/K만 바꾸고 통계는 봇 ID로 합산한다. 재개는 저장된 job index를 건너뛴다. 병렬 worker는 SQLite 연결을 공유하지 않으며 결과 기록은 호출 스레드가 직렬화한다.

웹 서버는 루프백 주소만 허용하고 리플레이 API는 `workspace/replays` 바깥을 읽지 않는다. 실행되는 봇 자체는 샌드박스되지 않는다.
