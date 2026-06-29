---
type: decision
project: Codex-Workflow
status: inbox
visibility: private
---
# Codex 전역 Superpowers Workflow 설정 정리

작성일: 2026-06-29  
대상 경로: `~/.codex/`  
대상 도구: Codex CLI + Superpowers Plugin  
목적: 본 PC에서 실행되는 모든 Codex 프로젝트에 전역 개발 workflow 적용

---

## 1. 목적

Claude Code에서 활용하던 Superpowers plugin을 Codex CLI에도 적용하고, 본 PC에서 진행되는 모든 Codex 프로젝트에 대해 전역 개발 workflow를 통일하는 것을 목표로 설정을 검토했다.

최종 목표는 다음과 같다.

- Codex 전역 설정 경로 `~/.codex/` 기준으로 모든 프로젝트에 동일한 작업 규칙 적용
- `/plan` 사용 시 Superpowers brainstorming 사용 여부를 먼저 질문
- 사용자가 Superpowers brainstorming 사용을 선택한 경우에만 `brainstorming` 및 `writing-plans` 수행
- planning 결과물은 기존 `PLAN.md`가 아니라 `PLAN-YYYY-MM-DD-<feature-name>.md` 형식으로 생성
- 하루에 여러 번 planning을 수행할 수 있으므로 plan 파일을 날짜 + feature 단위로 구분
- execution phase에서는 Superpowers의 주요 실행/검증/리뷰 관련 skill을 전역 규칙으로 강제
- `finishing-a-development-branch`는 branch 관리를 별도로 할 예정이므로 자동 수행 금지
- `writing-skills`는 필요 시 수동 호출

---

## 2. 확인한 전제

### 2.1 Superpowers plugin의 Codex 적용 가능 여부

Superpowers는 Claude Code 전용 plugin만 제공하는 것이 아니라 Codex용 plugin 구조도 제공한다.

Codex에서는 `/plugins` 명령을 통해 Superpowers plugin을 설치할 수 있으며, 설치 후 `/skills`에서 사용 가능한 skill 목록을 확인할 수 있다.

Codex에서의 Superpowers 사용은 Claude Code와 100% 동일한 UX는 아니지만, 주요 workflow는 Codex의 skill/plugin 구조를 통해 사용할 수 있다.

### 2.2 Codex 전역 설정 경로

Codex 전역 설정은 기본적으로 아래 경로를 사용한다.

    ~/.codex/
    ├── AGENTS.md
    └── config.toml

각 파일의 역할은 다음과 같다.

- `~/.codex/AGENTS.md`
  - 본 PC에서 실행되는 Codex 작업 전반에 적용되는 전역 instruction 파일
  - 모든 프로젝트에 공통 적용할 작업 규칙을 정의하기 적합함

- `~/.codex/config.toml`
  - Codex 사용자 레벨 설정 파일
  - `developer_instructions`, sandbox, approval policy, skill 설정 등을 보조적으로 정의 가능함

---

## 3. 기존 전역 파일 기준 검토

기존 `~/.codex/AGENTS.md`에는 다음 내용이 있었다.

### 3.1 Default Behavior

- 최소 변경 우선
- 관련 파일 확인 후 수정
- 기존 프로젝트 스타일 준수
- 불필요한 dependency 추가 금지
- 코드 변경 후 관련 검증 명령 실행
- 검증 불가 시 이유 명시

### 3.2 Final Response

- 변경 사항 요약
- 검증 사항 요약
- 남은 리스크/가정 명시

### 3.3 Always-on Caveman Response Mode

- 기본적으로 concise mode 유지
- 한국어 요청 시 한국어 응답
- 불필요한 filler 제거
- 기술 용어, 경로, 명령어, config key는 정확히 유지
- 코드 작업 시에도 검토, 수정, 테스트, 검증 보고는 명확히 수행

기존 내용은 유지하고, 그 위에 Superpowers 기반 planning/execution 정책을 추가하는 방향으로 정리했다.

---

## 4. Superpowers skill 역할 정리

현재 검토한 Superpowers 주요 skill은 다음과 같다.

---

### 4.1 `using-superpowers`

Superpowers 전체 사용 원칙을 정의하는 bootstrap 성격의 skill.

역할:

- 현재 작업에 적용 가능한 Superpowers skill이 있으면 사용하도록 유도
- 단, 사용자 지시, 프로젝트 `AGENTS.md`, `CLAUDE.md`, repo 규칙보다 우선하지 않음
- Superpowers workflow를 적용할 수 있는 작업인지 판단하는 기준점 역할

정책:

- 전역 규칙으로 항상 참고 가능
- 단, 사용자 전역 정책과 프로젝트 안전 규칙이 우선
- Superpowers가 설치되어 있더라도 모든 skill을 무조건 호출하는 방식은 아님

---

### 4.2 `brainstorming`

구현 전 요구사항, 목적, 제약, 접근안을 정리하는 skill.

역할:

- 바로 구현하지 않고 먼저 문제 정의
- 사용자의 실제 목표와 constraints 파악
- 가능한 접근안 및 trade-off 정리
- 설계 방향 확정
- 구현 전 불필요한 시행착오 방지

정책:

- `/plan`에서 무조건 실행하지 않음
- 먼저 사용자에게 Superpowers brainstorming 사용 여부를 질문
- 사용자가 “예”라고 답한 경우에만 실행
- 결과는 별도 design 문서가 아니라 `PLAN-YYYY-MM-DD-<feature-name>.md` 안에 함께 정리

---

### 4.3 `writing-plans`

brainstorming 결과를 실제 실행 가능한 plan으로 변환하는 skill.

역할:

- 실행 단계를 세분화
- 수정 대상 파일, 검증 명령, rollback 전략 등을 포함한 구현 계획 작성
- 다른 Codex 세션에서도 이어서 수행 가능한 수준으로 plan 작성
- execution phase의 기준 문서 생성

정책:

- brainstorming이 활성화된 경우에만 수행
- 일반 plan mode에서는 `writing-plans`를 호출하지 않음
- 결과물은 `PLAN-YYYY-MM-DD-<feature-name>.md`
- 같은 날짜/같은 feature로 중복될 경우 `-02`, `-03` suffix 사용 가능

예시 파일명:

    PLAN-2026-06-29-codex-superpowers-global-workflow.md
    PLAN-2026-06-29-kis-config-loader.md
    PLAN-2026-06-29-kis-config-loader-02.md

---

### 4.4 `executing-plans`

작성된 plan 파일을 기준으로 실제 작업을 수행하는 skill.

역할:

- plan 파일 읽기
- plan의 task 순서대로 실행
- scope 변경 필요 시 plan 갱신 및 승인 요청
- 실행 결과와 검증 결과 기록

정책:

- execution phase에서 plan 파일이 존재하면 반드시 적용
- `PLAN-YYYY-MM-DD-<feature-name>.md`가 execution source of truth가 됨
- plan 범위를 벗어나는 작업은 수행하지 않음

---

### 4.5 `subagent-driven-development`

계획의 각 task를 독립 subagent로 나누어 수행하는 skill.

역할:

- task별 구현 agent 분리
- 각 task 완료 후 review agent를 통해 검토
- 큰 feature를 구조적으로 수행
- 구현과 리뷰를 분리하여 품질 향상

정책:

- execution phase에서 적용 가능하면 사용
- Codex 환경이나 작업 규모상 부적합하면 `N/A` 사유 기록
- 대형 기능 개발, 리팩터링, 테스트 추가에 유용

---

### 4.6 `dispatching-parallel-agents`

독립적인 문제를 병렬 agent에게 나누어 처리하는 skill.

역할:

- 독립적인 테스트 실패, 독립 모듈 수정, 다중 분석 작업을 병렬 처리
- 서로 충돌하지 않는 작업 단위에 적합
- 병렬 탐색이나 독립 이슈 해결 시 효율 향상

정책:

- execution phase에서 독립 작업이 2개 이상이면 적용
- 단일 root cause 가능성이 높거나 같은 파일을 동시에 수정할 위험이 있으면 사용하지 않음
- 사용하지 않을 경우 `N/A` 사유 기록

---

### 4.7 `test-driven-development`

TDD 방식으로 구현 전 실패 테스트를 먼저 작성하는 skill.

역할:

- 실패 테스트 작성
- 테스트 실패 확인
- 최소 구현
- 테스트 통과 확인
- 리팩터링

정책:

- 코드 동작 변경이 있는 execution phase에서 필수
- 단순 문서 수정, 설정 문구 수정 등 테스트가 불필요한 경우 `N/A` 사유 기록
- 금융/자동매매 프로젝트에서는 fabricated financial data 금지 원칙을 유지해야 함
- 테스트 결과를 추측하거나 지어내면 안 됨

---

### 4.8 `systematic-debugging`

버그 수정 전 root cause를 먼저 찾도록 하는 skill.

역할:

- 에러 메시지 확인
- 재현 조건 확인
- 최근 변경 확인
- instrumentation 추가
- root cause 확정 후 수정

정책:

- 버그, 테스트 실패, 예상 밖 동작, 성능 문제 발생 시 필수
- 단순 추측성 수정 금지
- 원인 없이 sleep 추가, 예외 무시, 임시 조건문 추가 금지
- root cause가 확인되지 않으면 완료로 보고하지 않음

---

### 4.9 `verification-before-completion`

완료 주장 전 실제 검증을 강제하는 skill.

역할:

- 완료 전 검증 명령 식별
- 실제 명령 실행
- exit code 및 결과 확인
- 검증 결과 기반으로만 완료 보고

정책:

- execution phase 종료 전 항상 필수
- 검증을 실행하지 못한 경우 이유를 명확히 기록
- 테스트 결과, benchmark 결과, 실행 결과를 추측하거나 지어내면 안 됨
- “아마 통과할 것” 같은 표현 금지

---

### 4.10 `requesting-code-review`

작업 후 code review를 요청하는 skill.

역할:

- diff 기준 review 요청
- 요구사항 충족 여부 확인
- critical/important/minor issue 분리
- 수정 필요 사항 반영

정책:

- non-trivial code change가 있는 execution phase에서 필수
- 단순 문서 수정 등에는 `N/A` 가능
- 자동매매/금융 관련 코드는 특히 review gate를 강하게 적용

---

### 4.11 `receiving-code-review`

review feedback을 받았을 때 무비판적으로 수용하지 않고 검증하는 skill.

역할:

- 리뷰 의견 읽기
- 코드와 요구사항 기준으로 검증
- 맞는 지적은 반영
- 틀린 지적은 근거를 들어 반박

정책:

- review feedback이 존재하는 경우 필수
- “맞습니다” 식의 무조건 동의 금지
- 기술적 정확성과 프로젝트 규칙 우선

---

### 4.12 `using-git-worktrees`

작업 branch를 별도 worktree로 분리하는 skill.

역할:

- 기능 개발을 독립 workspace에서 수행
- 기존 작업공간 오염 방지
- 병렬 작업 관리

정책:

- execution phase 진입 전 사용 여부 평가
- 실제 worktree 생성은 사용자 승인 필요
- 단순 작업에는 `N/A` 가능
- branch 관리는 별도 계획이 있으므로 자동 branch finishing과는 분리

---

### 4.13 `finishing-a-development-branch`

개발 branch 완료 후 merge, PR, discard, cleanup 등을 수행하는 skill.

정책:

- 현재 설정에서는 자동 수행 금지
- branch 관리는 별도로 진행할 예정
- Codex가 임의로 merge, push, PR 생성, branch 삭제를 수행하면 안 됨
- 필요 시 사용자가 명시적으로 요청한 경우에만 별도 검토

---

### 4.14 `writing-skills`

새로운 Superpowers skill을 작성하거나 기존 skill을 수정하는 meta skill.

정책:

- 전역 자동 수행 대상 아님
- 필요 시 사용자가 명시적으로 호출
- 반복 작업이 안정화된 뒤 개인 custom skill을 만들 때 활용 가능

---

## 5. 최종 Workflow 정책

### 5.1 Plan Mode 기본 동작

`/plan` 입력 시 Codex는 바로 planning을 시작하지 않고 먼저 질문해야 한다.

질문 예시:

    Superpowers brainstorming을 사용해서 계획을 만들까요?

    - 예: Superpowers brainstorming → PLAN-YYYY-MM-DD-<feature-name>.md 생성/갱신 → 승인 후 실행
    - 아니오: 일반 Codex plan mode → 승인 후 실행

---

### 5.2 사용자가 “예”라고 답한 경우

수행 흐름:

    /plan
      ↓
    Superpowers brainstorming 사용 여부 질문
      ↓
    사용자: 예
      ↓
    brainstorming 수행
      ↓
    writing-plans 수행
      ↓
    PLAN-YYYY-MM-DD-<feature-name>.md 생성
      ↓
    사용자 승인
      ↓
    execution phase

생성되는 plan 파일 형식:

    PLAN-YYYY-MM-DD-<feature-name>.md

예시:

    PLAN-2026-06-29-codex-superpowers-global-workflow.md

파일 안에는 최소한 다음 항목을 포함한다.

    # PLAN-YYYY-MM-DD-<feature-name>

    ## 1. Goal

    ## 2. Brainstorming Summary

    ## 3. Context Discovered

    ## 4. Non-goals

    ## 5. Assumptions

    ## 6. Constraints and Safety Rules

    ## 7. Expected Files to Read or Modify

    ## 8. Implementation Tasks

    ## 9. Validation and Test Commands

    ## 10. Rollback Plan

    ## 11. Progress Log

    ## 12. Decision Log

    ## 13. Open Questions

---

### 5.3 사용자가 “아니오”라고 답한 경우

수행 흐름:

    /plan
      ↓
    Superpowers brainstorming 사용 여부 질문
      ↓
    사용자: 아니오
      ↓
    일반 Codex plan mode
      ↓
    필요 시 텍스트 계획만 제시
      ↓
    사용자 승인 후 execution

정책:

- `brainstorming` 호출하지 않음
- `writing-plans` 호출하지 않음
- 반드시 plan 파일을 생성하지 않아도 됨
- 단, 작업이 복잡하거나 장기 작업이면 일반 plan mode에서도 plan 파일 생성을 제안 가능

---

## 6. Execution Phase 전역 강제 정책

execution phase에서는 다음 skill을 반드시 적용하거나, 적용 불가 시 `N/A` 사유를 명시한다.

### 6.1 Execution Phase Skill Checklist

    ## Execution Phase Superpowers Checklist

    - [ ] executing-plans 적용 또는 N/A 사유 기록
    - [ ] subagent-driven-development 적용 또는 N/A 사유 기록
    - [ ] dispatching-parallel-agents 적용 또는 N/A 사유 기록
    - [ ] test-driven-development 적용 또는 N/A 사유 기록
    - [ ] systematic-debugging 적용 또는 N/A 사유 기록
    - [ ] verification-before-completion 적용
    - [ ] requesting-code-review 적용 또는 N/A 사유 기록
    - [ ] receiving-code-review 적용 또는 N/A 사유 기록
    - [ ] using-git-worktrees 적용 여부 평가 및 N/A 사유 기록
    - [ ] finishing-a-development-branch 자동 수행 금지 확인
    - [ ] writing-skills 미호출 확인

### 6.2 핵심 실행 규칙

- plan 파일이 있으면 반드시 먼저 읽는다.
- plan 파일은 execution source of truth로 사용한다.
- plan 범위를 벗어나는 구현은 하지 않는다.
- scope 변경이 필요하면 plan을 갱신하고 사용자 승인 후 진행한다.
- 검증 없이 완료를 주장하지 않는다.
- branch merge, push, PR, cleanup은 사용자 명시 요청 없이는 하지 않는다.
- `finishing-a-development-branch`는 자동 수행하지 않는다.
- `writing-skills`는 사용자 명시 요청 없이는 호출하지 않는다.

---

## 7. 작성한 신규 설정 파일

기존 `~/.codex/AGENTS.md`와 `~/.codex/config.toml`을 바탕으로 아래 신규 파일을 작성했다.

    AGENTS.superpowers.phase-policy.md
    config.superpowers.phase-policy.toml

### 7.1 `AGENTS.superpowers.phase-policy.md`

역할:

- 전역 Codex 작업 규칙 정의
- 기존 Default Behavior, Final Response, Caveman Response Mode 유지
- plan mode에서 Superpowers brainstorming 사용 여부 질문
- brainstorming 선택 시에만 `brainstorming` + `writing-plans` 수행
- plan 파일명을 `PLAN-YYYY-MM-DD-<feature-name>.md`로 정의
- execution phase에서 4~12번 skill 적용 또는 N/A 사유 기록
- 13번 `finishing-a-development-branch` 자동 수행 금지
- 14번 `writing-skills` 수동 호출 전용

### 7.2 `config.superpowers.phase-policy.toml`

역할:

- Codex config 보조 설정
- `developer_instructions`를 통해 동일 정책을 한 번 더 강조
- 기존 sandbox/approval/plugin 관련 설정을 유지 또는 보조
- TOML 파싱 검증 완료

---

## 8. 실제 적용 명령어

현재 파일을 다운로드한 뒤 아래 명령으로 적용한다.

    cp ~/.codex/AGENTS.md ~/.codex/AGENTS.md.bak.$(date +%Y%m%d_%H%M%S)
    cp ~/.codex/config.toml ~/.codex/config.toml.bak.$(date +%Y%m%d_%H%M%S)

    cp ~/Downloads/AGENTS.superpowers.phase-policy.md ~/.codex/AGENTS.md
    cp ~/Downloads/config.superpowers.phase-policy.toml ~/.codex/config.toml

파일 경로가 `~/Downloads`가 아니라면 실제 저장 경로로 변경한다.

적용 후 기존 Codex 세션은 종료하고 새로 시작한다.

---

## 9. 설정 확인 방법

Codex 새 세션에서 다음 명령을 사용한다.

    /status
    /skills
    /plugins

전역 instruction이 제대로 반영되는지 확인하려면 다음과 같이 요청한다.

    codex --ask-for-approval never "Summarize the current instructions. Confirm whether plan mode asks before using Superpowers brainstorming and whether execution phase uses the Superpowers checklist."

기대 응답:

    - /plan 사용 시 Superpowers brainstorming 사용 여부를 먼저 질문한다.
    - 사용자가 yes를 선택한 경우에만 brainstorming과 writing-plans를 수행한다.
    - plan 파일은 PLAN-YYYY-MM-DD-<feature-name>.md 형식으로 생성한다.
    - execution phase에서는 executing-plans, TDD, debugging, verification, review 관련 checklist를 적용한다.
    - finishing-a-development-branch는 자동 수행하지 않는다.
    - writing-skills는 명시 요청 시에만 사용한다.

---

## 10. 현재까지의 최종 결정 사항

### 결정 1

Superpowers plugin은 Codex에도 적용 가능하다.

### 결정 2

전역 적용은 `~/.codex/AGENTS.md` 중심으로 한다.

### 결정 3

`/plan`에서는 Superpowers brainstorming을 무조건 사용하지 않고, 먼저 사용자에게 사용 여부를 질문한다.

### 결정 4

`writing-plans`는 brainstorming이 활성화된 경우에만 수행한다.

### 결정 5

planning 결과물은 `PLAN.md`가 아니라 `PLAN-YYYY-MM-DD-<feature-name>.md`로 생성한다.

### 결정 6

brainstorming 결과와 writing-plans 결과는 같은 plan 파일에 통합한다.

### 결정 7

execution phase에서는 4~12번 Superpowers skill을 필수 적용하거나 N/A 사유를 기록한다.

### 결정 8

`finishing-a-development-branch`는 자동 수행하지 않는다.

### 결정 9

`writing-skills`는 필요 시 수동 호출한다.

### 결정 10

branch 관리는 Superpowers 자동 branch finishing이 아니라 사용자가 별도 전략으로 관리한다.

---

## 11. 남은 확인 사항

- 실제 설치된 Superpowers skill 이름이 GitHub 기준과 동일한지 `/skills`에서 확인 필요
- Codex가 전역 `AGENTS.md`의 plan mode gate를 항상 잘 따르는지 실제 `/plan` 테스트 필요
- `finishing-a-development-branch`를 완전히 비활성화할지, 전역 지침으로만 금지할지 최종 선택 필요
- `PLAN-YYYY-MM-DD-<feature-name>.md` 파일을 repo root에 둘지, 별도 `docs/plans/` 경로에 둘지 프로젝트별 선호 확인 가능
- execution phase checklist를 plan 파일 내부에 자동 포함하도록 더 강하게 지시할지 검토 가능

---

## 12. 개인 운영 기준 초안

앞으로 Codex 작업은 아래 흐름으로 진행한다.

    1. 신규 작업 요청
    2. /plan 사용
    3. Codex가 Superpowers brainstorming 사용 여부 질문
    4. 중요한 작업이면 “예”
    5. 가벼운 작업이면 “아니오”
    6. Superpowers 사용 시 PLAN-YYYY-MM-DD-<feature-name>.md 생성
    7. plan 승인
    8. execution phase 진입
    9. execution checklist 기반 수행
    10. 검증 결과 확인
    11. 리뷰 결과 확인
    12. 완료 요약

내 기준에서는 다음과 같이 구분한다.

    가벼운 수정:
    - 일반 plan mode
    - 별도 plan 파일 없이 진행 가능

    중요한 기능 개발:
    - Superpowers brainstorming 사용
    - writing-plans 사용
    - PLAN-YYYY-MM-DD-<feature-name>.md 생성

    자동매매/금융/데이터 관련 작업:
    - Superpowers brainstorming 사용 권장
    - PLAN 파일 필수
    - TDD, verification, code review gate 필수
    - fabricated data, secrets, live order 관련 안전 규칙 최우선

---

## 13. 참고 출처

- Codex AGENTS.md Guide
  - https://developers.openai.com/codex/guides/agents-md

- Codex Config Reference
  - https://developers.openai.com/codex/config-reference

- Codex Skills
  - https://developers.openai.com/codex/skills

- Codex Plugins
  - https://developers.openai.com/codex/plugins

- Codex Slash Commands
  - https://developers.openai.com/codex/cli/slash-commands

- Codex Subagents
  - https://developers.openai.com/codex/subagents

- Superpowers GitHub Repository
  - https://github.com/obra/Superpowers