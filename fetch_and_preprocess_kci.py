import os
import time
import requests
import re
import pandas as pd
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

def load_kci_api_key():
    load_dotenv()
    api_key = os.getenv("KCI_API_KEY")
    if not api_key:
        raise ValueError(".env 파일에서 KCI_API_KEY를 찾을 수 없습니다.")
    return api_key

def search_articles(api_key, keyword, max_pages=None):
    """
    Search for articles and return a list of article-ids.
    """
    url = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"
    display_count = 100
    page = 1
    article_ids = []
    
    print(f"[*] '{keyword}' KCI 논문 검색을 시작합니다...")
    
    while True:
        params = {
            "apiCode": "articleSearch",
            "key": api_key,
            "title": keyword,
            "displayCount": display_count,
            "page": page
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        
        # Check total count
        total_elem = root.find(".//result/total")
        if total_elem is None:
            break
            
        total = int(total_elem.text)
        if page == 1:
            print(f"[*] 총 {total}건의 논문이 검색되었습니다.")
            
        records = root.findall(".//record")
        if not records:
            break
            
        for record in records:
            article_info = record.find("articleInfo")
            if article_info is not None:
                article_id = article_info.get("article-id")
                if article_id:
                    article_ids.append(article_id)
        
        if (page * display_count) >= total:
            break
            
        if max_pages and page >= max_pages:
            break
            
        page += 1
        time.sleep(0.5) # Rate limit protection
        
    return article_ids

def get_article_detail(api_key, article_id):
    """
    Fetch details for a specific article.
    """
    url = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"
    params = {
        "apiCode": "articleDetail",
        "key": api_key,
        "id": article_id
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # 파싱 데이터 딕셔너리
            data = {
                "article_id": article_id,
                "논문명": "",
                "영문제목": "",
                "저자명": "",
                "주저자 소속기관": "",
                "학술지명": "",
                "초록": "",
                "초록(영문)": "",
                "저자키워드": "",
                "발행년도": "",
                "인용수": 0,
                "URL": ""
            }
            
            # 논문 정보 파싱
            article_info = root.find(".//articleInfo")
            if article_info is not None:
                # 제목
                title_orig = article_info.find(".//title-group/article-title[@lang='original']")
                if title_orig is not None and title_orig.text:
                    data["논문명"] = title_orig.text.strip()
                    
                title_eng = article_info.find(".//title-group/article-title[@lang='english']")
                if title_eng is not None and title_eng.text:
                    data["영문제목"] = title_eng.text.strip()
                elif article_info.find(".//title-group/article-title[@lang='foreign']") is not None and article_info.find(".//title-group/article-title[@lang='foreign']").text:
                    data["영문제목"] = article_info.find(".//title-group/article-title[@lang='foreign']").text.strip()
                
                # 저자
                authors = article_info.findall(".//author-group/author")
                author_names = []
                main_institution = "미상"
                for i, author in enumerate(authors):
                    name_elem = author.find("name")
                    if name_elem is not None and name_elem.text:
                        author_names.append(name_elem.text.strip())
                        
                    # 첫 번째 저자의 소속을 주저자 소속으로
                    if i == 0:
                        inst_elem = author.find("institution")
                        if inst_elem is not None and inst_elem.text:
                            main_institution = inst_elem.text.strip()
                            
                data["저자명"] = "; ".join(author_names)
                data["주저자 소속기관"] = main_institution
                
                # 초록
                abstract_orig = article_info.find(".//abstract-group/abstract[@lang='original']")
                if abstract_orig is not None and abstract_orig.text:
                    data["초록"] = abstract_orig.text.strip()
                    
                abstract_eng = article_info.find(".//abstract-group/abstract[@lang='english']")
                if abstract_eng is not None and abstract_eng.text:
                    data["초록(영문)"] = abstract_eng.text.strip()
                    
                # 키워드
                keywords = article_info.findall(".//keyword-group/keyword")
                kw_list = []
                for kw in keywords:
                    if kw.text:
                        kw_list.append(kw.text.strip())
                data["저자키워드"] = "; ".join(kw_list)
                
                # 인용수
                cite_elem = article_info.find("citation-count")
                if cite_elem is not None and cite_elem.text:
                    data["인용수"] = int(cite_elem.text.strip())
                    
                # URL
                url_elem = article_info.find("url")
                if url_elem is not None and url_elem.text:
                    data["URL"] = url_elem.text.strip()
            
            # 저널 정보 (발행년도, 학술지명)
            journal_info = root.find(".//journalInfo")
            if journal_info is not None:
                year_elem = journal_info.find("pub-year")
                if year_elem is not None and year_elem.text:
                    data["발행년도"] = year_elem.text.strip()
                journal_elem = journal_info.find("journal-name")
                if journal_elem is not None and journal_elem.text:
                    data["학술지명"] = journal_elem.text.strip()
                    
            return data
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[-] {article_id} 상세 정보 추출 실패: {e}")
                return None
            time.sleep(2)
            
    return None

def fetch_all_kci_data(api_key, keyword):
    article_ids = search_articles(api_key, keyword)
    
    total = len(article_ids)
    print(f"[*] {total}건의 상세 데이터를 추출합니다. (약 {total * 0.3:.1f}초 소요 예상)")
    
    results = []
    for i, article_id in enumerate(article_ids):
        if (i + 1) % 50 == 0:
            print(f"    ... {i + 1}/{total} 처리 중")
            
        detail = get_article_detail(api_key, article_id)
        if detail:
            results.append(detail)
            
        time.sleep(0.3) # Rate limit protection
        
    df = pd.DataFrame(results)
    return df

def preprocess_kci_data(df):
    """
    기존 raw.py의 전처리 로직을 적용 + 개념 클러스터링을 위한 영문 키워드 보존 등 개선된 로직
    """
    print("[*] 데이터 전처리를 시작합니다...")
    
    # 중복 제거
    if '논문명' in df.columns and '저자명' in df.columns:
        df['_temp_key'] = df['논문명'].astype(str).str.replace(r'\s+', '', regex=True).str.lower() + \
                          df['저자명'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
        before_count = len(df)
        df = df.drop_duplicates(subset=['_temp_key'], keep='first')
        df = df.drop(columns=['_temp_key'])
        after_count = len(df)
        print(f"    - 중복 제거: {before_count}건 -> {after_count}건")

    # 저자명 분리 및 포맷팅 (1:N Explode 대신 문자열 포맷팅으로 변경)
    if '저자명' in df.columns:
        def format_authors(author_str):
            if pd.isna(author_str):
                return '미상'
            author_str = str(author_str).strip()
            # 세미콜론(;) 또는 쉼표(,) 기준 분리
            if ';' in author_str:
                authors = [a.strip() for a in author_str.split(';')]
            elif ',' in author_str:
                authors = [a.strip() for a in author_str.split(',')]
            else:
                authors = [author_str]
                
            authors = [a for a in authors if a]
            
            if len(authors) == 0:
                return '미상'
            elif len(authors) == 1:
                return authors[0]
            elif len(authors) <= 3:
                return ', '.join(authors)
            else:
                return f"{', '.join(authors[:3])} 외 {len(authors) - 3}인"
                
        df['저자명'] = df['저자명'].apply(format_authors)

    # 키워드 매핑 및 노이즈 제거 (영문 보존)
    if '저자키워드' in df.columns:
        keyword_mapping = {
            r'(?i)Chair': '살',
            r'(?i)Flesh': '살',
            r'육\(肉\)': '살',
            r'원소\(Element\)': '살',
            r'(?i)Chiasme': '교차/살',
            r'얽힘': '교차/살',
            r'(?i)Entrelacs': '교차/살',
            r'가역성': '교차/살'
        }
        
        def apply_mapping(text):
            if pd.isna(text):
                return text
            text = str(text)
            
            for pattern, replacement in keyword_mapping.items():
                text = re.sub(pattern, replacement, text)
            
            raw_keywords = re.split(r'[,;]', text)
            cleaned_keywords = []
            for kw in raw_keywords:
                kw = kw.strip()
                if not kw:
                    continue
                
                # 기존에는 괄호 안의 내용을 모두 지웠으나, 이번에는 영문이 순수하게 있을 때는 남기는 방향으로 가거나
                # 이미 API가 키워드를 분리해서 줬기 때문에 한자 등 노이즈만 가볍게 정제
                # 예: "신체(body)" -> API에서는 "신체", "body" 로 각각 나오기도 함.
                kw = re.sub(r'\([一-龥]+\)', '', kw).strip() # 한자 괄호 제거
                # kw = re.sub(r'\(.*?\)', '', kw).strip() # 과도한 괄호 삭제 방지
                
                if kw:
                    cleaned_keywords.append(kw.lower()) # 영문은 소문자 통일
            
            unique_keywords = []
            for kw in cleaned_keywords:
                if kw not in unique_keywords:
                    unique_keywords.append(kw)
            
            return ', '.join(unique_keywords)

        df['저자키워드'] = df['저자키워드'].apply(apply_mapping)

    # 기관명 상위 매핑
    if '주저자 소속기관' in df.columns:
        def clean_institution(inst):
            if pd.isna(inst):
                return '미상'
            inst = str(inst).strip()
            inst = re.split(r'[,\s]+', inst)[0]
            if inst.endswith('대') and not inst.endswith('대학교'):
                inst = inst + '학교'
            return inst
        df['주저자 소속기관'] = df['주저자 소속기관'].apply(clean_institution)
        
    # 논문명 정제
    if '논문명' in df.columns:
        def clean_title(title):
            if pd.isna(title):
                return '미상'
            title = str(title)
            title = re.sub(r'[\ue000-\uf8ff]', '', title)
            title = re.sub(r'&#\w+;', '', title)
            title = re.sub(r'[-_~]{2,}', ' ', title)
            title = re.sub(r'\s+', ' ', title).strip()
            return title
        df['논문명'] = df['논문명'].apply(clean_title)

    return df

def main():
    try:
        api_key = load_kci_api_key()
    except ValueError as e:
        print(e)
        return
        
    # 데이터 수집
    raw_df = fetch_all_kci_data(api_key, "메를로-퐁티")
    
    if raw_df.empty:
        print("[-] 수집된 데이터가 없습니다.")
        return
        
    # 전처리
    processed_df = preprocess_kci_data(raw_df)
    
    # 저장
    output_file = 'c:/dashboard/퐁티_전처리완료.csv'
    processed_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"[*] 결과 파일이 성공적으로 저장되었습니다: {output_file}")
    print(f"[*] 총 {len(processed_df)}행 생성 완료.")

if __name__ == "__main__":
    main()
