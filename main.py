#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from dotenv import load_dotenv
from scraper import WebScraper
from content_processor import ContentProcessor
from blogger import BloggerAPI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autoblog.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("자동블로그")

def main():
    """메인 프로그램 실행 함수"""
    load_dotenv()  # .env 파일에서 환경변수 로드
    
    try:
        # 사용자 입력 받기
        print("=" * 50)
        print("자동 블로그 포스팅 프로그램")
        print("=" * 50)
        
        url = input("스크랩할 URL을 입력하세요: ")
        app_info = input("앱 정보를 입력하세요 (앱 이름, 버전 등): ")
        category = input("블로그 카테고리를 입력하세요: ")
        
        # 웹 스크래핑
        logger.info(f"스크래핑 시작: {url}")
        scraper = WebScraper()
        content, images = scraper.scrape(url)
        
        if not content:
            logger.error("컨텐츠를 스크랩하지 못했습니다.")
            return
        
        # 컨텐츠 처리
        processor = ContentProcessor()
        title, processed_content = processor.process(content, images, app_info)
        
        # 사용자 확인
        print("\n" + "=" * 50)
        print(f"제목: {title}")
        print("-" * 50)
        print(f"내용 미리보기: {processed_content[:150]}...")
        print("-" * 50)
        confirm = input("이대로 블로그에 포스팅하시겠습니까? (y/n): ")
        
        if confirm.lower() != 'y':
            logger.info("사용자가 포스팅을 취소했습니다.")
            return
        
        # 블로깅
        blogger = BloggerAPI()
        post_url = blogger.create_post(title, processed_content, category)
        
        if post_url:
            logger.info(f"포스팅 성공: {post_url}")
            print(f"포스팅이 성공적으로 완료되었습니다: {post_url}")
        else:
            logger.error("포스팅 실패")
            print("포스팅 중 오류가 발생했습니다.")
            
    except Exception as e:
        logger.exception("프로그램 실행 중 오류 발생")
        print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main() 