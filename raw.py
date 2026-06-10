import pandas as pd
import re

def preprocess_kci_data(file_paths):
    """
    KCI 엑셀 데이터를 로드하여 전처리를 수행합니다.
    1. 저자명 다중 분리 (1:N Explode)
    2. 키워드 매핑 (동의어 및 외국어/한자 병기 통일)
    """
    dfs = []
    for f in file_paths:
        try:
            # xlrd 엔진으로 KCI의 구형 xls 파일을 읽어옵니다.
            df = pd.read_excel(f, engine='xlrd')
            dfs.append(df)
        except Exception as e:
            print(f"파일 로드 오류 ({f}): {e}")
            
    if not dfs:
        return None
        
    df = pd.concat(dfs, ignore_index=True)
    
    # 컬럼명에 포함된 공백 및 줄바꿈 기호 제거
    df.columns = df.columns.str.strip().str.replace('\n', '')
    
    # ==========================================
    # 0. 다중 파일 통합 및 강력한 중복 제거 (분석 기반 확보)
    # ==========================================
    if '논문명' in df.columns and '저자명' in df.columns:
        # 중복 검사를 위한 임시 식별키 생성 (공백 제거, 소문자화하여 미세한 오타로 인한 중복 누락 방지)
        df['_temp_key'] = df['논문명'].astype(str).str.replace(r'\s+', '', regex=True).str.lower() + \
                          df['저자명'].astype(str).str.replace(r'\s+', '', regex=True).str.lower()
        
        # 병합 전 데이터 건수 기록
        before_count = len(df)
        
        # 중복 제거 (첫 번째 데이터 유지)
        df = df.drop_duplicates(subset=['_temp_key'], keep='first')
        
        # 임시 식별키 삭제
        df = df.drop(columns=['_temp_key'])
        
        after_count = len(df)
        print(f"[*] 다중 파일 통합 및 중복 제거 완료: {before_count}건 -> {after_count}건 (중복 {before_count - after_count}건 제거)")
        
    # ==========================================
    # 1. 저자명 다중 분리 (1:N Explode)
    # ==========================================
    if '저자명' in df.columns:
        df['저자명'] = df['저자명'].fillna('미상')
        
        # KCI 논문의 다중 저자는 주로 세미콜론(;)이나 쉼표(,)로 구분됩니다.
        # 정규식을 사용해 쉼표를 세미콜론으로 통일
        df['저자명'] = df['저자명'].astype(str).str.replace(r'[,;]+', ';', regex=True)
        
        # 세미콜론을 기준으로 리스트로 분할
        df['저자명'] = df['저자명'].str.split(';')
        
        # explode()를 사용하여 리스트 안의 저자 수만큼 행(Row)을 복제 및 분할
        df = df.explode('저자명')
        
        # 이름 앞뒤 공백 제거 및 빈 문자열 행 제거
        df['저자명'] = df['저자명'].str.strip()
        df = df[df['저자명'] != '']

    # ==========================================
    # 2. 키워드 매핑 및 노이즈 제거
    # ==========================================
    if '저자키워드' in df.columns:
        # 매핑 규칙 정의 (정규식 패턴 사용)
        # (?i)는 대소문자 구분 없이 매칭 (Chair, chair, CHAIR 모두 매칭)
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
            
            # 1. 핵심 철학 개념어 우선 매핑 (사용자 지정 규칙)
            for pattern, replacement in keyword_mapping.items():
                text = re.sub(pattern, replacement, text)
            
            # 2. 키워드 분리 (쉼표 및 세미콜론 기준)
            # 일부 데이터에서 세미콜론을 쓰는 경우도 있으므로 정규식으로 분리
            raw_keywords = re.split(r'[,;]', text)
            
            cleaned_keywords = []
            for kw in raw_keywords:
                kw = kw.strip()
                if not kw:
                    continue
                
                # 3. 노이즈 전면 제거: 괄호 및 괄호 안의 영문/한자 모두 제거 (예: "신체(body)" -> "신체")
                # 이는 KCI 키워드의 가장 큰 파편화 원인입니다.
                kw = re.sub(r'\(.*?\)', '', kw).strip()
                
                if kw:
                    cleaned_keywords.append(kw)
            
            # 4. 키워드 중복 제거 (예: '살(Chair), 살' -> 치환 후 '살, 살'이 된 것을 하나로 병합)
            # 순서를 유지하며 중복 제거
            unique_keywords = []
            for kw in cleaned_keywords:
                if kw not in unique_keywords:
                    unique_keywords.append(kw)
            
            # 5. 깔끔하게 쉼표로 다시 결합하여 저장
            return ', '.join(unique_keywords)

        df['저자키워드'] = df['저자키워드'].apply(apply_mapping)
        
    # ==========================================
    # 3. 기관명 상위 매핑 (Parent Mapping)
    # ==========================================
    if '주저자 소속기관' in df.columns:
        def clean_institution(inst):
            if pd.isna(inst):
                return '미상'
            inst = str(inst).strip()
            
            # 1. 쉼표(,)나 띄어쓰기 기준으로 가장 앞의 텍스트(상위 기관)만 추출
            # 예: "건국대학교, 철학과" -> "건국대학교"
            # 예: "연세대학교 대학원" -> "연세대학교"
            inst = re.split(r'[,\s]+', inst)[0]
            
            # 2. '대'로 끝나는 약칭을 '대학교'로 통일 (예: 건국대 -> 건국대학교)
            # 이미 '대학교'로 끝나는 경우 제외
            if inst.endswith('대') and not inst.endswith('대학교'):
                inst = inst + '학교'
                
            return inst

        df['주저자 소속기관'] = df['주저자 소속기관'].apply(clean_institution)
        
    # ==========================================
    # 4. 논문명 표시 품질 향상 (PUA 및 부제 기호 정제)
    # ==========================================
    if '논문명' in df.columns:
        def clean_title(title):
            if pd.isna(title):
                return '미상'
            title = str(title)
            
            # 1. PUA(Private Use Area) 유니코드 특수문자 및 깨진 한자 제거 (U+E000 ~ U+F8FF)
            title = re.sub(r'[\ue000-\uf8ff]', '', title)
            
            # 2. HTML 엔티티 기호(&#...; 등) 제거 (웹에서 깨지는 코드)
            title = re.sub(r'&#\w+;', '', title)
            
            # 3. 불필요한 부제 장식 기호 제거 (예: __, ---, ~~~ 등 연속된 특수기호)
            # 연속된 2개 이상의 하이픈, 언더스코어, 물결표를 공백으로 치환
            title = re.sub(r'[-_~]{2,}', ' ', title)
            
            # 4. 불필요하게 띄어쓰기가 많은 경우 다중 공백을 하나로 통일하고 양끝 공백 제거
            title = re.sub(r'\s+', ' ', title).strip()
            
            return title

        df['논문명'] = df['논문명'].apply(clean_title)

    return df

if __name__ == "__main__":
    # 처리할 원본 데이터 파일 목록
    target_files = [
        'c:/dashboard/퐁티_1_300.xls', 
        'c:/dashboard/퐁티_301_600.xls'
    ]
    
    print("데이터 전처리를 시작합니다...")
    processed_df = preprocess_kci_data(target_files)
    
    if processed_df is not None:
        print(f"전처리 완료! 총 {len(processed_df)}개의 행(저자 분리 포함)이 생성되었습니다.")
        
        # 처리된 데이터를 CSV 파일로 저장 (한글 깨짐 방지를 위해 utf-8-sig 인코딩 사용)
        output_file = 'c:/dashboard/퐁티_엑셀_통합_전처리.csv'
        processed_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"결과 파일이 저장되었습니다: {output_file}")
