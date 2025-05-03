#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import requests
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("자동블로그.scraper")

class WebScraper:
    """웹 페이지 스크래핑을 담당하는 클래스"""
    
    def __init__(self):
        """WebScraper 초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"임시 디렉토리 생성됨: {self.temp_dir}")
    
    def scrape(self, url):
        """
        URL에서 컨텐츠와 이미지를 스크랩
        
        Args:
            url (str): 스크랩할 웹 페이지 URL
            
        Returns:
            tuple: (컨텐츠 딕셔너리, 이미지 딕셔너리 리스트)
        """
        try:
            logger.info(f"페이지 요청: {url}")
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 제목 추출
            title = self._extract_title(soup)
            
            # 본문 추출
            main_content = self._extract_main_content(soup)
            
            # 이미지 추출 및 다운로드
            images = self._extract_images(soup, url)
            
            content = {
                'title': title,
                'url': url,
                'main_content': main_content,
            }
            
            return content, images
            
        except Exception as e:
            logger.exception(f"스크래핑 중 오류 발생: {str(e)}")
            return None, []
    
    def _extract_title(self, soup):
        """페이지에서 제목 추출"""
        # 일반적인 제목 추출 시도
        title = None
        
        # 메타 태그에서 제목 찾기
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title.get('content')
        
        # h1 태그에서 제목 찾기
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
        
        # 기본 title 태그에서 제목 찾기
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # 제목이 없으면 기본값 사용
        if not title:
            title = "스크랩 컨텐츠"
            
        return title
        
    def _extract_main_content(self, soup):
        """페이지에서 주요 컨텐츠 추출"""
        # 컨텐츠가 있을 가능성이 높은 요소들
        content_elements = [
            soup.find('article'),
            soup.find('div', class_=re.compile(r'content|article|post|entry')),
            soup.find('div', id=re.compile(r'content|article|post|entry')),
            soup.find('main'),
        ]
        
        # 첫 번째로 발견된 유효한 요소 사용
        content = None
        for element in content_elements:
            if element:
                content = element
                break
        
        # 유효한 요소를 찾지 못했으면 body 전체 사용
        if not content:
            content = soup.find('body')
        
        if content:
            # 불필요한 요소 제거
            for tag in content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # 텍스트 정규화
            paragraphs = []
            for p in content.find_all(['p', 'h2', 'h3', 'h4', 'li']):
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # 짧은 텍스트 필터링
                    paragraphs.append(text)
            
            return "\n\n".join(paragraphs)
        
        return ""
        
    def _extract_images(self, soup, base_url):
        """페이지에서 이미지 추출 및 다운로드"""
        images = []
        
        # 이미지 태그 찾기
        img_tags = soup.find_all('img', src=True)
        logger.info(f"발견된 이미지 수: {len(img_tags)}")
        
        for i, img in enumerate(img_tags):
            try:
                # 상대 URL을 절대 URL로 변환
                img_url = img['src']
                if not img_url.startswith(('http://', 'https://', 'data:')):
                    img_url = urljoin(base_url, img_url)
                
                # 데이터 URL 무시
                if img_url.startswith('data:'):
                    continue
                
                # 작은 이미지나 아이콘 필터링 (src에 icon이 포함된 경우)
                if 'icon' in img_url.lower() or 'logo' in img_url.lower():
                    continue
                
                # 이미지 너비/높이 확인 (작은 이미지 필터링)
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    if int(width) < 200 or int(height) < 200:
                        continue
                
                # 이미지 다운로드
                img_filename = f"image_{i}_{os.path.basename(urlparse(img_url).path)}"
                img_path = os.path.join(self.temp_dir, img_filename)
                
                response = self.session.get(img_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"이미지 다운로드 완료: {img_url} -> {img_path}")
                
                # 원본 alt 텍스트 가져오기
                alt_text = img.get('alt', '').strip() or f"이미지 {i+1}"
                
                images.append({
                    'url': img_url,
                    'path': img_path,
                    'alt': alt_text
                })
                
                # 최대 5개 이미지로 제한
                if len(images) >= 5:
                    break
                    
            except Exception as e:
                logger.warning(f"이미지 다운로드 실패: {img_url} - {str(e)}")
        
        return images 