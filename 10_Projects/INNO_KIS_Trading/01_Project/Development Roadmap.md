# Development Roadmap

## 1. 전체 개발 로드맵

이 프로젝트는 아래 단계로 진행한다.

1. Stage 0. 프로젝트 기반 구축
2. Stage 1. 정량적 스크리너
3. Stage 2. AI 리서치
4. Stage 3. 최종 universe 선별
5. Stage 4. 매매 시스템
6. Stage 5. 백테스트 및 검증
7. Stage 6. 운영 자동화 및 개선

현재는 Stage 0만 진행한다.

---

## 2. Stage 0. 프로젝트 기반 구축

### 목표

본격 개발 전에 프로젝트의 원칙, 문서 구조, repo 구조, AI 사용 규칙, 데이터 저장 정책을 정의한다.

### Phase 0-1. 프로젝트 원칙 정의

담당 도구:

- ChatGPT
- Obsidian

산출물:

- Project Charter.md
- Development Roadmap.md
- System Architecture.md
- Decision Log.md

완료 기준:

- 프로젝트 목적이 명확히 정의되어 있다.
- AI 사용 범위가 명확히 정의되어 있다.
- 매수/매도 판단과 리서치가 분리되어 있다.
- 데이터 원칙이 명확히 정의되어 있다.
- 이후 개발 순서가 문서화되어 있다.

### Phase 0-2. GitHub Repo 생성

담당 도구:

- Codex CLI
- GitHub

산출물:

- GitHub repository
- README.md
- 기본 폴더 구조
- Python 프로젝트 구조
- .gitignore
- pyproject.toml 또는 requirements.txt

완료 기준:

- 로컬 또는 원격 GitHub repo가 생성되어 있다.
- 기본 폴더 구조가 생성되어 있다.
- README에 프로젝트 목적과 구조가 작성되어 있다.
- Python 실행 환경의 기본 구조가 준비되어 있다.

### Phase 0-3. AGENTS.md 작성

담당 도구:

- ChatGPT
- Codex CLI

산출물:

- AGENTS.md

완료 기준:

- Codex CLI가 지켜야 할 개발 규칙이 문서화되어 있다.
- 금융 데이터 임의 생성 금지 원칙이 명시되어 있다.
- 테스트 필수 원칙이 명시되어 있다.
- raw data 수정 금지 원칙이 명시되어 있다.
- config 기반 설계 원칙이 명시되어 있다.

### Phase 0-4. CLAUDE.md 작성

담당 도구:

- ChatGPT
- Claude Code

산출물:

- CLAUDE.md

완료 기준:

- Claude Code와 AI Berkshire의 사용 범위가 명확히 정의되어 있다.
- AI Berkshire는 리서치 전용으로 제한되어 있다.
- 매수/매도 지시 문구가 금지되어 있다.
- 리서치 리포트 구조가 정의되어 있다.
- 핵심 수치의 출처 표시 원칙이 명시되어 있다.

### Phase 0-5. config 파일 정의

담당 도구:

- ChatGPT
- Codex CLI

산출물:

- config/universe.yaml
- config/screener.yaml
- config/research_score.yaml
- config/trading_rules.yaml
- config/risk.yaml
- config/data_sources.yaml

완료 기준:

- 주요 기준값이 코드가 아니라 config에서 관리된다.
- 스크리너 조건이 config로 분리되어 있다.
- 리서치 점수화 기준이 config로 분리되어 있다.
- 매매 규칙이 config로 분리되어 있다.
- 리스크 관리 기준이 config로 분리되어 있다.
- 데이터 출처가 config로 명시되어 있다.

### Phase 0-6. 데이터 저장 정책 정의

담당 도구:

- ChatGPT
- Obsidian
- Codex CLI

산출물:

- data/raw/
- data/interim/
- data/processed/
- data/external/
- reports/screening/
- reports/research/
- reports/universe/
- reports/backtest/
- Data Policy.md

완료 기준:

- raw data 수정 금지 원칙이 문서화되어 있다.
- 데이터 단계별 저장 위치가 정의되어 있다.
- 리포트 저장 위치가 정의되어 있다.
- 파일명 규칙이 정의되어 있다.
- Git 추적 대상과 제외 대상이 구분되어 있다.

---

## 3. Stage 1. 정량적 스크리너

### 목표

국내 전체 종목에서 정량 기준을 적용해 후보 30개를 선별한다.

### 주요 작업

- 국내 상장 종목 universe 수집
- 거래정지, 관리종목, SPAC 등 제외 기준 정의
- 재무 데이터 수집
- 가격 데이터 수집
- 스크리너 기준 정의
- 점수화 로직 구현
- 후보 30개 산출
- screening report 생성

### 완료 기준

- 동일한 config와 동일한 데이터로 동일한 후보 30개가 재현된다.
- 각 후보 종목의 선정 사유가 기록된다.
- 모든 수치의 출처가 기록된다.

---

## 4. Stage 2. AI 리서치

### 목표

후보 30개에 대해 AI Berkshire식 정성 리서치를 수행한다.

### 주요 작업

- 기업별 리서치 자료 수집
- DART 공시 확인
- KRX 자료 확인
- 기업 IR 자료 확인
- 사업모델 분석
- 해자 분석
- 재무 품질 분석
- 현금흐름 분석
- 밸류에이션 검토
- 경영진 검토
- 리스크 및 실패 시나리오 작성
- 투자 가치 점수화

### 완료 기준

- 후보 종목별 Markdown 리포트가 생성된다.
- 핵심 수치에 출처가 표시된다.
- 불확실한 정보는 “확인 불가”로 표시된다.
- 매수/매도 지시 문구가 포함되지 않는다.

---

## 5. Stage 3. 최종 universe 선별

### 목표

정량 점수와 AI 리서치 점수를 함께 검토하여 상위 5~10개 관심 종목을 등록한다.

### 주요 작업

- 정량 점수와 정성 점수 결합
- 관심 universe 선정
- 선정 사유 기록
- 제외 사유 기록
- universe report 생성

### 완료 기준

- 관심 universe가 Markdown 또는 CSV로 저장된다.
- 각 종목의 편입 사유가 기록된다.
- 제외 종목의 제외 사유가 기록된다.
- 관심 universe 등록이 자동 매수 신호가 아님을 명시한다.

---

## 6. Stage 4. 매매 시스템

### 목표

관심 universe에 대해서만 규칙 기반 진입/청산 시스템을 설계한다.

### 주요 작업

- 기술적 진입 조건 정의
- ATR 기반 손절 규칙 정의
- 트레일링 스탑 규칙 정의
- 시장 국면별 비중 조절 규칙 정의
- 포지션 사이징 정의
- 리스크 제한 정의
- 백테스트 구현
- 실거래 전 검증

### 완료 기준

- 진입 조건과 청산 조건이 명확히 분리되어 있다.
- 모든 매매 규칙이 config에서 관리된다.
- 백테스트 결과가 재현 가능하다.
- 과최적화 방지 원칙이 반영되어 있다.

---

## 7. 현재 작업 상태

| 날짜 | Stage | Phase | 상태 | 메모 |
|---|---|---|---|---|
| 2026-06-27 | Stage 0 | Phase 0-1 | 진행 중 | 프로젝트 문서 초안 작성 |