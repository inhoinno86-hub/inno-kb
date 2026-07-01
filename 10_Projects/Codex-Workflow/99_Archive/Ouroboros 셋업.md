---
type: decision
scope: project
project: Codex-Workflow
area: archive
status: archived
visibility: private
---
# Codex 전역 설정: Ouroboros + Superpowers Planning Workflow 정리

## 1. 작업 배경

Codex CLI에 `Ouroboros`를 적용하고, 기존 전역 설정에 이미 적용되어 있던 `Superpowers plugin`과 함께 사용할 수 있도록 전역 planning workflow를 재정의했다.

기존 전역 Codex 설정에는 다음 항목이 포함되어 있었다.

- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- Superpowers plugin
- FableCodex plugin
- Caveman response mode
- Plan mode 진입 시 Superpowers brainstorming 사용 여부를 묻는 정책
- `PLAN-YYYY-MM-DD-<feature-name>.md` 형식의 plan file 생성 정책

이번 작업의 핵심 목표는 다음과 같다.

- Codex plan mode에서 `Ouroboros interview`를 선택적으로 사용할 수 있게 한다.
- 기존 `Superpowers brainstorming`과 충돌하지 않도록 역할을 분리한다.
- 둘 다 사용할 경우 같은 plan artifact를 함께 수정하고 공유하도록 정의한다.
- Ouroboros는 명시적 승인 없이 자동 실행되지 않도록 제한한다.
- 기존 `PLAN.md` 단일 파일 대신 `PLAN-YYYY-MM-DD-<feature-name>.md` 형식을 전역 표준으로 사용한다.
- 필요 시 hook/rule을 통해 `PLAN.md` 생성과 잘못된 plan filename 생성을 차단한다.

---

## 2. Ouroboros 설치 상태

`pipx ensurepath` 수행 시 아래 메시지가 출력되었다.

    /home/inno/.local/bin is already in PATH.

    ⚠️  All pipx binary directories have been appended to
    PATH. If you are sure you want to proceed, try again
    with the '--force' flag.

    Otherwise pipx is ready to go!

판단 결과:

- 정상 메시지
- `/home/inno/.local/bin`이 이미 `PATH`에 포함되어 있음
- `--force` 실행 불필요
- 이후 `pipx install 'ouroboros-ai[mcp]'` 진행 가능

이후 Ouroboros 설치는 정상 수행된 것으로 확인했다.

---

## 3. Ouroboros 사용 정책

Ouroboros는 자동 실행하지 않는다.

Ouroboros 사용 조건은 아래로 제한한다.

1. 사용자가 명시적으로 Ouroboros 사용을 요청한 경우
2. plan mode 진입 후 Codex가 물어봤고, 사용자가 Ouroboros 사용을 승인한 경우
3. 사용자가 직접 `ooo interview`, `ooo run`, `ouroboros` 명령 등을 호출한 경우

기본 정책:

    명시적 승인 없는 Ouroboros 실행 금지

---

## 4. Plan Mode Gate 정책

기존에는 plan mode 진입 시 Superpowers brainstorming 사용 여부만 물어보는 구조였다.

변경 후에는 plan mode 진입 시 아래 4개 선택지를 물어보는 구조로 확장한다.

    계획 생성 전에 확인하겠습니다.
    생성/수정할 계획 파일은 `PLAN-YYYY-MM-DD-<feature-name>.md` 형식을 사용합니다.
    이 파일은 Ouroboros interview와 Superpowers brainstorming이 함께 수정하고 공유할 수 있는 planning artifact입니다.

    어떤 planning workflow를 사용할까요?

    - 둘 다 사용
    - Ouroboros만 사용
    - Superpowers만 사용
    - 둘 다 사용 안 함

선택지별 동작:

| 선택 | 동작 |
|---|---|
| 둘 다 사용 | Superpowers brainstorming 후 Ouroboros interview 수행 |
| Ouroboros만 사용 | Ouroboros interview만 수행 |
| Superpowers만 사용 | Superpowers brainstorming + writing-plans 수행 |
| 둘 다 사용 안 함 | 일반 Codex plan mode 사용 |

---

## 5. Plan File 이름 정책

기존 `PLAN.md` 단일 파일은 사용하지 않는다.

앞으로 모든 plan artifact는 아래 형식을 사용한다.

    PLAN-YYYY-MM-DD-<feature-name>.md

예시:

    PLAN-2026-06-29-phase-0-4-claude-md.md
    PLAN-2026-06-29-config-design.md
    PLAN-2026-06-29-data-pipeline.md

파일명 규칙:

- `YYYY-MM-DD`는 plan 생성일 기준
- `<feature-name>`은 짧은 kebab-case 사용
- 영문 소문자, 숫자, 하이픈만 사용
- 공백, 언더스코어, 한글, 대문자 사용 금지
- 같은 날짜와 feature 이름이 이미 있으면 기존 파일을 업데이트
- 다른 작업과 충돌하면 `-02`, `-03` suffix 사용 가능

---

## 6. Shared Planning Artifact 정의

`PLAN-YYYY-MM-DD-<feature-name>.md`는 아래 두 workflow가 함께 수정하고 공유하는 파일로 정의한다.

- Ouroboros interview
- Superpowers brainstorming

둘 다 사용하는 경우 권장 순서:

1. Superpowers brainstorming으로 넓은 아이디어 탐색
2. Ouroboros interview로 구조화된 요구사항 정리
3. 두 결과를 같은 plan artifact에 병합
4. 기존 내용 덮어쓰기 금지
5. 변경 이유와 결정 사항을 plan file에 기록
6. 사용자 승인 전 implementation 진입 금지

---

## 7. Plan Artifact 필수 메타데이터

모든 `PLAN-YYYY-MM-DD-<feature-name>.md` 파일 상단에는 아래 메타데이터를 포함한다.

    # PLAN: <feature-name>

    ## Planning Metadata

    - Date: YYYY-MM-DD
    - Feature name: <feature-name>
    - Planning artifact: PLAN-YYYY-MM-DD-<feature-name>.md
    - Superpowers brainstorming: used / not used
    - Ouroboros interview: used / not used
    - Shared artifact: yes
    - Notes: This file is the shared planning artifact that may contain contributions from both Superpowers brainstorming and Ouroboros interview.

---

## 8. 수정한 전역 설정 파일

첨부된 기존 `~/.codex/AGENTS.md`, `~/.codex/config.toml`을 기준으로 신규 파일을 생성했다.

생성 파일:

    AGENTS.global-ouroboros-superpowers.md
    config.global-ouroboros-superpowers.toml

### AGENTS.md 반영 사항

- 기존 Global Codex Working Agreements 유지
- 기존 Superpowers execution phase policy 유지
- 기존 Caveman response mode 유지
- Plan Mode Gate를 Superpowers 단일 질문에서 4개 선택지 구조로 확장
- Ouroboros 자동 실행 금지 정책 추가
- `PLAN.md` 대신 `PLAN-YYYY-MM-DD-<feature-name>.md` 사용 명시
- Ouroboros와 Superpowers가 같은 plan artifact를 공유할 수 있음을 명시
- implementation 전 사용자 승인 필요 정책 유지

### config.toml 반영 사항

- 기존 model 설정 유지
- 기존 trusted projects 유지
- 기존 plugin 설정 유지
- `developer_instructions`에 planning gate 정책 반영
- `PLAN.md` 금지 및 `PLAN-YYYY-MM-DD-<feature-name>.md` 사용 정책 반영
- Ouroboros 승인 없는 실행 금지 정책 반영

---

## 9. 적용 명령어

신규 파일을 다운로드한 뒤 아래처럼 적용한다.

    # 백업
    cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.bak.$(date +%Y%m%d_%H%M%S)
    cp ~/.codex/config.toml ~/.codex/config.toml.bak.$(date +%Y%m%d_%H%M%S)

    # 신규 파일 적용
    cp AGENTS.global-ouroboros-superpowers.md ~/.codex/AGENTS.md
    cp config.global-ouroboros-superpowers.toml ~/.codex/config.toml

적용 후 Codex 재시작:

    cd ~/repo/inno-kis-trading
    codex

테스트 프롬프트:

    /plan Phase 0-4 CLAUDE.md 작성 계획 만들어줘

기대 동작:

- 바로 구현하지 않음
- plan file 생성 전 workflow 선택 질문
- 선택에 따라 Ouroboros / Superpowers / 일반 plan mode 수행
- 결과는 `PLAN-YYYY-MM-DD-<feature-name>.md` 형식으로 생성

---

## 10. Hook 기반 강제 규칙 검토

`AGENTS.md`와 `config.toml`은 Codex 행동 지침이다.

더 강하게 제어하려면 hook을 사용한다.

권장 구조:

    ~/.codex/
    ├── AGENTS.md
    ├── config.toml
    ├── hooks.json
    ├── hooks/
    │   └── plan_policy_hook.py
    ├── hook-state/
    │   └── plan-policy-<session-id>.json
    └── rules/
        └── plan-artifact.rules

역할:

| 구성 | 역할 |
|---|---|
| `AGENTS.md` | 행동 정책 선언 |
| `config.toml` | Codex 설정 및 developer instruction |
| `hooks.json` | hook 등록 |
| `plan_policy_hook.py` | prompt/tool 실행 감지 및 차단 |
| `hook-state/` | 세션별 Ouroboros 승인 상태 저장 |
| `rules/` | shell command prefix 차단 |

---

## 11. Hook으로 강제할 항목

hook으로 강제하거나 보조할 수 있는 항목:

1. `/plan`, `plan mode`, `계획`, `PLAN-*` 등 planning prompt 감지
2. workflow 선택이 없으면 gating question context 주입
3. hard gate 모드에서는 prompt 자체 block 가능
4. `PLAN.md` 생성·수정 명령 차단
5. 잘못된 `PLAN-*.md` 파일명 차단
6. 승인 없는 `ouroboros`, `ooo interview`, `ooo run` 실행 차단
7. 세션 단위로 Ouroboros 승인 상태 저장

---

## 12. Hook 운영 모드

### Soft Gate

기본 권장 방식.

    plan prompt 감지
    → prompt를 막지는 않음
    → Codex에게 workflow 선택 질문을 반드시 하도록 context 주입

장점:

- UX가 자연스러움
- 사용자가 다시 입력할 필요가 적음

단점:

- Codex가 지침을 무시할 가능성이 완전히 0은 아님

### Hard Gate

강제성이 더 높음.

    plan prompt 감지
    → workflow 선택이 없으면 prompt block
    → 사용자가 다시 선택지를 포함해 입력해야 함

장점:

- 강제력 높음

단점:

- 사용성이 다소 불편
- 사용자가 한 번 더 입력해야 함

초기에는 soft gate를 권장하고, Codex가 gate를 자주 무시하면 hard gate로 전환한다.

---

## 13. PLAN.md 관련 판단

Hook/rule 정의에서 `PLAN.md`가 등장하는 것은 문제가 아니다.

이때 `PLAN.md`는 생성 대상이 아니라 금지 대상이다.

    허용:
    PLAN-2026-06-29-phase-0-4-claude-md.md

    차단:
    PLAN.md

따라서 hook/rule에서 `PLAN.md`를 감지하고 차단하는 것은 정상이다.

다만 추가 보강이 필요하다.

---

## 14. Hook 보강 권장 사항

기존 hook은 `PLAN.md` 차단에는 적절하다.

하지만 아래처럼 잘못된 `PLAN-*.md` 파일명을 차단하려면 추가 정규식이 필요하다.

차단해야 할 예시:

    PLAN-2026-06-29-Phase0.md
    PLAN-2026-06-29-phase_0_4.md
    PLAN-2026-06-29-계획.md
    PLAN-2026-06-29.md

허용해야 할 예시:

    PLAN-2026-06-29-phase-0-4-claude-md.md
    PLAN-2026-06-29-config-design.md
    PLAN-2026-06-29-data-pipeline-02.md

추가 권장 정규식:

    ANY_PLAN_FILENAME_RE = re.compile(
        r"\bPLAN-[^\s/;&|'\"]+\.md\b"
    )

`pre_tool_use()` 안에 추가할 검사:

    for m in ANY_PLAN_FILENAME_RE.finditer(command):
        filename = Path(m.group(0)).name
        if not VALID_PLAN_FILENAME_RE.fullmatch(filename):
            deny_pretool(
                f"Invalid plan artifact filename `{filename}`. "
                "Use `PLAN-YYYY-MM-DD-<feature-name>.md` with lowercase kebab-case feature name."
            )

최종 hook 역할:

- `PLAN.md` 차단
- invalid `PLAN-*.md` 차단
- 승인 없는 Ouroboros 차단
- plan mode gate context 주입

---

## 15. Rules 정의 방향

rules는 복잡한 파일명 검증보다 단순 shell command 차단에 적합하다.

권장 rules 역할:

- `touch PLAN.md` 차단
- `vim PLAN.md` 차단
- `nano PLAN.md` 차단
- `tee PLAN.md` 차단
- `ouroboros` CLI 실행은 prompt 처리

정밀한 filename validation은 hook에서 담당한다.

---

## 16. 최종 권장 구성

최종적으로는 아래 조합이 가장 적합하다.

    필수:
    - ~/.codex/AGENTS.md
    - ~/.codex/config.toml

    강화:
    - ~/.codex/hooks.json
    - ~/.codex/hooks/plan_policy_hook.py

    보조:
    - ~/.codex/rules/plan-artifact.rules

역할 분리:

    AGENTS.md
    → 전역 행동 정책

    config.toml
    → Codex developer instruction 및 plugin 설정

    hook
    → plan prompt 감지, workflow gate, PLAN.md 차단, Ouroboros 승인 상태 관리

    rules
    → 명백한 shell command 실수 차단

---

## 17. 현재까지 결론

현재까지의 설정 방향은 적절하다.

핵심 원칙:

    PLAN.md는 사용하지 않는다.
    PLAN-YYYY-MM-DD-<feature-name>.md를 사용한다.
    이 파일은 Ouroboros interview와 Superpowers brainstorming이 함께 수정하고 공유하는 planning artifact다.
    Ouroboros는 명시 승인 없이는 자동 실행하지 않는다.
    Plan mode 진입 시 workflow 선택 gate를 먼저 거친다.
    Implementation은 plan 승인 후에만 진행한다.

남은 작업:

1. 신규 `AGENTS.md`, `config.toml`을 `~/.codex/`에 적용
2. Codex 재시작
3. `/plan ...` 테스트
4. 필요 시 hook soft gate 적용
5. Codex가 gate를 무시하면 hard gate로 전환
6. `PLAN.md` 차단 및 invalid `PLAN-*.md` 차단 hook 보강
