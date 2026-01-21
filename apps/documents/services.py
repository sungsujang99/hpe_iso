"""
Document Services - PDF Generation
ISO 9001/14001 표준 서식 적용 (사용자 제공 양식 기반)
"""
import os
import io
from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class ISOStandardDocTemplate(SimpleDocTemplate):
    """ISO 표준 문서 템플릿 (모든 페이지에 헤더/푸터 고정)"""
    
    def __init__(self, *args, document=None, korean_font='Helvetica', **kwargs):
        super().__init__(*args, **kwargs)
        self.document = document
        self.korean_font = korean_font
        self.total_pages = 0
        
        # 회사명 및 문서번호 (고정값)
        self.company_name = getattr(settings, 'COMPANY_NAME', '주식회사 에이치피엔지니어링')
        self.company_name_en = getattr(settings, 'COMPANY_NAME_EN', 'HP Engineering Co.,Ltd')
        self.doc_number = document.document_number if document else ''
        self.doc_title = document.title if document else ''
        self.category_name = document.category.name if document and document.category else ''
    
    def handle_pageBegin(self):
        """각 페이지 시작 시 호출"""
        self._pageNum += 1
        self.canv.saveState()
        
    def onFirstPage(self, canvas, doc):
        """첫 페이지 헤더/푸터"""
        self._draw_header_footer(canvas, doc, is_first=True)
    
    def onLaterPages(self, canvas, doc):
        """나머지 페이지 헤더/푸터"""
        self._draw_header_footer(canvas, doc, is_first=False)
    
    def _draw_header_footer(self, canvas, doc, is_first=False):
        """헤더와 푸터 그리기 (ISO 표준 형식)"""
        canvas.saveState()
        
        page_num = canvas.getPageNumber()
        
        # 헤더 테이블 (ISO 표준 형식 - 사용자 제공 양식 기반)
        # 상단에서 15mm 위치
        y_position = A4[1] - 15*mm
        
        # 테이블 그리기
        table_width = A4[0] - 40*mm  # 좌우 여백 각 20mm
        col_widths = [table_width * 0.35, table_width * 0.25, table_width * 0.15, table_width * 0.25]
        
        # 헤더 테이블 데이터 (4행 x 4열)
        # 행 1: 회사명(영문) | 문서종류 | 문서번호 텍스트 | 문서번호
        # 행 2: 회사명(한글) | (공백) | 제.개정일자 텍스트 | 제.개정일자
        # 행 3: (공백) | 문서제목 | 개정번호 텍스트 | 개정번호
        # 행 4: (공백) | (공백) | 페이지 텍스트 | 페이지번호
        
        revision_date = self.document.approved_at.strftime('%Y.%m.%d') if self.document.approved_at else self.document.created_at.strftime('%Y.%m.%d')
        
        x_start = 20*mm
        row_height = 6*mm
        
        # 그리드 그리기
        canvas.setLineWidth(0.5)
        # 세로선
        for i, w in enumerate([0] + col_widths):
            x = x_start + sum(col_widths[:i]) if i > 0 else x_start
            canvas.line(x, y_position, x, y_position - 4 * row_height)
        canvas.line(x_start + sum(col_widths), y_position, x_start + sum(col_widths), y_position - 4 * row_height)
        
        # 가로선
        for i in range(5):
            y = y_position - i * row_height
            canvas.line(x_start, y, x_start + sum(col_widths), y)
        
        # 텍스트 작성
        canvas.setFont(self.korean_font, 9)
        
        # 행 1
        canvas.drawString(x_start + 2, y_position - row_height + 2, self.company_name_en)
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1]/2, y_position - row_height + 2, self.category_name)
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2]/2, y_position - row_height + 2, '문서번호')
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]/2, y_position - row_height + 2, self.doc_number)
        
        # 행 2
        canvas.drawString(x_start + 2, y_position - 2*row_height + 2, self.company_name)
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2]/2, y_position - 2*row_height + 2, '제.개정일자')
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]/2, y_position - 2*row_height + 2, revision_date)
        
        # 행 3
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1]/2, y_position - 3*row_height + 2, self.doc_title[:30])  # 제목 길이 제한
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2]/2, y_position - 3*row_height + 2, '개정번호')
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]/2, y_position - 3*row_height + 2, str(self.document.revision))
        
        # 행 4
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2]/2, y_position - 4*row_height + 2, '페이지')
        # 총 페이지 수는 빌드 후에 알 수 있으므로 일단 현재 페이지만 표시
        canvas.drawCentredString(x_start + col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3]/2, y_position - 4*row_height + 2, f'{page_num}')
        
        # 푸터 (하단) - 문서번호 | 회사명 | 용지크기
        canvas.setFont(self.korean_font, 8)
        canvas.setFillColor(colors.grey)
        footer_y = 12*mm
        footer_text = f"{self.doc_number}  |  {self.company_name}  |  A4(210mm x 297mm)"
        canvas.drawCentredString(A4[0] / 2, footer_y, footer_text)
        
        canvas.restoreState()


class PDFGenerator:
    """ISO 문서 PDF 생성기"""
    
    def __init__(self):
        self.width, self.height = A4
        self.margin = 20 * mm
        self.styles = getSampleStyleSheet()
        self._setup_fonts()
        self._setup_styles()
    
    def _setup_fonts(self):
        """폰트 설정 (한글 지원)"""
        # 시스템 폰트 경로 (macOS/Linux/Windows)
        font_paths = [
            '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS - Apple SD Gothic Neo
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',  # macOS - Apple Gothic
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # Linux - Nanum Gothic
            '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',  # Linux - Nanum Barun Gothic
            'C:/Windows/Fonts/malgun.ttf',  # Windows - 맑은 고딕
            'C:/Windows/Fonts/gulim.ttc',  # Windows - 굴림
        ]
        
        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # TTC 파일인 경우 subfontIndex 지정
                    if font_path.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont('Korean', font_path, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont('Korean', font_path))
                    font_registered = True
                    print(f"✓ 한글 폰트 로드 성공: {font_path}")
                    break
                except Exception as e:
                    print(f"✗ 한글 폰트 로드 실패 ({font_path}): {e}")
                    continue
        
        if not font_registered:
            # 기본 폰트 사용 (한글 지원 안됨)
            print("⚠ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            self.korean_font = 'Helvetica'
        else:
            self.korean_font = 'Korean'
    
    def _setup_styles(self):
        """스타일 설정"""
        self.styles.add(ParagraphStyle(
            name='TitleKorean',
            fontName=self.korean_font,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=8,
            leading=20,
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading1Korean',
            fontName=self.korean_font,
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=12,
            leading=18,
            textColor=colors.black,
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading2Korean',
            fontName=self.korean_font,
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=10,
            leading=16,
            textColor=colors.black,
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyKorean',
            fontName=self.korean_font,
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=4,
            leading=14,
            textColor=colors.black,
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyJustifyKorean',
            fontName=self.korean_font,
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
            leading=14,
            textColor=colors.black,
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeaderKorean',
            fontName=self.korean_font,
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.black,
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableBodyKorean',
            fontName=self.korean_font,
            fontSize=9,
            alignment=TA_LEFT,
            textColor=colors.black,
        ))
    
    def generate_document_pdf(self, document):
        """ISO 9001/14001 표준 서식으로 문서 PDF 생성"""
        buffer = io.BytesIO()
        
        # ISO 표준 서식: 상단 여백 40mm (헤더 공간), 하단 여백 20mm
        doc = ISOStandardDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=40 * mm,  # 헤더 테이블 공간 확보
            bottomMargin=20 * mm,
            document=document,
            korean_font=self.korean_font
        )
        
        story = []
        
        # 관리본/비관리본 체크박스
        story.extend(self._create_control_checkbox(document))
        story.append(Spacer(1, 5 * mm))
        
        # 개정이력 테이블
        story.append(self._create_revision_history_table(document))
        story.append(Spacer(1, 8 * mm))
        
        # 문서 내용
        story.extend(self._create_content(document))
        
        # 서명란 (작성/검토/승인)
        story.append(Spacer(1, 15 * mm))
        story.append(self._create_signature_table(document))
        
        # 문서 생성
        doc.build(story)
        
        # 파일 저장
        buffer.seek(0)
        filename = f"{document.document_number}_rev{document.revision}.pdf"
        
        return ContentFile(buffer.read(), name=filename)
    
    def _create_control_checkbox(self, document):
        """관리본/비관리본 체크박스"""
        elements = []
        
        # 승인된 문서는 관리본, 아니면 비관리본
        if document.status == 'approved':
            control_text = '☑ 관리본    ☐ 비관리본'
        else:
            control_text = '☐ 관리본    ☑ 비관리본'
        
        control_para = Paragraph(control_text, self.styles['BodyKorean'])
        elements.append(control_para)
        
        return elements
    
    def _create_revision_history_table(self, document):
        """개정이력 테이블 (ISO 표준 형식)"""
        # 헤더
        header_row = [
            Paragraph('<b>제정<br/>번호</b>', self.styles['TableHeaderKorean']),
            Paragraph('<b>제.개정일자</b>', self.styles['TableHeaderKorean']),
            Paragraph('<b>제.개정내용 및 사유</b>', self.styles['TableHeaderKorean']),
            Paragraph('<b>비고</b>', self.styles['TableHeaderKorean']),
        ]
        
        # 데이터 행
        revision_date = document.approved_at.strftime('%Y.%m.%d') if document.approved_at else document.created_at.strftime('%Y.%m.%d')
        
        # 카테고리별 제.개정내용 자동 생성
        if 'ISO 9001' in document.category.name or 'ISO9001' in document.category.name or '품질' in document.category.name:
            revision_content = 'ISO 9001:2015/KS Q ISO 9001:2015 품질경영시스템 요구사항을 근거로 신규 제정'
        elif 'ISO 14001' in document.category.name or 'ISO14001' in document.category.name or '환경' in document.category.name:
            revision_content = 'ISO 14001:2015/KS I ISO 14001:2015 환경경영시스템 요구사항을 근거로 신규 제정'
        else:
            revision_content = '신규 제정'
        
        data_row = [
            Paragraph(str(document.revision), self.styles['TableBodyKorean']),
            Paragraph(revision_date, self.styles['TableBodyKorean']),
            Paragraph(revision_content, self.styles['TableBodyKorean']),
            Paragraph('', self.styles['TableBodyKorean']),
        ]
        
        table_data = [header_row, data_row]
        
        # 테이블 너비: A4 - 좌우 여백 40mm
        table_width = A4[0] - 40*mm
        col_widths = [table_width * 0.12, table_width * 0.18, table_width * 0.55, table_width * 0.15]
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('ALIGN', (1, 1), (1, 1), 'CENTER'),
            ('ALIGN', (2, 1), (2, 1), 'LEFT'),
            ('ALIGN', (3, 1), (3, 1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return table
    
    def _create_content(self, document):
        """문서 내용 생성 (템플릿 필드 스키마 기반)"""
        elements = []
        content_data = document.content_data or {}
        
        # 템플릿이 있는 경우 필드 스키마에 따라 렌더링
        if document.template and document.template.fields_schema:
            schema = document.template.fields_schema
            fields = schema.get('fields', [])
            
            for idx, field in enumerate(fields):
                field_name = field.get('name', '')
                field_label = field.get('label', field_name)
                field_value = content_data.get(field_name, '')
                field_type = field.get('type', 'text')
                
                # 필드 라벨 (섹션 번호 자동 생성)
                if field_label:
                    # 주요 섹션인 경우 제목 스타일 사용
                    if any(keyword in field_label for keyword in ['목적', '적용범위', '정의', '책임', '절차', '기록', '참조', '부록', '방침', '목표']):
                        section_num = f"{idx + 1}."
                        elements.append(Paragraph(f"<b>{section_num} {field_label}</b>", self.styles['Heading1Korean']))
                    else:
                        elements.append(Paragraph(f"<b>{field_label}</b>", self.styles['Heading2Korean']))
                
                # 필드 값
                if field_value:
                    # 긴 텍스트는 줄바꿈 처리
                    if isinstance(field_value, str):
                        # 줄바꿈을 <br/>로 변환
                        formatted_value = field_value.replace('\n', '<br/>')
                        elements.append(Paragraph(formatted_value, self.styles['BodyJustifyKorean']))
                    else:
                        elements.append(Paragraph(str(field_value), self.styles['BodyJustifyKorean']))
                else:
                    # 빈 값인 경우 공백 표시
                    elements.append(Paragraph('(내용 없음)', self.styles['BodyKorean']))
                
                elements.append(Spacer(1, 6 * mm))
        else:
            # 기본 필드 렌더링 (템플릿이 없는 경우)
            field_mapping = {
                'occurrence_date': '발생 일시',
                'nonconformity_content': '부적합 내용',
                'cause_analysis': '원인 분석',
                'corrective_action': '시정 조치 계획',
                'preventive_action': '예방 조치',
                'target_date': '목표 완료일',
                'remarks': '비고',
            }
            
            for key, label in field_mapping.items():
                if key in content_data and content_data[key]:
                    elements.append(Paragraph(f"<b>{label}</b>", self.styles['Heading2Korean']))
                    formatted_value = str(content_data[key]).replace('\n', '<br/>')
                    elements.append(Paragraph(formatted_value, self.styles['BodyJustifyKorean']))
                    elements.append(Spacer(1, 5 * mm))
            
            # 나머지 필드
            for key, value in content_data.items():
                if key not in field_mapping and value:
                    elements.append(Paragraph(f"<b>{key}</b>", self.styles['Heading2Korean']))
                    formatted_value = str(value).replace('\n', '<br/>')
                    elements.append(Paragraph(formatted_value, self.styles['BodyJustifyKorean']))
                    elements.append(Spacer(1, 5 * mm))
        
        return elements
    
    def _create_signature_table(self, document):
        """서명란 테이블 (ISO 표준 형식)"""
        # 서명 데이터
        writer_name = document.created_by.get_full_name() if document.created_by else ''
        writer_date = document.created_at.strftime('%Y.%m.%d') if document.created_at else ''
        
        reviewer_name = document.reviewed_by.get_full_name() if document.reviewed_by else ''
        reviewer_date = document.reviewed_at.strftime('%Y.%m.%d') if document.reviewed_at else ''
        
        approver_name = document.approved_by.get_full_name() if document.approved_by else ''
        approver_date = document.approved_at.strftime('%Y.%m.%d') if document.approved_at else ''
        
        # 서명 테이블 데이터
        sig_data = [
            [
                Paragraph('<b>구분</b>', self.styles['TableHeaderKorean']),
                Paragraph('<b>작성</b>', self.styles['TableHeaderKorean']),
                Paragraph('<b>검토</b>', self.styles['TableHeaderKorean']),
                Paragraph('<b>승인</b>', self.styles['TableHeaderKorean']),
            ],
            [
                Paragraph('<b>확인</b>', self.styles['TableHeaderKorean']),
                Paragraph('', self.styles['TableBodyKorean']),
                Paragraph('', self.styles['TableBodyKorean']),
                Paragraph('', self.styles['TableBodyKorean']),
            ],
            [
                Paragraph('<b>일자</b>', self.styles['TableHeaderKorean']),
                Paragraph(writer_date, self.styles['TableBodyKorean']),
                Paragraph(reviewer_date, self.styles['TableBodyKorean']),
                Paragraph(approver_date, self.styles['TableBodyKorean']),
            ],
            [
                Paragraph('', self.styles['TableBodyKorean']),
                Paragraph(writer_name, self.styles['TableBodyKorean']),
                Paragraph(reviewer_name, self.styles['TableBodyKorean']),
                Paragraph(approver_name, self.styles['TableBodyKorean']),
            ],
        ]
        
        # 테이블 너비
        table_width = A4[0] - 40*mm
        col_widths = [table_width * 0.2, table_width * 0.27, table_width * 0.27, table_width * 0.26]
        
        table = Table(sig_data, colWidths=col_widths, rowHeights=[8*mm, 12*mm, 8*mm, 8*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),  # 구분 열 배경
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        return table
    
    def _add_watermark_to_pdf(self, pdf_buffer, watermark_text="관리본"):
        """PDF에 워터마크 추가"""
        try:
            from PyPDF2 import PdfReader, PdfWriter
            
            # 워터마크 PDF 생성
            watermark_buffer = io.BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=A4)
            
            c.setFont(self.korean_font, 60)
            c.setFillColor(colors.Color(0.8, 0.8, 0.8, alpha=0.3))
            c.saveState()
            c.translate(A4[0] / 2, A4[1] / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
            c.save()
            
            watermark_buffer.seek(0)
            watermark_pdf = PdfReader(watermark_buffer)
            watermark_page = watermark_pdf.pages[0]
            
            # 원본 PDF 읽기
            pdf_buffer.seek(0)
            pdf_reader = PdfReader(pdf_buffer)
            pdf_writer = PdfWriter()
            
            # 모든 페이지에 워터마크 추가
            for page in pdf_reader.pages:
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)
            
            # 새 버퍼에 저장
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer
        except Exception as e:
            print(f"워터마크 추가 실패: {e}")
            pdf_buffer.seek(0)
            return pdf_buffer


def generate_pdf(document):
    """PDF 생성 헬퍼 함수"""
    generator = PDFGenerator()
    return generator.generate_document_pdf(document)
