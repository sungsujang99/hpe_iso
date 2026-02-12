"""
템플릿 전체 동기화 커맨드
사용법: python manage.py sync_templates
"""
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from apps.documents.models import DocumentCategory, DocumentTemplate


class Command(BaseCommand):
    help = '모든 문서 템플릿을 DB에 동기화합니다 (카테고리 + fixture + 엑셀 파일)'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('템플릿 동기화 시작')
        self.stdout.write('=' * 60)

        # 0) HP-QR → HP-QM 마이그레이션 (기존 서버 데이터 정리)
        self._migrate_qr_to_qm()

        # 1) 카테고리 시드
        self._seed_categories()

        # 2) fixture 기반 텍스트 템플릿
        self._seed_fixture_templates()

        # 3) 단독 엑셀 템플릿
        self._seed_solo_excel()

        # 4) 9001 전체 양식
        self._seed_9001()

        # 5) 45001 전체 양식
        self._seed_45001()

        total = DocumentTemplate.objects.count()
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'동기화 완료! 총 템플릿: {total}개'))
        self.stdout.write('=' * 60)

    def _migrate_qr_to_qm(self):
        """HP-QR 카테고리를 HP-QM으로 통합 (서버 호환용)"""
        qr = DocumentCategory.objects.filter(code='HP-QR').first()
        if not qr:
            self.stdout.write('  HP-QR 없음 (이미 마이그레이션됨)')
            return

        qm, _ = DocumentCategory.objects.get_or_create(
            code='HP-QM', defaults={'name': '품질경영 매뉴얼', 'prefix': 'HP-QM-'}
        )

        # 템플릿 이동
        moved = DocumentTemplate.objects.filter(category=qr).update(category=qm)
        self.stdout.write(f'  HP-QR → HP-QM: {moved}개 템플릿 이동')

        # 템플릿 이름에서 HP-QR → HP-QM 치환
        renamed = 0
        for t in DocumentTemplate.objects.filter(name__contains='HP-QR'):
            t.name = t.name.replace('HP-QR', 'HP-QM')
            t.save()
            renamed += 1
        if renamed:
            self.stdout.write(f'  HP-QR → HP-QM: {renamed}개 이름 변경')

        # 관련 문서도 이동
        try:
            from apps.documents.models import Document
            doc_moved = Document.objects.filter(category=qr).update(category=qm)
            if doc_moved:
                self.stdout.write(f'  HP-QR → HP-QM: {doc_moved}개 문서 이동')
        except Exception:
            pass

        # HP-QR 카테고리 삭제
        try:
            qr.delete()
            self.stdout.write(self.style.SUCCESS('  HP-QR 카테고리 삭제 완료'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  HP-QR 삭제 실패: {e}'))

    def _seed_categories(self):
        categories = [
            ('HP-QM', '품질경영 매뉴얼', 'HP-QM-'),
            ('HP-QP', '품질절차서', 'HP-QP-'),
            ('HP-QI', '품질경영 지침서', 'HP-QI-'),
            ('HP-EM', '환경경영 매뉴얼', 'HP-EM-'),
            ('HP-EP', '기술절차서', 'HP-EP-'),
            ('HP-EI', '환경경영 지침서', 'HP-EI-'),
            ('HP-WI', '작업지시서', 'HP-WI-'),
        ]
        created = 0
        for code, name, prefix in categories:
            _, is_new = DocumentCategory.objects.get_or_create(
                code=code, defaults={'name': name, 'prefix': prefix}
            )
            if is_new:
                created += 1
        self.stdout.write(f'  카테고리: {created}개 신규')

    def _seed_fixture_templates(self):
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'fixtures', 'templates.json'
        )
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.WARNING(f'  fixture 없음: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cat_map = {c.code: c for c in DocumentCategory.objects.all()}
        created = 0
        for item in data:
            cc = item.get('category_code', '')
            cat = cat_map.get(cc)
            if not cat:
                continue
            _, is_new = DocumentTemplate.objects.get_or_create(
                category=cat, name=item['name'],
                defaults={
                    'description': item.get('description', ''),
                    'fields_schema': item.get('fields_schema', {}),
                    'template_file': item.get('template_file', ''),
                    'is_active': item.get('is_active', True),
                    'version': item.get('version', '1.0'),
                }
            )
            if is_new:
                created += 1
        self.stdout.write(f'  fixture 템플릿: {created}개 신규')

    def _register_excel(self, name, filepath, category, description=''):
        """엑셀 파일을 템플릿으로 등록 (이미 있으면 파일만 갱신)"""
        if not filepath.exists():
            return False
        t, _ = DocumentTemplate.objects.get_or_create(
            name=name,
            defaults={
                'category': category,
                'description': description or name,
                'is_active': True,
                'version': '1.0',
                'fields_schema': {},
            }
        )
        # 파일이 없으면 저장
        if not t.template_file:
            with open(filepath, 'rb') as f:
                t.template_file.save(filepath.name, File(f), save=True)
        return True

    def _seed_solo_excel(self):
        cat_map = {c.code: c for c in DocumentCategory.objects.all()}
        base = Path(settings.MEDIA_ROOT) / 'document_templates'
        items = [
            ('내부심사 체크리스트 (HP-QP-940)', '내부심사_체크리스트_템플릿', 'HP-QP'),
            ('부적합품 관리대장 (HP-QM-870)', '부적합품_관리대장_템플릿', 'HP-QM'),
            ('업무분장표 (HP-QM-520)', '업무분장표_템플릿', 'HP-QM'),
            ('AS 관리대장 (HP-QM-854)', 'AS_관리대장_템플릿', 'HP-QM'),
        ]
        created = 0
        for name, fn_prefix, cc in items:
            cat = cat_map.get(cc)
            if not cat:
                continue
            files = list(base.glob(f'{fn_prefix}*.xlsx'))
            if not files:
                continue
            if self._register_excel(name, files[0], cat):
                created += 1
        self.stdout.write(f'  단독 엑셀: {created}개 처리')

    def _seed_9001(self):
        cat_map = {c.code: c for c in DocumentCategory.objects.all()}
        d = Path(settings.MEDIA_ROOT) / 'document_templates' / '9001'
        if not d.exists():
            self.stdout.write(self.style.WARNING('  9001 폴더 없음'))
            return
        m = [
            ('SWOT 분석표','SWOT_분석표.xlsx','HP-QM','HP-QM-410'),('이해관계자 파악표','이해관계자_파악표.xlsx','HP-QM','HP-QM-410-2'),
            ('조직 및 업무분장 관리','조직_및_업무분장_관리.xlsx','HP-QP','HP-QP-520'),('업무분장표 (9001)','업무분장표_9001.xlsx','HP-QM','HP-QM-520'),
            ('리스크 및 기회관리 조치 계획서','리스크_기회관리_조치_계획서.xlsx','HP-QM','HP-QM-610'),
            ('업무 환경관리 검토서','업무_환경관리_검토서.xlsx','HP-QM','HP-QM-710'),
            ('5S 평가 체크리스트 (현장용)','5S_평가_체크리스트_현장용.xlsx','HP-QM','HP-QM-710-2'),
            ('5S 평가 체크리스트 (사무실용)','5S_평가_체크리스트_사무실용.xlsx','HP-QM','HP-QM-710-3'),
            ('설비 관리 대장','설비_관리_대장.xlsx','HP-QM','HP-QM-720'),('설비 이력 카드','설비_이력_카드.xlsx','HP-QM','HP-QM-720-2'),
            ('계측장비 관리대장','계측장비_관리대장.xlsx','HP-QM','HP-QM-730'),('계측장비 이력카드','계측장비_이력카드.xlsx','HP-QM','HP-QM-730-2'),
            ('교육훈련 계획서','교육훈련_계획서.xlsx','HP-QM','HP-QM-740'),('교육결과 보고서','교육결과_보고서.xlsx','HP-QM','HP-QM-740-2'),
            ('개인별 교육훈련 이력카드','개인별_교육훈련_이력카드.xlsx','HP-QM','HP-QM-740-3'),
            ('자격인증 관리대장','자격인증_관리대장.xlsx','HP-QM','HP-QM-741'),('자격인증 평가표','자격인증_평가표.xlsx','HP-QM','HP-QM-741-2'),
            ('자격인증서','자격인증서.xlsx','HP-QM','HP-QM-741-3'),
            ('환경정보 보고서','환경정보_보고서.xlsx','HP-QM','HP-QM-750'),('의사소통 관리대장','의사소통_관리대장.xlsx','HP-QM','HP-QM-750-2'),
            ('회의록','회의록.xlsx','HP-QM','HP-QM-750-3'),
            ('문서 제개정 심의서','문서_제개정_심의서.xlsx','HP-QM','HP-QM-760'),('문서배포처 대장','문서배포처_대장.xlsx','HP-QM','HP-QM-760-2'),
            ('문서파일 목록','문서파일_목록.xlsx','HP-QM','HP-QM-760-3'),('사외규격 관리대장','사외규격_관리대장.xlsx','HP-QM','HP-QM-760-4'),
            ('전자매체 관리대장','전자매체_관리대장.xlsx','HP-QM','HP-QM-760-5'),
            ('계약검토서','계약검토서.xlsx','HP-QM','HP-QM-810'),('계약관리대장','계약관리대장.xlsx','HP-QM','HP-QM-810-2'),
            ('설계 검토검증서','설계_검토검증서.xlsx','HP-QM','HP-QM-820'),('설계 검토검증 체크리스트','설계_검토검증_체크리스트.xlsx','HP-QM','HP-QM-820-2'),
            ('협의록','협의록.xlsx','HP-QM','HP-QM-820-3'),('CAD도면 출력대장','CAD도면_출력대장.xlsx','HP-QM','HP-QM-820-4'),
            ('구매요청서','구매요청서.xlsx','HP-QM','HP-QM-830'),('거래명세서','거래명세서.xlsx','HP-QM','HP-QM-830-2'),
            ('발주서','발주서.xlsx','HP-QM','HP-QM-830-3'),('견적서','견적서.xlsx','HP-QM','HP-QM-830-4'),
            ('업태실태 조사서','업태실태_조사서.xlsx','HP-QM','HP-QM-840'),('협력업체 등록대장','협력업체_등록대장.xlsx','HP-QM','HP-QM-840-2'),
            ('협력업체 평가표','협력업체_평가표.xlsx','HP-QM','HP-QM-840-3'),('협력업체 정기평가표','협력업체_정기평가표.xlsx','HP-QM','HP-QM-840-4'),
            ('작업지시서','작업지시서.xlsx','HP-QM','HP-QM-850'),('ORDER별 생산일지','ORDER별_생산일지.xlsx','HP-QM','HP-QM-850-2'),
            ('작업표준서','작업표준서.xlsx','HP-QM','HP-QM-850-3'),('제조QC 공정도','제조QC_공정도.xlsx','HP-QM','HP-QM-850-4'),
            ('고객자산 관리대장','고객자산_관리대장.xlsx','HP-QM','HP-QM-852'),
            ('자재 점검일지','자재_점검일지.xlsx','HP-QM','HP-QM-853'),('자재 수불대장','자재_수불대장.xlsx','HP-QM','HP-QM-853-2'),
            ('고객불만 AS 사항','고객불만_AS_사항.xlsx','HP-QM','HP-QM-854'),('고객요구 불만접수 처리대장','고객요구_불만접수_처리대장.xlsx','HP-QM','HP-QM-854-2'),
            ('수입검사 성적서','수입검사_성적서.xlsx','HP-QM','HP-QM-860'),('공정검사 성적서','공정검사_성적서.xlsx','HP-QM','HP-QM-860-2'),
            ('최종검사 성적서','최종검사_성적서.xlsx','HP-QM','HP-QM-860-3'),('성적서 확인검사 품목','성적서_확인검사_품목.xlsx','HP-QM','HP-QM-860-4'),
            ('부적합 보고서','부적합_보고서.xlsx','HP-QM','HP-QM-870'),('부적합 관리대장','부적합_관리대장.xlsx','HP-QM','HP-QM-870-2'),
            ('성과지표 관리대장','성과지표_관리대장.xlsx','HP-QM','HP-QM-910'),
            ('고객만족도 조사표','고객만족도_조사표.xlsx','HP-QM','HP-QM-920'),('고객만족도 평가표','고객만족도_평가표.xlsx','HP-QM','HP-QM-920-2'),
            ('내부심사 일정표','내부심사_일정표.xlsx','HP-QM','HP-QM-940'),('내부심사 실시계획 통보서','내부심사_실시계획_통보서.xlsx','HP-QM','HP-QM-940-2'),
            ('내부심사 체크리스트 (9001)','내부심사_체크리스트_9001.xlsx','HP-QM','HP-QM-940-3'),('내부심사 결과보고서','내부심사_결과보고서.xlsx','HP-QM','HP-QM-940-4'),
            ('품질 경영검토서','품질_경영검토서.xlsx','HP-QM','HP-QM-950'),('품질 경영검토서 (2)','품질_경영검토서_2.xlsx','HP-QM','HP-QM-950-2'),
            ('시정조치 요구서','시정조치_요구서.xlsx','HP-QM','HP-QM-1010'),('시정조치 관리대장','시정조치_관리대장.xlsx','HP-QM','HP-QM-1010-2'),
        ]
        count = 0
        for title, fn, cc, dn in m:
            cat = cat_map.get(cc)
            if not cat:
                continue
            p = d / fn
            if self._register_excel(f'{title} ({dn})', p, cat, f'ISO 9001 - {title}'):
                count += 1
        self.stdout.write(f'  9001 양식: {count}개 처리')

    def _seed_45001(self):
        cat_qm = DocumentCategory.objects.filter(code='HP-QM').first()
        if not cat_qm:
            return
        d = Path(settings.MEDIA_ROOT) / 'document_templates' / '45001'
        if not d.exists():
            self.stdout.write(self.style.WARNING('  45001 폴더 없음'))
            return
        m = [
            ('안전보건 관리조직표','안전보건_관리조직표.xlsx','HP-QM-45001-01'),
            ('안전보건경영검토 보고서','안전보건경영검토_보고서.xlsx','HP-QM-45001-02'),
            ('공정별 유해위험요인 조사 보고서','공정별_유해위험요인_조사보고서.xlsx','HP-QM-45001-03'),
            ('위험성 평가표','위험성_평가표.xlsx','HP-QM-45001-04'),
            ('안전심사 일정표','안전심사_일정표.xlsx','HP-QM-45001-05'),
            ('안전심사 점검표','안전심사_점검표.xlsx','HP-QM-45001-06'),
            ('안전심사 보고서','안전심사_보고서.xlsx','HP-QM-45001-07'),
            ('안전심사 점검표(상세)','안전심사_점검표_상세.xlsx','HP-QM-45001-08'),
            ('비상사태 대응 프로세스(화재폭발)','비상사태_대응_화재폭발.xlsx','HP-QM-45001-09'),
            ('비상사태 대응 프로세스(태풍침수)','비상사태_대응_태풍침수.xlsx','HP-QM-45001-10'),
            ('비상사태 대응 프로세스(누출)','비상사태_대응_누출.xlsx','HP-QM-45001-11'),
            ('안전 교육 프로그램','안전_교육_프로그램.xlsx','HP-QM-45001-12'),
            ('안전 연간 교육계획표','안전_연간_교육계획표.xlsx','HP-QM-45001-13'),
            ('안전 교육 보고서','안전_교육_보고서.xlsx','HP-QM-45001-14'),
            ('안전 교육 참석자 명단','안전_교육_참석자명단.xlsx','HP-QM-45001-15'),
            ('안전부적합 조치 관리대장','안전부적합_조치_관리대장.xlsx','HP-QM-45001-16'),
            ('안전부적합 조치 보고서','안전부적합_조치_보고서.xlsx','HP-QM-45001-17'),
        ]
        count = 0
        for title, fn, dn in m:
            p = d / fn
            if self._register_excel(f'{title} ({dn})', p, cat_qm, f'ISO 45001 - {title}'):
                count += 1
        self.stdout.write(f'  45001 양식: {count}개 처리')
