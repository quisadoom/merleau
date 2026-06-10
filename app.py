import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import re
from collections import Counter
import os

# 1. 전역 설정 (Global Settings)
st.set_page_config(page_title="Merleau-Ponty Dashboard", layout="wide", page_icon="🚗")

# 마트플롯립(matplotlib) 한글 폰트 설정 (워드클라우드 등에서 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Plotly 기본 폰트 설정
PLOTLY_FONT = dict(family="Malgun Gothic, Arial")

# 2. 데이터 처리 모듈
@st.cache_data(show_spinner=False)
def validate_and_load_data():
    file = 'c:/dashboard/퐁티_전처리완료.csv'
    
    try:
        # 새로 생성된 API 기반 전처리 완료 CSV 로드
        df = pd.read_csv(file, encoding='utf-8-sig')
        
        # 컬럼명 공백 및 줄바꿈 정제 (Clean Column Names)
        df.columns = df.columns.str.strip().str.replace('\n', '')
        
        # 논문명, 저자명을 기준으로 동일 문헌 중복 제거
        if '논문명' in df.columns and '저자명' in df.columns:
            df = df.drop_duplicates(subset=['논문명', '저자명'], keep='first')
        
        return df
    except Exception as e:
        st.error(f"데이터 파일 확인 필드 오류: {e}")
        st.stop()

@st.cache_data(show_spinner=False)
def preprocess_data(df):
    """
    데이터 정제 핵심 엔진: 결측치 보정, 형 변환, 조건부 형태소 분석
    """
    df = df.copy()

    # (1) 발행년도 처리
    if '발행년도' in df.columns:
        df['발행년도'] = pd.to_numeric(df['발행년도'], errors='coerce')
        df = df.dropna(subset=['발행년도']) # 연도가 없는 논문은 추이에서 제외
        df['발행년도'] = df['발행년도'].astype(int)
    else:
        df['발행년도'] = 2000

    # (2) 인용된 총 횟수 처리
    if '인용수' in df.columns:
        df['인용수'] = pd.to_numeric(df['인용수'], errors='coerce').fillna(0).astype(int)
    else:
        df['인용수'] = 0

    # (3) 저자, 학술지명 결측치 보완
    for col in ['저자명', '학술지명']:
        if col in df.columns:
            df[col] = df[col].fillna("미상")
            
    # (4) 저자키워드 불용어 처리 (Stopwords Filtering)
    stopwords = [
        "연구", "분석", "고찰", "현상학", "메를로", "퐁티", "철학", "메를로퐁티",
        "의미", "현대", "문제", "대한", "통한", "중심", "이해", "방법론", "사유"
    ]
    
    def extract_keywords(text):
        if pd.isna(text):
            return []
        words = []
        # 한국어/영어 1글자 초과 명사만 추출
        for match in re.finditer(r'[가-힣a-zA-Z]{2,}', str(text)):
            word = match.group()
            if word not in stopwords:
                words.append(word)
        return words
        
    if '저자키워드' in df.columns:
        df['저자키워드_추출'] = df['저자키워드'].apply(extract_keywords)
    else:
        df['저자키워드_추출'] = [[] for _ in range(len(df))]
        
    return df

# 3. 사이트 컴포넌트(Tab 단위) 렌더링 모듈
def render_tab1(df):
    st.subheader("📊 Total Insight (주행 기록계)")
    st.markdown("연구 담론의 **확산 시기(논문 발행 수)** 및 **학계 내 영향력(총 인용 수)** 트렌드입니다.")
    
    yearly = df.groupby('발행년도').agg(논문수=('논문명', 'count'), 인용수=('인용수', 'sum')).reset_index()
    yearly = yearly.sort_values('발행년도')
    
    # 이중축 그래프 (Plotly Subplots)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=yearly['발행년도'], y=yearly['논문수'], name="발행된 논문 수", marker_color='rgba(55, 83, 109, 0.8)'),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=yearly['발행년도'], y=yearly['인용수'], name="총 피인용 수", mode='lines+markers', line=dict(color='#FF4B4B', width=3)),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="시간 흐름에 따른 논문 발행 및 피인용수 추이", 
        font=PLOTLY_FONT, 
        hovermode="x unified",
        xaxis_title="발행 연도"
    )
    fig.update_yaxes(title_text="신규 발행 건수 (Bar)", secondary_y=False)
    fig.update_yaxes(title_text="인용된 총 횟수 (Line)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)


def render_tab2(df):
    st.subheader("🧭 Concept Map (핵심 경로)")
    
    # 모든 추출된 단어 리스트업
    all_words = []
    for wl in df['저자키워드_추출']:
        all_words.extend(wl)
    
    if not all_words:
        st.warning("분석 가능한 한글 키워드가 충분하지 않습니다.")
        return
        
    word_counts = Counter(all_words)
    top15 = pd.DataFrame(word_counts.most_common(15), columns=['키워드', '빈도수'])
    
    col_bar, col_wc = st.columns(2)
    
    with col_bar:
        st.markdown("##### 📌 상위 15개 한국어 핵심어 빈도")
        top15_rev = top15.sort_values("빈도수", ascending=True)
        fig = px.bar(top15_rev, x='빈도수', y='키워드', orientation='h', text='빈도수', color='빈도수', color_continuous_scale="Blues")
        fig.update_traces(textposition='outside')
        fig.update_layout(font=PLOTLY_FONT, height=500, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_wc:
        st.markdown("##### ☁️ 핵심 개념어 워드클라우드")
        font_path = "C:/Windows/Fonts/malgun.ttf" if os.path.exists("C:/Windows/Fonts/malgun.ttf") else None
        
        try:
            # 워드클라우드 렌더링
            wc = WordCloud(font_path=font_path, width=600, height=500, background_color="white", colormap="viridis").generate_from_frequencies(word_counts)
            fig_wc, ax = plt.subplots(figsize=(6, 5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis('off')
            st.pyplot(fig_wc)
        except Exception as e:
            st.error("워드클라우드를 생성하는 데 문제가 발생했습니다. 시스템에 한글 폰트가 설치되어 있는지 확인해주세요.")


def render_tab3(df):
    st.subheader("👥 People & Journal (주변 시야)")
    
    col_authors, col_journals = st.columns(2)
    
    with col_authors:
        st.markdown("##### 🖋️ 최다 게재 연구자 순위 (Top 10)")
        authors = df['저자명'].value_counts().head(10).reset_index()
        authors.columns = ['연구자명', '논문 편수']
        fig_auth = px.bar(authors.sort_values('논문 편수', ascending=True), 
                          x='논문 편수', y='연구자명', orientation='h', text='논문 편수',
                          color_discrete_sequence=['#4BB543'])
        fig_auth.update_traces(textposition='outside')
        fig_auth.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig_auth, use_container_width=True)
        
    with col_journals:
        st.markdown("##### 📓 주요 학술지 분포 (Top 10)")
        journals = df['학술지명'].value_counts().head(10).reset_index()
        journals.columns = ['학술지명', '비중']
        fig_jour = px.pie(journals, names='학술지명', values='비중', hole=0.45)
        fig_jour.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig_jour, use_container_width=True)


def render_tab4(df):
    st.subheader("📚 Research Library (집중 분석)")
    # 테이블에 출력할 핵심 항목 필터링
    display_cols = [c for c in ['발행년도', '논문명', '저자명', '학술지명', '인용수', '저자키워드'] if c in df.columns]
    
    st.write("아래 리스트는 **발행년도 최신순 > 인용수 랭킹순**으로 정렬되어 있습니다. (테이블 헤더를 클릭하면 정렬 방향을 바꿀 수 있습니다)")
    view_df = df[display_cols].sort_values(by=['발행년도', '인용수'], ascending=[False, False])
    st.dataframe(view_df, use_container_width=True, height=400)
    
    st.markdown("---")
    st.markdown("##### 🔎 문헌별 요약 정보 (초록 검색창)")
    if '초록' in df.columns:
        search_kw = st.text_input('🔎 "논문명"이나 "저자명"을 검색하면 관련 논문의 상세 요약을 확인할 수 있습니다.', '')
        
        if search_kw:
            matched = df[df['논문명'].str.contains(search_kw, na=False, case=False) | df['저자명'].str.contains(search_kw, na=False, case=False)]
            if matched.empty:
                st.info("조건에 맞는 결과가 없습니다.")
            else:
                st.write(f"총 **{len(matched)}**건의 논문이 검색되었습니다.")
                for idx, row in matched.iterrows():
                    with st.expander(f"📖 {row['논문명']} - {row['저자명']} (인용 수: {row['인용수']})"):
                        abstract_text = row['초록'] if pd.notna(row['초록']) else "초록 정보가 기재되지 않은 문헌입니다."
                        st.markdown(f"**학술지:** {row.get('학술지명', '미상')} ({row['발행년도']})")
                        st.write(abstract_text)
    else:
        st.info("현재 로드된 데이터셋에는 '초록' 텍스트 컬럼이 존재하지 않습니다.")

# 4. 앱 통합 메인 (Entry Point)
def main():
    st.title("🚗 모리스 메를로-퐁티 연구 대시보드")
    st.caption("한국연구재단(KCI) 데이터를 바탕으로 한 졸업 논문 예비탐색 네비게이션입니다.")
    st.markdown("---")
    
    with st.spinner('문헌 데이버베이스를 불러오고 전처리하는 중입니다...'):
        raw_df = validate_and_load_data()
        df = preprocess_data(raw_df)
    
    # 4개의 탭 레이아웃 생성
    t1, t2, t3, t4 = st.tabs(["📊 Total Insight", "🧭 Concept Map", "👥 People & Journal", "📚 Research Library"])
    
    with t1:
        render_tab1(df)
    with t2:
        render_tab2(df)
    with t3:
        render_tab3(df)
    with t4:
        render_tab4(df)

if __name__ == "__main__":
    main()
