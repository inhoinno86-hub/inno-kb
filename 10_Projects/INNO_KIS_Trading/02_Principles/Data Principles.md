---
type: concept
scope: project
project: INNO_KIS_Trading
area: principle
status: active
visibility: private
---

# Data Principles

## 목적

데이터 수집, 저장, 검증의 기본 원칙을 정리한다.

## 원칙

- `raw` 데이터는 수정하지 않는다.
- 계산 결과는 `interim` 또는 `processed`에서 관리한다.
- 출처와 수집 시점을 함께 남긴다.
- 핵심 계산은 재현 가능한 코드와 테스트로 검증한다.

## 확인 항목

- 데이터 출처
- 수집 주기
- 컬럼 정의
- 품질 검증 기준
