---
type: project
scope: project
project: INNO_KIS_Trading
area: project
status: active
visibility: private
---

# System Architecture

## 1. 시스템 개요

INNO_KIS_Trading은 국내 주식 대상 리서치 및 규칙 기반 매매 시스템이다.

시스템은 아래 흐름으로 구성된다.

```text
국내 전체 종목
    ↓
Stage 1. 정량적 스크리너
    ↓
후보 30개
    ↓
Stage 2. AI 리서치
    ↓
투자 가치 점수화
    ↓
Stage 3. 관심 universe 선별
    ↓
상위 5~10개 관심 종목
    ↓
Stage 4. 규칙 기반 매매 시스템
    ↓
진입 / 손절 / 트레일링 스탑 / 비중 조절
```

---

## 2. 핵심 설계 원칙

### 2.1 리서치와 매매의 분리

AI 리서치는 투자 가능한 universe를 고급화하는 필터로만 사용한다.

AI 리서치 결과가 직접 매수 또는 매도 신호가 되어서는 안 된다.

매매 시스템은 별도의 규칙 기반 조건으로 작동한다.

### 2.2 데이터와 로직의 분리

스크리너 기준, 리서치 점수 기준, 매매 규칙, 리스크 기준은 코드에 직접 박아넣지 않는다.

모든 기준값은 config 파일에서 관리한다.

### 2.3 원본 데이터 보호

raw data는 수정하지 않는다.

원본 데이터는 수집 시점, 출처, 파일명, 수집 방법을 함께 기록한다.

가공 데이터는 interim 또는 processed 영역에 별도로 저장한다.

### 2.4 재현성

동일한 데이터와 동일한 config를 사용하면 동일한 결과가 나와야 한다.

모든 계산 로직은 테스트 코드로 검증한다.

### 2.5 편향 방지

아래 편향을 방지한다.

- 룩어헤드 바이어스
- 생존자 편향
- 과최적화
- 데이터 스누핑
- 임의 데이터 생성

---

## 3. 도구별 역할

### 3.1 ChatGPT

역할:

- 전체 계획 수립
- 단계별 수행 방법 안내
- Obsidian 문서 초안 작성
- Codex CLI 입력 프롬프트 작성
- Claude Code 입력 프롬프트 작성
- 작업 결과 검토 기준 제시

사용 위치:

- Stage 0 전체
- 각 Stage의 설계 단계
- 문서 초안 작성
- 개발 방향 검토

제한:

- 검증되지 않은 금융 데이터를 임의로 생성하지 않는다.
- 투자 수익률을 보장하지 않는다.
- 매수/매도 지시를 하지 않는다.

### 3.2 Obsidian

역할:

- 프로젝트 헌장 관리
- 개발 로드맵 관리
- 시스템 아키텍처 관리
- 의사결정 로그 관리
- 데이터 정책 관리
- 실험 기록 관리
- 투자 원칙 기록

주요 문서:

- Project Charter.md
- Development Roadmap.md
- System Architecture.md
- Decision Log.md
- Data Policy.md
- Investment Principles.md
- AI Usage Principles.md

### 3.3 Codex CLI

역할:

- GitHub Repo 구조 생성
- Python 프로젝트 구조 생성
- AGENTS.md 작성
- config/*.yaml 초안 작성
- 데이터 저장 구조 설계
- 실제 코드 개발
- 테스트 코드 작성
- 리팩토링

제한:

- 금융 데이터를 임의 생성하지 않는다.
- raw data를 수정하지 않는다.
- 계산 로직에는 반드시 테스트를 작성한다.
- 기준값은 config에서 관리한다.
- 투자 조언 문구를 생성하지 않는다.

### 3.4 Claude Code

역할:

- AI Berkshire 리서치 프레임워크 운영
- CLAUDE.md 작성
- 후보 종목 리서치 리포트 생성
- 기업 분석 보고서 작성
- 정성 리서치 점수화

제한:

- AI Berkshire는 리서치 전용으로 사용한다.
- 매수/매도 지시를 하지 않는다.
- 핵심 수치에는 출처를 표시한다.
- 불확실한 정보는 “확인 불가”로 표기한다.
- AI가 확신할 수 없는 내용은 추정하지 않는다.

### 3.5 AI Berkshire

역할:

- 워렌 버핏, 찰리 멍거, 돤융핑, 리루식 관점의 기업 분석 프레임워크
- 기업의 장기 경쟁력 검토
- 해자, 자본배분, 현금흐름, 경영진, 실패 시나리오 검토

제한:

- 매수/매도 판단기가 아니다.
- 자동매매 신호 생성기가 아니다.
- 정성 리서치 필터로만 사용한다.

---

## 4. 예상 GitHub Repository 구조

```text
inno-kis-trading/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── pyproject.toml
├── .gitignore
├── config/
│   ├── universe.yaml
│   ├── screener.yaml
│   ├── research_score.yaml
│   ├── trading_rules.yaml
│   ├── risk.yaml
│   └── data_sources.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── docs/
│   ├── project/
│   ├── architecture/
│   ├── data_policy/
│   └── research_policy/
├── notebooks/
├── reports/
│   ├── screening/
│   ├── research/
│   ├── universe/
│   └── backtest/
├── scripts/
├── src/
│   └── inno_kis_trading/
│       ├── __init__.py
│       ├── data/
│       ├── screening/
│       ├── research/
│       ├── universe/
│       ├── trading/
│       ├── backtest/
│       ├── reporting/
│       └── utils/
└── tests/
    ├── test_data/
    ├── test_screening/
    ├── test_trading/
    └── test_backtest/
```

---

## 5. 데이터 흐름

```text
외부 데이터 출처
    ↓
data/raw/
    ↓
data/interim/
    ↓
data/processed/
    ↓
Stage 1. Screener
    ↓
reports/screening/
    ↓
Stage 2. AI Research
    ↓
reports/research/
    ↓
Stage 3. Universe
    ↓
reports/universe/
    ↓
Stage 4. Trading / Backtest
    ↓
reports/backtest/
```

---

## 6. 주요 모듈 구조

### 6.1 data module

역할:

- 데이터 수집
- 원본 데이터 저장
- 데이터 로딩
- 데이터 검증
- 데이터 가공

주의:

- raw data는 수정하지 않는다.
- 가공 결과는 interim 또는 processed에 저장한다.

### 6.2 screening module

역할:

- 정량 스크리너 실행
- config 기반 필터 적용
- 후보 30개 선별
- screening report 생성

주의:

- 스크리너 기준은 코드가 아니라 config에서 관리한다.

### 6.3 research module

역할:

- AI 리서치 입력 데이터 정리
- Claude Code 리서치 결과 저장
- research score 관리

주의:

- AI 리서치는 매수/매도 지시를 생성하지 않는다.

### 6.4 universe module

역할:

- 최종 관심 universe 관리
- 편입/제외 사유 기록
- universe report 생성

주의:

- universe 등록은 자동 매수 신호가 아니다.

### 6.5 trading module

역할:

- 기술적 진입 조건
- ATR 손절
- 트레일링 스탑
- 시장 국면별 비중 조절
- 포지션 사이징

주의:

- 매매 규칙은 config에서 관리한다.
- 실거래 전 반드시 백테스트와 검증을 수행한다.

### 6.6 backtest module

역할:

- 전략 백테스트
- 룩어헤드 바이어스 방지
- 수수료 및 슬리피지 반영
- 성과 지표 산출
- backtest report 생성

주의:

- 과최적화를 방지한다.
- 검증 기간과 학습 기간을 분리한다.

### 6.7 reporting module

역할:

- Markdown 리포트 생성
- CSV 결과 저장
- 실험 결과 요약
- 출처 정보 기록

---

## 7. 데이터 출처 우선순위

국내 주식 분석 시 데이터 출처 우선순위는 아래와 같다.

1. DART
2. KRX
3. KIND
4. 기업 IR 자료
5. 기업 공식 홈페이지
6. 증권사 리포트
7. 기타 공개 데이터

출처가 명확하지 않은 데이터는 사용하지 않는다.

---

## 8. 현재 아키텍처 상태

- Stage 0 기준 설계 단계
- 실제 데이터 수집 모듈 미구현
- 실제 스크리너 미구현
- 실제 리서치 자동화 미구현
- 실제 매매 시스템 미구현
- 현재 목표는 원칙, 구조, 정책, config 설계 확정
