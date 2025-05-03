#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import logging
import requests
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote

logger = logging.getLogger("자동블로그.scraper")

class WebScraper:
    """웹 페이지 스크래핑을 담당하는 클래스"""
    
    def __init__(self):
        """WebScraper 초기화"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"임시 디렉토리 생성됨: {self.temp_dir}")
    
    def _normalize_url(self, url):
        """URL 정규화: 프로토콜 추가, URL 디코딩 등"""
        # URL 디코딩
        url = unquote(url)
        
        # 프로토콜이 없으면 https:// 추가
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # URL 파싱 후 재구성하여 표준화
        parsed = urlparse(url)
        
        # 티스토리 블로그 특화 처리
        if 'tistory.com' in parsed.netloc:
            # 모바일 버전을 피함
            if 'm.' in parsed.netloc:
                parsed = parsed._replace(netloc=parsed.netloc.replace('m.', ''))
            
            # 티스토리 URL에서 불필요한 쿼리 파라미터 제거 (주로 트래킹 파라미터)
            # 원본 쿼리 파라미터
            query_params = {}
            if parsed.query:
                # 기존 쿼리 파라미터 파싱
                from urllib.parse import parse_qsl
                query_params = dict(parse_qsl(parsed.query))
                
                # 필수 파라미터만 유지 (다른 파라미터는 제거)
                essential_params = ['category']  # 필수 쿼리 파라미터 목록
                for param in list(query_params.keys()):
                    if param not in essential_params:
                        del query_params[param]
                
                # 쿼리 재구성
                from urllib.parse import urlencode
                if query_params:
                    parsed = parsed._replace(query=urlencode(query_params))
                else:
                    parsed = parsed._replace(query='')
        
        # URL 재구성
        normalized_url = parsed.geturl()
        
        if url != normalized_url:
            logger.info(f"URL 정규화: {url} -> {normalized_url}")
            
        return normalized_url
    
    def scrape(self, url):
        """
        URL에서 컨텐츠와 이미지를 스크랩
        
        Args:
            url (str): 스크랩할 웹 페이지 URL
            
        Returns:
            tuple: (컨텐츠 딕셔너리, 이미지 딕셔너리 리스트)
        """
        try:
            # 원본 URL 저장 (절대 변경되지 않아야 함)
            original_url = url
            logger.info(f"스크래핑 시작 - 원본 URL (변경 전): {original_url}")
            
            # URL 정규화
            url = self._normalize_url(url)
            
            # 원본 URL 업데이트 (정규화 후 URL)
            original_url = url
            logger.info(f"스크래핑 시작 - 원본 URL (정규화 후): {original_url}")
            
            # 리다이렉션 허용하면서 요청
            response = self.session.get(
                url, 
                headers=self.headers, 
                timeout=30, 
                allow_redirects=True,
                verify=True  # SSL 인증서 확인
            )
            response.raise_for_status()
            
            # 최종 URL과 원본 URL이 다른 경우 로그 기록
            final_url = response.url
            if final_url != original_url:
                logger.warning(f"리다이렉션 발생: {original_url} -> {final_url}")
                # 리다이렉션 URL은 내부적으로만 사용하고, 원본 URL을 유지
            
            # 응답 인코딩 확인
            if response.encoding.lower() == 'iso-8859-1':
                # 한국어 페이지는 보통 UTF-8 또는 EUC-KR 인코딩 사용
                response.encoding = 'utf-8'
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 제목 추출
            title = self._extract_title(soup)
            
            # 도메인 기반 컨텐츠 추출 메서드 선택
            domain = urlparse(original_url).netloc.lower()
            main_content = ""
            
            # 티스토리 블로그 특화 처리
            if 'tistory.com' in domain:
                logger.info(f"티스토리 블로그 감지: {domain}")
                main_content = self._extract_tistory_content(soup, original_url)
            # 네이버 블로그 특화 처리
            elif 'naver.com' in domain:
                logger.info(f"네이버 블로그 감지: {domain}")
                main_content = self._extract_naver_content(soup)
            # 일반 웹사이트 처리
            else:
                logger.info(f"일반 웹사이트 처리: {domain}")
                main_content = self._extract_main_content(soup)
            
            # 이미지 추출 및 다운로드 (실제 URL 사용)
            images = self._extract_images(soup, final_url)
            
            # 컨텐츠 구성 (항상 원본 URL 사용)
            content = {
                'title': title,
                'url': original_url,  # 원본 URL 유지
                'main_content': main_content,
                'domain': domain
            }
            
            logger.info(f"스크래핑 완료: {original_url}, 제목: {title}, 이미지: {len(images)}개")
            return content, images
            
        except Exception as e:
            logger.exception(f"스크래핑 중 오류 발생: {str(e)}")
            return None, []
    
    def _extract_title(self, soup):
        """페이지에서 제목 추출"""
        # 일반적인 제목 추출 시도
        title = None
        
        # 티스토리 블로그 특화 제목 찾기
        tistory_title = soup.find('meta', property='og:title') or soup.find('h1', class_='title')
        if tistory_title:
            if hasattr(tistory_title, 'get') and tistory_title.get('content'):
                title = tistory_title.get('content')
            else:
                title = tistory_title.get_text(strip=True)
        
        # 메타 태그에서 제목 찾기
        if not title:
            meta_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'})
            if meta_title and meta_title.get('content'):
                title = meta_title.get('content')
        
        # h1 태그에서 제목 찾기
        if not title:
            h1_tags = soup.find_all('h1')
            for h1 in h1_tags:
                text = h1.get_text(strip=True)
                if text and len(text) > 5:  # 의미 있는 길이의 텍스트만
                    title = text
                    break
        
        # 기본 title 태그에서 제목 찾기
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # 제목이 없으면 기본값 사용
        if not title:
            title = "스크랩 컨텐츠"
            
        return title
    
    def _extract_tistory_content(self, soup, original_url):
        """티스토리 블로그에서 컨텐츠 추출"""
        # 티스토리 블로그의 주요 컨텐츠 영역 추출
        content_area = None
        
        # 티스토리 블로그의 일반적인 컨텐츠 영역
        possible_selectors = [
            'div.entry-content',           # 일반적인 티스토리 컨텐츠 클래스
            'div.article',                 # 티스토리 아티클 영역
            'div.post-content',            # 포스트 컨텐츠 영역
            'div.contents_style',          # 구 버전 티스토리 컨텐츠 스타일
            'div#content',                 # 컨텐츠 ID
            'div.content',                 # 컨텐츠 클래스
            'div.tt_article_useless_p_margin', # 티스토리 특수 클래스
        ]
        
        # 티스토리 템플릿별 컨텐츠 영역 태그를 순차적으로 확인
        for selector in possible_selectors:
            # 선택자 유형에 따라 검색
            tag, attr_type, attr_value = self._parse_selector(selector)
            elements = soup.select(selector)
            
            if elements:
                content_area = elements[0]
                logger.info(f"티스토리 컨텐츠 영역 찾음: {selector}")
                break
        
        # 일반적인 방법으로도 찾지 못했으면 다른 시도
        if not content_area:
            # 티스토리 특유의 구조에서 본문 추출 시도
            for div in soup.find_all('div'):
                class_attr = div.get('class', [])
                if isinstance(class_attr, list):
                    class_str = ' '.join(class_attr)
                else:
                    class_str = str(class_attr)
                
                if any(term in class_str.lower() for term in ['article', 'post', 'content', 'entry']):
                    content_area = div
                    logger.info(f"티스토리 컨텐츠 영역 찾음 (클래스 매칭): {class_str}")
                    break
        
        # 여전히 찾지 못했다면 기본 방법 사용
        if not content_area:
            logger.warning(f"티스토리 컨텐츠 영역을 찾지 못함: {original_url}")
            return self._extract_main_content(soup)
        
        # 불필요한 요소 제거
        for tag in content_area.find_all(['script', 'style', 'footer', 'aside', 'div', 'a'], class_=lambda c: c and any(skip in str(c).lower() for skip in ['comment', 'sidebar', 'widget', 'banner', 'ad-', 'advertisement'])):
            tag.decompose()
        
        # HTML 내용 반환 (티스토리 블로그는 HTML 구조가 중요함)
        return str(content_area)
    
    def _parse_selector(self, selector):
        """CSS 선택자 파싱"""
        match = re.match(r'([a-z]+)(?:#([a-zA-Z0-9_-]+)|\.([a-zA-Z0-9_-]+))?', selector)
        if match:
            tag = match.group(1)
            id_attr = match.group(2)
            class_attr = match.group(3)
            
            if id_attr:
                return tag, 'id', id_attr
            elif class_attr:
                return tag, 'class', class_attr
            else:
                return tag, None, None
        return 'div', None, None  # 기본값
        
    def _extract_naver_content(self, soup):
        """네이버 블로그에서 컨텐츠 추출"""
        # 네이버 블로그의 주요 컨텐츠 영역 추출
        content_area = None
        
        # 네이버 블로그의 일반적인 컨텐츠 영역
        possible_selectors = [
            'div.se-main-container',  # 스마트 에디터 2.0
            'div.post-content',       # 네이버 포스트 컨텐츠
            'div#postViewArea',       # 구 버전 네이버 블로그
            'div.se_component_wrap'   # 스마트 에디터 컴포넌트
        ]
        
        # 각 선택자 시도
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                content_area = elements[0]
                break
        
        # 일반적인 방법으로도 찾지 못했으면 다른 시도
        if not content_area:
            iframe = soup.find('iframe', id='mainFrame')
            if iframe:
                # 네이버 블로그는 iframe 구조를 사용하는 경우가 있어 스크래핑이 어려울 수 있음
                logger.warning("네이버 블로그의 iframe 구조 감지됨. 전체 컨텐츠를 가져오지 못할 수 있습니다.")
        
        # 여전히 찾지 못했다면 기본 방법 사용
        if not content_area:
            return self._extract_main_content(soup)
        
        # 불필요한 요소 제거
        for tag in content_area.find_all(['script', 'style', 'footer', 'aside']):
            tag.decompose()
        
        # HTML 내용 반환
        return str(content_area)
        
    def _extract_main_content(self, soup):
        """페이지에서 주요 컨텐츠 추출 (일반 웹사이트용)"""
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
            
            # HTML 내용 반환 (더 풍부한 콘텐츠를 위해)
            return str(content)
        
        return ""
        
    def _extract_images(self, soup, base_url):
        """페이지에서 이미지 추출 및 다운로드"""
        images = []
        
        # 이미지 태그 찾기 (더 많은 이미지 태그 패턴 추가)
        img_tags = soup.select('img[src], div.imageblock img, div.se-image img')
        logger.info(f"발견된 이미지 수: {len(img_tags)}")
        
        for i, img in enumerate(img_tags):
            try:
                # 원본 이미지 URL 찾기 시도 (티스토리의 경우 data-origin-url 속성 확인)
                img_url = None
                
                # 티스토리 원본 이미지 URL 찾기
                if img.get('data-origin-url'):
                    img_url = img.get('data-origin-url')
                elif img.get('data-original'):
                    img_url = img.get('data-original')
                else:
                    img_url = img.get('src')
                
                # URL이 없으면 건너뛰기
                if not img_url:
                    continue
                
                # 상대 URL을 절대 URL로 변환
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
                    try:
                        if int(width) < 200 or int(height) < 200:
                            continue
                    except ValueError:
                        # 너비나 높이가 숫자가 아닌 경우 (예: 'auto')
                        pass
                
                # 이미지 다운로드 URL 정리
                img_url = img_url.strip().replace(' ', '%20')
                
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
                logger.warning(f"이미지 다운로드 실패: {img_url if 'img_url' in locals() else '알 수 없음'} - {str(e)}")
        
        return images 