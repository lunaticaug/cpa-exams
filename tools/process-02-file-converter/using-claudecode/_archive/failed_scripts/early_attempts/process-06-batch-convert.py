"""
기능: PDF 파일들을 일괄로 Markdown으로 변환
입력: source 폴더의 PDF 파일들
출력: output/markdown 폴더에 변환된 MD 파일들
"""

from pathlib import Path
import json
import pdfplumber
import re
from datetime import datetime
import traceback

class BatchPDFConverter:
    def __init__(self):
        self.source_dir = Path("source")
        self.output_dir = Path("output/markdown")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log = []
        
    def convert_table_to_markdown(self, table):
        """표를 Markdown 테이블로 변환"""
        if not table or not table[0]:
            return ""
        
        markdown_table = []
        
        # 헤더 행
        header = [str(cell) if cell else "" for cell in table[0]]
        markdown_table.append("| " + " | ".join(header) + " |")
        
        # 구분선
        separator = "|"
        for _ in header:
            separator += " --- |"
        markdown_table.append(separator)
        
        # 데이터 행
        for row in table[1:]:
            cleaned_row = [str(cell) if cell else "" for cell in row]
            markdown_table.append("| " + " | ".join(cleaned_row) + " |")
        
        return "\n".join(markdown_table)
    
    def process_text(self, text):
        """텍스트 처리 및 포맷팅"""
        if not text:
            return ""
        
        # 문제 번호 패턴
        text = re.sub(r'【문제\s*(\d+)】\s*\((\d+)점\)', r'\n## 문제 \1 (\2점)\n', text)
        
        # 하위 문제 패턴
        text = re.sub(r'\(물음\s*(\d+)\)', r'\n### (물음 \1)', text)
        
        # <자료> 패턴
        text = re.sub(r'<자료\s*(\d+)>', r'\n#### <자료 \1>', text)
        
        # 답안양식 패턴
        text = re.sub(r'\(답안양식\)', r'\n**답안양식:**', text)
        
        return text
    
    def convert_single_pdf(self, pdf_path):
        """단일 PDF 파일 변환"""
        try:
            print(f"\n변환 중: {pdf_path.name}")
            
            # 출력 파일명 생성
            output_path = self.output_dir / f"{pdf_path.stem}.md"
            
            # 연도 추출
            year = pdf_path.name.split('_')[0]
            
            content = []
            content.append(f"# {year}년 2차 원가회계 기출문제\n")
            content.append(f"> 파일: {pdf_path.name}")
            content.append(f"> 변환일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # PDF 처리
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    content.append(f"\n---\n\n## 페이지 {page_num}\n")
                    
                    # 텍스트 추출
                    text = page.extract_text()
                    if text:
                        # 텍스트 처리
                        processed_text = self.process_text(text)
                        
                        # 표 추출 및 삽입
                        tables = page.extract_tables()
                        if tables:
                            # 표를 텍스트 내 적절한 위치에 삽입하는 로직
                            # 간단히 텍스트 뒤에 표들을 추가
                            lines = processed_text.split('\n')
                            final_content = []
                            
                            for line in lines:
                                final_content.append(line)
                                
                                # "답안양식" 다음에 표가 올 가능성이 높음
                                if "답안양식" in line and tables:
                                    final_content.append("\n")
                                    final_content.append(self.convert_table_to_markdown(tables.pop(0)))
                                    final_content.append("\n")
                            
                            # 남은 표들 추가
                            for table in tables:
                                final_content.append("\n")
                                final_content.append(self.convert_table_to_markdown(table))
                                final_content.append("\n")
                            
                            content.extend(final_content)
                        else:
                            content.append(processed_text)
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.log.append({
                "file": pdf_path.name,
                "status": "success",
                "output": str(output_path)
            })
            
            print(f"  ✓ 완료: {output_path.name}")
            return True
            
        except Exception as e:
            self.log.append({
                "file": pdf_path.name,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"  ✗ 오류: {e}")
            return False
    
    def run_batch_conversion(self):
        """일괄 변환 실행"""
        print("=== PDF → Markdown 일괄 변환 시작 ===")
        
        # PDF 파일 목록
        pdf_files = sorted(self.source_dir.glob("*.pdf"), 
                          key=lambda x: x.name.split('_')[0], 
                          reverse=True)
        
        print(f"\n총 {len(pdf_files)}개 PDF 파일 발견")
        
        # 변환 실행
        success_count = 0
        for pdf_file in pdf_files:
            if self.convert_single_pdf(pdf_file):
                success_count += 1
        
        # 결과 요약
        print(f"\n=== 변환 완료 ===")
        print(f"성공: {success_count}/{len(pdf_files)}")
        print(f"실패: {len(pdf_files) - success_count}/{len(pdf_files)}")
        
        # 로그 저장
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(pdf_files),
            "success": success_count,
            "failed": len(pdf_files) - success_count,
            "details": self.log
        }
        
        with open("output-06-conversion-log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n상세 로그: output-06-conversion-log.json")
        print(f"변환된 파일들: {self.output_dir}/")

def main():
    converter = BatchPDFConverter()
    converter.run_batch_conversion()

if __name__ == "__main__":
    main()