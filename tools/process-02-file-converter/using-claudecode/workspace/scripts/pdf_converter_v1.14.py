"""
기능: 레이아웃 인식 PDF 변환기 (2단 구성 처리)
입력: PDF 파일
출력: 올바른 순서로 정렬된 Markdown
"""

import pdfplumber
from pathlib import Path
import re
from dataclasses import dataclass
from typing import List, Tuple, Dict
import statistics

@dataclass
class TextBlock:
    """텍스트 블록 클래스"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page: int
    column: int = 0  # 0: 미정, 1: 왼쪽, 2: 오른쪽
    
    @property
    def x0(self): return self.bbox[0]
    
    @property
    def y0(self): return self.bbox[1]
    
    @property
    def x1(self): return self.bbox[2]
    
    @property
    def y1(self): return self.bbox[3]
    
    @property
    def center_x(self): return (self.x0 + self.x1) / 2
    
    @property
    def center_y(self): return (self.y0 + self.y1) / 2

class LayoutAwareConverter:
    def __init__(self):
        self.pages_content = []
        self.column_threshold = None
        
    def convert_pdf(self, pdf_path, output_path):
        """PDF를 레이아웃을 인식하여 변환"""
        print(f"레이아웃 인식 변환 시작: {pdf_path.name}")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n페이지 {page_num} 처리 중...")
                
                # 페이지별 처리
                page_content = self._process_page(page, page_num)
                self.pages_content.append(page_content)
        
        # Markdown 생성
        markdown = self._generate_markdown()
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"\n변환 완료: {output_path}")
        return True
    
    def _process_page(self, page, page_num):
        """페이지 처리"""
        # 1. 텍스트 블록 추출
        text_blocks = self._extract_text_blocks(page, page_num)
        
        # 2. 컬럼 경계 감지
        column_boundary = self._detect_column_boundary(text_blocks, page.width)
        
        # 3. 블록을 컬럼별로 분류
        left_blocks, right_blocks = self._classify_blocks_by_column(
            text_blocks, column_boundary
        )
        
        # 4. 각 컬럼 내에서 Y 좌표로 정렬
        left_blocks.sort(key=lambda b: b.y0)
        right_blocks.sort(key=lambda b: b.y0)
        
        # 5. 올바른 읽기 순서로 병합
        ordered_blocks = self._merge_columns_in_reading_order(
            left_blocks, right_blocks
        )
        
        # 6. 표 추출 및 매칭
        tables = page.extract_tables()
        
        return {
            'page_num': page_num,
            'blocks': ordered_blocks,
            'tables': tables
        }
    
    def _extract_text_blocks(self, page, page_num):
        """텍스트를 의미있는 블록으로 추출"""
        words = page.extract_words(keep_blank_chars=True)
        if not words:
            return []
        
        # 라인별로 그룹화
        lines = self._group_words_into_lines(words)
        
        # 라인을 블록으로 그룹화
        blocks = []
        for line in lines:
            if line:
                text = ' '.join(w['text'] for w in line)
                bbox = self._get_bbox_from_words(line)
                blocks.append(TextBlock(text=text, bbox=bbox, page=page_num))
        
        return blocks
    
    def _group_words_into_lines(self, words):
        """단어들을 라인으로 그룹화"""
        if not words:
            return []
        
        # Y 좌표로 정렬
        words.sort(key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = [words[0]]
        
        for word in words[1:]:
            # 같은 라인인지 확인 (Y 좌표 차이가 작으면)
            if abs(word['top'] - current_line[-1]['top']) < 5:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_bbox_from_words(self, words):
        """단어들로부터 바운딩 박스 계산"""
        x0 = min(w['x0'] for w in words)
        y0 = min(w['top'] for w in words)
        x1 = max(w['x1'] for w in words)
        y1 = max(w['bottom'] for w in words)
        return (x0, y0, x1, y1)
    
    def _detect_column_boundary(self, blocks, page_width):
        """컬럼 경계 감지"""
        if not blocks:
            return page_width / 2
        
        # 텍스트 블록들의 X 좌표 분포 분석
        x_positions = []
        for block in blocks:
            x_positions.extend([block.x0, block.x1])
        
        # 중앙 영역 찾기 (텍스트가 없는 영역)
        x_positions.sort()
        
        # 간격이 큰 곳 찾기
        gaps = []
        for i in range(len(x_positions) - 1):
            gap_start = x_positions[i]
            gap_end = x_positions[i + 1]
            gap_size = gap_end - gap_start
            
            if gap_size > 20:  # 충분히 큰 간격
                gaps.append((gap_start, gap_end, gap_size))
        
        # 페이지 중앙에 가장 가까운 큰 간격 찾기
        page_center = page_width / 2
        best_gap = None
        min_distance = float('inf')
        
        for gap_start, gap_end, gap_size in gaps:
            gap_center = (gap_start + gap_end) / 2
            distance = abs(gap_center - page_center)
            
            if distance < min_distance and gap_size > 30:
                min_distance = distance
                best_gap = gap_center
        
        # 경계가 없으면 페이지 중앙 사용
        boundary = best_gap if best_gap else page_center
        print(f"  컬럼 경계 감지: x={boundary:.1f}")
        
        return boundary
    
    def _classify_blocks_by_column(self, blocks, boundary):
        """블록을 컬럼별로 분류"""
        left_blocks = []
        right_blocks = []
        
        for block in blocks:
            # 블록의 중심점으로 판단
            if block.center_x < boundary:
                block.column = 1
                left_blocks.append(block)
            else:
                block.column = 2
                right_blocks.append(block)
        
        print(f"  좌측 컬럼: {len(left_blocks)}개 블록")
        print(f"  우측 컬럼: {len(right_blocks)}개 블록")
        
        return left_blocks, right_blocks
    
    def _merge_columns_in_reading_order(self, left_blocks, right_blocks):
        """컬럼을 올바른 읽기 순서로 병합"""
        if not left_blocks and not right_blocks:
            return []
        
        # 모든 블록을 복사 (원본 수정 방지)
        left = left_blocks.copy()
        right = right_blocks.copy()
        
        merged = []
        
        # Y 좌표 기준으로 병합
        while left or right:
            # 다음에 읽을 블록 선택
            next_block = None
            from_left = False
            
            if left and not right:
                next_block = left[0]
                from_left = True
            elif right and not left:
                next_block = right[0]
                from_left = False
            else:
                # 둘 다 있으면 Y 좌표가 더 위에 있는 것 선택
                if left[0].y0 <= right[0].y0:
                    # 좌측이 더 위에 있거나 같은 높이
                    # 같은 높이면 좌측 우선
                    next_block = left[0]
                    from_left = True
                else:
                    # 우측이 더 위에 있음
                    # 하지만 좌측에 아직 읽지 않은 내용이 있고
                    # 우측 블록이 좌측의 현재 영역 내에 있으면 좌측 계속
                    if left and right[0].y0 < left[0].y1:
                        next_block = left[0]
                        from_left = True
                    else:
                        next_block = right[0]
                        from_left = False
            
            # 선택된 블록 추가
            merged.append(next_block)
            
            # 리스트에서 제거
            if from_left:
                left.pop(0)
            else:
                right.pop(0)
        
        # 특수 케이스 처리: 물음 번호가 분리된 경우
        self._fix_split_questions(merged)
        
        return merged
    
    def _fix_split_questions(self, blocks):
        """분리된 물음 번호 수정"""
        i = 0
        while i < len(blocks) - 1:
            current = blocks[i]
            next_block = blocks[i + 1]
            
            # "(물음 X)" 패턴이 다음 블록의 시작에 있는지 확인
            if re.match(r'^\(물음\s*\d+\)', next_block.text):
                # 이전 블록과 병합 가능한지 확인
                if abs(current.y1 - next_block.y0) < 20:
                    # 텍스트 병합
                    current.text = current.text + ' ' + next_block.text
                    # 다음 블록 제거
                    blocks.pop(i + 1)
                    continue
            
            i += 1
    
    def _generate_markdown(self):
        """Markdown 생성"""
        lines = []
        lines.append("# 2024년 2차 원가회계 기출문제\n")
        lines.append("> 레이아웃 인식 변환\n")
        
        for page_content in self.pages_content:
            page_num = page_content['page_num']
            lines.append(f"\n---\n\n## 페이지 {page_num}\n")
            
            # 텍스트 블록 처리
            for block in page_content['blocks']:
                text = block.text.strip()
                
                # 패턴별 포맷팅
                if re.match(r'【문제\s*\d+】', text):
                    lines.append(f"\n### {text}\n")
                elif re.match(r'\(물음\s*\d+\)', text):
                    lines.append(f"\n#### {text}\n")
                elif text.startswith('※'):
                    lines.append(f"\n> {text}\n")
                elif '<자료' in text:
                    lines.append(f"\n##### {text}\n")
                elif '(답안양식)' in text:
                    lines.append(f"\n**[답안양식]**\n")
                else:
                    lines.append(f"{text}\n")
            
            # 표가 있다면 추가
            if page_content['tables']:
                for i, table in enumerate(page_content['tables']):
                    if self._is_valid_table(table):
                        lines.append("\n")
                        lines.append(self._table_to_markdown(table))
                        lines.append("\n")
        
        return '\n'.join(lines)
    
    def _is_valid_table(self, table):
        """유효한 표인지 확인"""
        if not table or len(table) < 2:
            return False
        non_empty = sum(1 for row in table for cell in row if cell and str(cell).strip())
        return non_empty >= 4
    
    def _table_to_markdown(self, table):
        """표를 Markdown으로 변환"""
        if not table:
            return ""
        
        lines = []
        
        # 헤더
        header = [str(cell) if cell else "" for cell in table[0]]
        lines.append("| " + " | ".join(header) + " |")
        
        # 구분선
        lines.append("|" + "|".join([" --- " for _ in header]) + "|")
        
        # 데이터
        for row in table[1:]:
            row_data = [str(cell) if cell else "" for cell in row]
            lines.append("| " + " | ".join(row_data) + " |")
        
        return "\n".join(lines)

def main():
    # 변환 실행
    converter = LayoutAwareConverter()
    
    pdf_path = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    output_path = Path("output-14-layout-aware.md")
    
    if pdf_path.exists():
        converter.convert_pdf(pdf_path, output_path)
        
        # 결과 미리보기
        with open(output_path, 'r', encoding='utf-8') as f:
            preview = f.read()[:2000]
            print("\n=== 변환 결과 미리보기 ===")
            print(preview)
            print("...")
    else:
        print(f"파일을 찾을 수 없습니다: {pdf_path}")

if __name__ == "__main__":
    main()