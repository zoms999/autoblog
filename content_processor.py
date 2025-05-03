#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import random
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
        # 본문 구성을 위한 준비
        paragraphs = original_content.split('\n\n')
        
        # HTML 구성 시작
        html_parts = []
        
        # 도입부 추가
        intro = random.choice(self.intro_phrases).format(app_info)
        html_parts.append(f"<p>{intro}</p>")
        
        # 이미지 썸네일 처리 및 본문 시작 부분에 삽입
        if images:
            main_image = images[0]
            img_tag = f'<p><img src="{main_image["url"]}" alt="{main_image["alt"]}" title="{app_info}" class="img-fluid" /></p>'
            html_parts.append(img_tag)
        
        # 본문 내용 처리
        current_heading = None
        for i, para in enumerate(paragraphs):
            # 단락 길이가 너무 짧으면 건너뛰기
            if len(para.strip()) < 20:
                continue
                
            # 10번째 단락마다 랜덤하게 이미지 삽입
            if i > 0 and i % 10 == 0 and len(images) > 1:
                img_index = (i // 10) % (len(images) - 1) + 1
                if img_index < len(images):
                    img = images[img_index]
                    img_tag = f'<p><img src="{img["url"]}" alt="{img["alt"]}" title="{app_info}" class="img-fluid" /></p>'
                    html_parts.append(img_tag)
            
            # 대문자나 숫자로 시작하고 짧은 단락은 제목으로 처리
            if (para[0].isupper() or para[0].isdigit()) and len(para) < 60 and "." not in para:
                current_heading = para
                html_parts.append(f"<h3>{para}</h3>")
            else:
                # 앱 정보를 강조 표시
                if app_info in para:
                    para = para.replace(app_info, f"<strong>{app_info}</strong>")
                
                html_parts.append(f"<p>{para}</p>")
                
            # 단락 끝에 랜덤하게 강조 문구 추가
            if i > 0 and i % 15 == 0:
                emphasis = [
                    f"<p><em>{app_info}의 이 기능은 정말 유용합니다!</em></p>",
                    f"<p><strong>특히 주목할 점은 {app_info}의 사용 편의성입니다.</strong></p>",
                    f"<p><mark>이 부분은 {app_info}의 핵심 기능입니다.</mark></p>"
                ]
                html_parts.append(random.choice(emphasis))
        
        # 맺음말 추가
        outro = random.choice(self.outro_phrases).format(app_info)
        html_parts.append(f"<p>{outro}</p>")
        
        # 출처 표시 (옵션)
        html_parts.append(f'<p><small>참고: <a href="{source_url}" target="_blank" rel="nofollow">{source_url}</a></small></p>')
        
        # 최종 HTML 컨텐츠 생성
        html_content = "\n".join(html_parts)
        
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