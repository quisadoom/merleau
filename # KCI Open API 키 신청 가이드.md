# KCI Open API 키 신청 가이드

## 1단계: KRI 회원가입

KCI는 별도 회원가입이 없고, KRI(한국연구자정보)를 통해 가입합니다.

1. https://www.kri.go.kr 접속
2. 회원가입 클릭
3. 이름, 이메일, 비밀번호 등 입력하여 가입 완료

## 2단계: KCI 로그인

1. https://www.kci.go.kr 접속
2. 우측 상단 "로그인" 클릭
3. "개인회원" 선택 후 KRI에서 만든 아이디/비밀번호로 로그인

## 3단계: Open API 키 신청

1. 로그인 후 상단 메뉴에서 KCI 데이터 제공 > OPEN API 페이지로 이동
   (또는 직접 접속: https://www.kci.go.kr/kciportal/po/openapi/openApiList.kci)
2. 우측의 "OPEN API 키신청" 버튼 클릭
3. 활용 목적 등 간단한 정보 입력 후 신청

## 4단계: 키 확인 및 사용

발급된 키는 아래 형식으로 API 호출 시 사용합니다:

```
https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode=articleSearch&key=발급받은키&title=검색어
```

## 참고

- 신청 후 즉시 또는 1~2일 내 발급됩니다.
- 문의: kciadmin@nrf.re.kr / 042-869-6674