import pandas as pd
import json
import numpy as np

def convert_csv_to_js():
    csv_file = '퐁티_엑셀_통합_전처리.csv'
    js_file = 'data.js'
    
    # Read the CSV
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return
    
    # Fill NA values
    df = df.fillna('')
    
    # Convert types
    # Rename columns to match what index.html expects
    if '발행년도' in df.columns:
        df.rename(columns={'발행년도': '발행연도'}, inplace=True)
    if '인용수' in df.columns:
        df.rename(columns={'인용수': '인용된 총 횟수'}, inplace=True)
        
    df['발행연도'] = pd.to_numeric(df['발행연도'], errors='coerce').fillna(0).astype(int)
    df['인용된 총 횟수'] = pd.to_numeric(df['인용된 총 횟수'], errors='coerce').fillna(0).astype(int)
    
    records = df.to_dict(orient='records')
    
    import re
    # Post-process for javascript compatibility
    for row in records:
        # 1. 초록 요약 생성
        abstract = str(row.get('초록', '')).strip()
        if abstract and abstract.lower() != 'nan':
            sentences = [s.strip() for s in abstract.split('.') if s.strip()]
            row['초록_요약'] = '. '.join(sentences[:3]) + ('.' if len(sentences) > 0 else '')
        else:
            row['초록_요약'] = ''
            
        # 2. 키워드 정제
        kw = row.get('저자키워드', '')
        if not kw or str(kw).lower() == 'nan':
            row['저자키워드_추출'] = []
        else:
            cleaned_kws = []
            for k in str(kw).split(','):
                k = k.strip()
                if not k:
                    continue
                # 메를로-퐁티 동의어 통합 (모리스 메를로-퐁티, 메를로--퐁티 등 모두 포함)
                k_lower = k.lower()
                if 'merleau' in k_lower or 'ponty' in k_lower or '메를로' in k_lower or '퐁티' in k_lower or '메를르' in k_lower:
                    k = '메를로-퐁티'
                
                cleaned_kws.append(k)
            # 중복 제거 후 리스트로 저장
            row['저자키워드_추출'] = list(set(cleaned_kws))
            
        # 3. 저자명 처리 (제1저자, 공동저자 최대 3명, 그 이상은 '외 N명')
        author_str = str(row.get('저자명', '')).strip()
        if not author_str or author_str.lower() == 'nan':
            row['저자'] = '저자 미상'
        else:
            # KCI 데이터에서 공동저자는 주로 세미콜론(;) 또는 쉼표(,)로 구분됨
            if ';' in author_str:
                authors = [a.strip() for a in author_str.split(';')]
            elif ',' in author_str:
                authors = [a.strip() for a in author_str.split(',')]
            else:
                authors = [author_str]
            
            authors = [a for a in authors if a]
            
            if len(authors) == 0:
                row['저자'] = '저자 미상'
            elif len(authors) == 1:
                row['저자'] = authors[0]
            elif len(authors) <= 3:
                row['저자'] = ', '.join(authors)
            else:
                row['저자'] = f"{', '.join(authors[:3])} 외 {len(authors) - 3}인"
            
    # Write to data.js
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write('const rawData = ' + json.dumps(records, ensure_ascii=False) + ';\n')
        
    print(f"Successfully generated {js_file} with {len(records)} records.")

if __name__ == '__main__':
    convert_csv_to_js()
