---
type: decision
scope: project
project: INNO_KIS_Trading
area: development
status: active
visibility: private
---

# Testing Policy

## 목적

계산, 데이터 정합성, 전략 로직에 대한 테스트 기준을 정리한다.

## 기본 원칙

- 수치 계산은 테스트 없이 머지하지 않는다.
- 백테스트 로직은 룩어헤드 바이어스를 검사한다.
- 입력 데이터 스키마는 검증한다.

## 우선 테스트 대상

- 지표 계산
- 필터링 규칙
- 스코어링
- 포지션 사이징
