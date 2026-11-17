# 새 컴퓨터에서 작업 시작하기

새 Mac에서 아래 순서대로 하면 **eee-map**과 **nycta-gsm** 두 프로젝트를 이어서 작업할 수 있다.

## 1. 사람이 직접 할 일

1. Claude Code(데스크톱 앱 또는 `claude` CLI)를 설치한다.
2. GitHub CLI에 로그인한다. 비밀번호와 토큰은 사람이 직접 넣는다.
   ```bash
   brew install gh
   gh auth login
   ```
3. Claude Code를 `~/Projects` 폴더에서 연다. 폴더가 없으면 만든다.
4. 아래 **프롬프트**를 그대로 붙여 넣는다.
5. nycta-gsm에서 쓰는 매뉴얼 PDF(`NYCTA_GS_Manual.pdf`)는 git에 없다. 원래 컴퓨터에서 USB나 클라우드 드라이브로 가져와 `~/Projects/nycta-gsm/manual/`에 넣는다.

## 2. 프롬프트 (복사해서 붙여 넣기)

```text
이 컴퓨터에서 내 프로젝트 두 개를 이어서 작업할 수 있게 세팅해 줘. 다 끝나면 한국어로 결과를 보고해 줘.

프로젝트(둘 다 GitHub 계정 outofthisweird, 위치는 ~/Projects 아래):
- eee-map: github.com/outofthisweird/eee-map (공개). ~/Projects/eee-map 에 둔다.
- nycta-gsm: github.com/outofthisweird/nycta-gsm-src (비공개, 원본). ~/Projects/nycta-gsm 에 둔다(폴더 이름 주의: -src 없이).
  - 이 저장소에는 공개 사이트용 원격 pages(github.com/outofthisweird/nycta-gsm, web/만 올라감)를 따로 추가해야 한다.

순서:
1. git, python3, gh가 있는지 확인한다. `gh auth status`로 로그인이 안 되어 있으면 멈추고, 내가 직접 `gh auth login`을 하라고 안내해 줘(비밀번호·토큰은 네가 넣지 마).
2. 각 폴더가 이미 있으면 `git pull`만 하고, 없으면 clone한다. 비공개 저장소는 `gh repo clone outofthisweird/nycta-gsm-src ~/Projects/nycta-gsm`으로 받는다.
3. 각 프로젝트의 CLAUDE.md를 먼저 끝까지 읽고, 거기 적힌 규칙과 세팅 절차를 따른다. CLAUDE.md 내용이 이 프롬프트와 다르면 CLAUDE.md를 따른다.
4. eee-map:
   - `python3 build.py`를 실행한다.
   - Playwright를 설치하고(시스템 pip가 막혀 있으면 프로젝트 안 .venv를 만들어 쓴다) `tests/smoke_test.py`를 돌린다.
5. nycta-gsm:
   - `git remote add pages https://github.com/outofthisweird/nycta-gsm.git` (이미 있으면 건너뜀)
   - `make setup`, 그다음 `make preview`를 실행한다. 헬베티카 미리보기는 macOS 시스템 서체를 쓰고, 절대 커밋하거나 배포하지 않는다.
   - `manual/NYCTA_GS_Manual.pdf`가 있으면 `make verify`를 돌리고, CLAUDE.md의 「검증 기준」 값과 비교한다. 없으면 내가 원래 컴퓨터에서 복사해 와야 한다고 알려 줘.
6. 보고할 것: 각 프로젝트의 최신 커밋, 테스트·검증 결과(실패하면 출력 그대로), 내가 직접 해야 할 일이 남았는지.

주의: 두 저장소 모두 세팅 과정에서 커밋이나 push는 하지 마. 비공개 저장소 내용은 공개 저장소(pages, eee-map)로 옮기지 마.
```

## 3. 평소 작업 습관

- **시작할 때:** 해당 프로젝트에서 `git pull`을 한다. Claude에게 "pull하고 시작해"라고 하면 된다.
- **끝날 때:** "오늘 한 거 CLAUDE.md에 정리하고 push해 줘"라고 한다.
- **대화 기록과 Claude 메모리는 컴퓨터를 따라가지 않는다.** 남겨야 할 결정은 CLAUDE.md(nycta-gsm은 `ledger.yaml`도)에 적는다.
