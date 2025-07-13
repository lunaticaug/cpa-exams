"""
PDF Text Layer 검사 도구
각 PDF 파일의 텍스트 레이어 존재 여부와 품질을 확인합니다.
"""

import pdfplumber
from pathlib import Path
import json

def check_pdf_text_layer(pdf_path):
    """PDF의 text layer 상태 확인"""
    result = {
        'file': pdf_path.name,
        'has_text': False,
        'text_quality': 'none',
        'sample_text': '',
        'page_count': 0,
        'text_coverage': []
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result['page_count'] = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages[:3]):  # 처음 3페이지만 확인
                text = page.extract_text() or ""
                text_len = len(text.strip())
                
                result['text_coverage'].append({
                    'page': i + 1,
                    'char_count': text_len,
                    'has_text': text_len > 50
                })
                
                if i == 0 and text_len > 50:
                    result['has_text'] = True
                    result['sample_text'] = text[:200].strip()
                    
                    # 텍스트 품질 평가
                    if text_len > 1000:
                        result['text_quality'] = 'high'
                    elif text_len > 500:
                        result['text_quality'] = 'medium'
                    else:
                        result['text_quality'] = 'low'
    
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    source_dir = Path("_source")
    pdf_files = list(source_dir.glob("*.pdf"))
    
    print(f"PDF Text Layer 검사 시작 - 총 {len(pdf_files)}개 파일\n")
    
    results = []
    text_layer_stats = {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
    
    for pdf_path in sorted(pdf_files):
        if '2022' in pdf_path.name or '2023' in pdf_path.name or '2024' in pdf_path.name or '2025' in pdf_path.name:
            print(f"검사 중: {pdf_path.name}")
            result = check_pdf_text_layer(pdf_path)
            results.append(result)
            text_layer_stats[result['text_quality']] += 1
            
            if result['has_text']:
                print(f"  ✓ Text layer 존재 (품질: {result['text_quality']})")
                print(f"  샘플: {result['sample_text'][:80]}...")
            else:
                print(f"  ✗ Text layer 없음")
            print()
    
    # 요약 출력
    print("\n=== 요약 ===")
    print(f"고품질 text layer: {text_layer_stats['high']}개")
    print(f"중간품질 text layer: {text_layer_stats['medium']}개")
    print(f"저품질 text layer: {text_layer_stats['low']}개")
    print(f"Text layer 없음: {text_layer_stats['none']}개")
    
    # 결과 저장
    with open('pdf_text_layer_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

if __name__ == "__main__":
    main()