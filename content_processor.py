#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import random
from bs4 import BeautifulSoup
from PIL import Image
from datetime import datetime

logger = logging.getLogger("자동블로그.processor")

class ContentProcessor:
    """스크랩한 컨텐츠를 처리하고 변환하는 클래스"""
    
    def __init__(self):
        """ContentProcessor 초기화"""
        # 제목에 추가할 수 있는 접두어/접미어
        self.title_prefixes = [
            "완벽 분석 - ", 
            "상세 리뷰 - ", 
            "최신 정보 - ", 
            "알아보기 - ",
            "사용해보니 - ",
            "한눈에 보는 "
        ]
        
        # 본문 서두에 추가할 수 있는 문구
        self.intro_phrases = [
            "이번 포스팅에서는 {}에 대해 알아보겠습니다.",
            "오늘은 {}에 대한 상세한 정보를 공유해드립니다.",
            "많은 분들이 궁금해하시는 {}에 대해 정리해보았습니다.",
            "최근 화제가 되고 있는 {}을(를) 상세히 분석해보았습니다.",
            "{}에 대한 모든 것을 이 글에서 확인하세요."
        ]
        
        # 본문 말미에 추가할 수 있는 문구
        self.outro_phrases = [
            "이상으로 {}에 대한 정보를 알아보았습니다.",
            "지금까지 {}에 대해 알아보았습니다. 더 궁금한 점이 있으시면 댓글로 남겨주세요.",
            "{}에 대한 내용이 도움이 되셨기를 바랍니다.",
            "앞으로도 {}와(과) 관련된 유용한 정보를 계속 업데이트하겠습니다.",
            "{}에 대한 더 많은 정보와 팁은 다음 포스팅에서 확인하세요!"
        ]
    
    def process(self, content, images, app_info):
        """
        스크랩한 컨텐츠와 이미지를 처리하고 블로그 포스팅용 컨텐츠로 변환
        
        Args:
            content (dict): 스크랩한 컨텐츠 (title, url, main_content)
            images (list): 다운로드한 이미지 목록
            app_info (str): 앱 정보
            
        Returns:
            tuple: (제목, 처리된 HTML 컨텐츠)
        """
        try:
            # 원본 컨텐츠 가져오기
            original_title = content.get('title', '스크랩 컨텐츠')
            original_content = content.get('main_content', '')
            original_url = content.get('url', '')
            
            # 제목 처리
            title = self._process_title(original_title, app_info)
            
            # 내용 처리
            processed_content = self._process_content(original_content, images, app_info, original_url)
            
            return title, processed_content
            
        except Exception as e:
            logger.exception(f"컨텐츠 처리 중 오류 발생: {str(e)}")
            return content.get('title', '오류 발생'), f"<p>컨텐츠 처리 중 오류가 발생했습니다: {str(e)}</p>"
    
    def _process_title(self, original_title, app_info):
        """제목 처리"""
        # 제목에 앱 정보 추가 (없는 경우)
        if app_info.lower() not in original_title.lower():
            # 랜덤하게 접두어/접미어 선택
            if random.choice([True, False]):
                # 접두어 추가
                prefix = random.choice(self.title_prefixes)
                title = f"{prefix}{app_info} {original_title}"
            else:
                # 접미어 추가
                title = f"{original_title} - {app_info} 정보"
        else:
            title = original_title
            
        # 제목 길이 제한 (최대 100자)
        if len(title) > 100:
            title = title[:97] + "..."
            
        return title
    
    def _process_content(self, original_content, images, app_info, source_url):
        """내용 처리 및 HTML 변환"""
        # 원본 URL 보존 확인
        logger.info(f"컨텐츠 처리 - 소스 URL: {source_url}")
        
        # 원본 내용이 HTML인지 확인
        is_html = bool(re.search(r'<\s*[a-z]+[^>]*>', original_content))
        
        # HTML 파싱
        if is_html:
            try:
                # BeautifulSoup으로 HTML 파싱 시도
                soup = BeautifulSoup(original_content, 'lxml')
                
                # 불필요한 요소 제거 (스크립트, 스타일 등)
                for tag in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'aside']):
                    tag.decompose()
                
                # 원본 HTML에서 본문 추출
                processed_html = str(soup)
            except Exception as e:
                logger.warning(f"HTML 파싱 실패: {str(e)}. 원본 HTML을 사용합니다.")
                processed_html = original_content
        else:
            # 텍스트를 HTML로 변환
            paragraphs = original_content.split('\n\n')
            processed_html = "\n".join([f"<p>{p}</p>" for p in paragraphs if p.strip()])
        
        # HTML 구성 시작
        soup = BeautifulSoup(processed_html, 'lxml')
        html_parts = []
        
        # 도입부 추가
        intro = random.choice(self.intro_phrases).format(app_info)
        html_parts.append(f"<p>{intro}</p>")
        
        # 이미지 썸네일 처리 및 본문 시작 부분에 삽입
        if images:
            main_image = images[0]
            img_tag = f'<p><img src="{main_image["url"]}" alt="{main_image["alt"]}" title="{app_info}" class="img-fluid" /></p>'
            html_parts.append(img_tag)
        
        # 원본 HTML 컨텐츠 추가
        html_parts.append(processed_html)
        
        # 나머지 이미지 처리 및 삽입 (첫 번째 이미지는 이미 사용했으므로 제외)
        if len(images) > 1:
            remaining_images = images[1:]
            html = "\n".join(html_parts)
            soup = BeautifulSoup(html, 'lxml')
            
            # 컨텐츠 내의 단락 찾기
            paragraphs = soup.find_all('p')
            
            # 이미지 삽입 간격 계산 (단락 수에 따라 조정)
            if len(paragraphs) >= len(remaining_images) * 2:
                # 적절한 간격으로 이미지 삽입
                interval = max(1, len(paragraphs) // len(remaining_images))
                for i, img in enumerate(remaining_images):
                    pos = min((i + 1) * interval, len(paragraphs) - 1)
                    img_tag = soup.new_tag("p")
                    img_element = soup.new_tag("img", src=img["url"], alt=img["alt"], title=app_info, **{"class": "img-fluid"})
                    img_tag.append(img_element)
                    
                    # 이미지 삽입
                    if pos < len(paragraphs):
                        paragraphs[pos].insert_after(img_tag)
            
            # 수정된 HTML 생성
            html_parts = [str(soup)]
        
        # 앱 정보 강조
        html = "\n".join(html_parts)
        soup = BeautifulSoup(html, 'lxml')
        
        # 앱 정보를 강조 표시
        for text in soup.find_all(text=re.compile(re.escape(app_info))):
            if text.parent.name not in ['strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                new_text = text.replace(app_info, f"<strong>{app_info}</strong>")
                new_soup = BeautifulSoup(new_text, 'lxml')
                text.replace_with(new_soup)
        
        # 맺음말 추가
        outro_tag = soup.new_tag("p")
        outro_tag.string = random.choice(self.outro_phrases).format(app_info)
        soup.append(outro_tag)
        
        # 출처 표시 (원본 URL 사용)
        source_tag = soup.new_tag("p")
        source_tag.append(soup.new_tag("small"))
        source_tag.small.string = "참고: "
        
        # URL 유효성 검증
        if not source_url.startswith(('http://', 'https://')):
            logger.warning(f"유효하지 않은 소스 URL: {source_url}")
            source_url = "https://" + source_url if source_url else "출처 정보 없음"
        
        link = soup.new_tag("a", href=source_url, target="_blank", rel="nofollow")
        link.string = source_url
        source_tag.small.append(link)
        
        # 출처 로깅
        logger.info(f"컨텐츠 출처 URL: {source_url}")
        
        soup.append(source_tag)
        
        # 최종 HTML 컨텐츠 생성
        html_content = str(soup.body).replace("<body>", "").replace("</body>", "") if soup.body else str(soup)
        
        return html_content
        
    def _resize_image(self, image_path, max_width=800):
        """이미지 크기 조정 (옵션)"""
        try:
            img = Image.open(image_path)
            # 이미지가 최대 너비보다 크면 크기 조정
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                resized_img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                resized_img.save(image_path)
                logger.info(f"이미지 크기 조정 완료: {image_path} ({img.width}x{img.height} -> {max_width}x{new_height})")
        except Exception as e:
            logger.warning(f"이미지 크기 조정 실패: {image_path} - {str(e)}") 