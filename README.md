# Campus Conquest Offline Arena

공식 개발 도구의 엔진과 러너를 그대로 사용해 봇을 반복 대전시키는 오프라인 환경이다. 시간 제한을 강제하거나 측정만 할 수 있고, 단판·다중 시드·진영 교대·병렬 시리즈·라운드 로빈을 CLI 또는 로컬 웹 화면에서 실행한다.

## 빠른 시작

Python 3.11 이상만 필요하다. 프로젝트 루트에서 실행한다.

```bash
python3 scripts/setup_official.py
python3 -m arena doctor --json
python3 -m unittest discover -s tests -v
```

봇 두 개를 등록한다. `--command`는 쉘에서 실행할 명령, `--cwd`는 그 명령이 시작될 폴더다.

```bash
python3 -m arena bots add --id alpha --name Alpha --command "python3 /absolute/path/alpha/main.py" --cwd /absolute/path/alpha --language python --json
python3 -m arena bots add --id beta --name Beta --command "python3 /absolute/path/beta/main.py" --cwd /absolute/path/beta --language python --json
```

공식 시간 조건으로 여러 시드와 양 진영을 시험한다.

```bash
python3 -m arena series --bot-a alpha --bot-b beta --seeds 0:100 --swap-sides --jobs 4 --jsonl
```

사람이 보는 화면은 `python3 -m arena serve`로 열고 `http://127.0.0.1:8765`에 접속한다.

## 문서

- [사람용 사용법](docs/USER_GUIDE.md)
- [Codex·Claude 사용법](docs/AGENT_GUIDE.md)
- [설정 항목 참조](docs/CONFIG_REFERENCE.md)
- [구성 및 데이터 위치](docs/ARCHITECTURE.md)
- [원격 PC 인계](REMOTE_CODEX_HANDOFF.md)

원본 PDF와 ZIP은 수정하지 않는다. 생성되는 DB·리플레이·텔레메트리는 `workspace/` 아래에 저장되고 Git에는 포함되지 않는다.
