---
type: concept
scope: project
project: INNO_KIS_Trading
area: project
status: active
visibility: private
---

# Knowledge Base Structure

## 목적

이 문서는 INNO_KIS_Trading 프로젝트 관련 노트를 어떤 기준으로 저장할지 정의한다.

## Vault 상위 구조 원칙

- `00_Inbox`: 아직 분류하지 않은 캡처 노트만 둔다.
- `10_Projects`: 특정 프로젝트에 종속된 개념, 결정, 리서치, 개발, 로그를 보관한다.
- `20_Research`: 여러 프로젝트에서 재사용할 공용 조사 노트를 둔다.
- `30_Concepts`: 여러 프로젝트에서 재사용할 공용 개념 노트를 둔다.
- `50_Decisions`: 프로젝트에 종속되지 않는 전역 의사결정과 운영 원칙을 둔다.
- `60_Templates`: Inbox 캡처와 정리용 템플릿을 둔다.
- `90_Archive`: 더 이상 활성 관리하지 않는 전역 자료를 둔다.

## INNO_KIS_Trading 내부 구조

```text
10_Projects/INNO_KIS_Trading/
├── 00_Inbox/
├── 01_Project/
├── 02_Principles/
├── 03_Research/
├── 04_Development/
├── 05_Experiments/
├── 06_Logs/
├── 07_References/
└── 99_Archive/
```

## 폴더별 역할

- `01_Project`: 프로젝트 개요, 운영 모델, 아키텍처, 로드맵, 결정 로그
- `02_Principles`: 투자, 데이터, AI 사용 원칙
- `03_Research`: 리서치 프레임워크와 템플릿
- `04_Development`: 코드/설정/데이터 파이프라인 설계
- `05_Experiments`: 백테스트, 스크리닝, 매매 실험 기록
- `06_Logs`: 일일 개발 로그, 에러 로그, 리서치 로그
- `07_References`: DART, KRX, 재무 지표, 전략 참고 메모
- `99_Archive`: 중복 초안, 폐기안, 과거 스냅샷

## 정리 규칙

- 프로젝트 관련 노트는 `scope: project`, `project: INNO_KIS_Trading`를 사용한다.
- 공용 지식만 `scope: global`로 분리한다.
- Inbox에서 정리할 때는 `area`를 함께 넣어 프로젝트 내부 세부 폴더까지 결정한다.
