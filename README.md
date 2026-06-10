# 🚗 Merleau-Ponty Research Dashboard

모리스 메를로-퐁티(Maurice Merleau-Ponty)의 생애 및 철학, 관련 연구 동향을 분석하기 위해 한국연구재단(KCI) 데이터를 기반으로 제작된 **논문 데이터 통계 및 시각화 대시보드**입니다.

## 📌 주요 기능 (Features)
본 대시보드는 KCI에서 추출된 600여 건의 학술 데이터를 분석하여 직관적인 렌더링 뷰를 제공합니다.
- **Total Insight:** 연도별 논문 발행 빈도(막대그래프) 및 메를로-퐁티 학파의 학계 파급력/인용수(선그래프) 트렌드 분석
- **Concept Map:** 한국어 초록/키워드 형태소 분석을 통한 탑 티어 명사(개념어) 빈도 차트 및 철학적 워드클라우드 제공
- **People & Journal:** 주요 연구 논문 최다 산출 저자 랭킹 차트 및 메인스트림 학술지 비율 도넛 차트
- **Research Library:** 문헌별 인용수 기반 내림차순 정렬 및 초록을 검색/열람할 수 있는 상세 데이터 테이블

## 🛠️ 사용 기술 (Tech Stack)
- **Frontend / Dashboard Framework:** `Streamlit`
- **Data Engineering:** `pandas`, `xlrd` (KCI Excel Processing)
- **Data Visualization:** `Plotly`, `Matplotlib`, `wordcloud`

## 🚀 로컬 실행 방법 (How to run locally)

1. Python 3.9+ 버전이 설치되어 있어야 합니다.
2. 터미널(또는 명령 프롬프트)을 열고 프로젝트 폴더로 이동합니다.
3. 호환성 및 렌더링에 필요한 파이썬 라이브러리를 설치합니다.
```bash
pip install pandas xlrd streamlit plotly wordcloud matplotlib
```
4. Streamlit 서버를 구동합니다.
```bash
streamlit run app.py
```
5. 자동으로 열리는 브라우저(통상 `http://localhost:8501`)에서 대시보드를 확인합니다.

---
*본 프로젝트는 졸업 논문 준비 과정에서의 문헌 추적 및 시각적 직관을 돕기 위해 작성되었습니다.*
