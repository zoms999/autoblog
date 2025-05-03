#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from scraper import WebScraper
from content_processor import ContentProcessor
from blogger import BloggerAPI

# .env 파일 로드
load_dotenv()

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

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')  # 세션 암호화 키

# 임시 데이터 저장을 위한 전역 변수
# 실제 프로덕션에서는 데이터베이스 사용을 권장
scraped_data = {}

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """웹 스크래핑 API"""
    try:
        # 요청 데이터 파싱
        url = request.form.get('url')
        app_info = request.form.get('app_info')
        category = request.form.get('category')
        
        if not url or not app_info:
            return jsonify({'success': False, 'message': 'URL과 앱 정보는 필수 입력 항목입니다.'})
            
        # 스크래핑 시작
        logger.info(f"스크래핑 시작: {url}")
        scraper = WebScraper()
        content, images = scraper.scrape(url)
        
        if not content:
            return jsonify({'success': False, 'message': '컨텐츠를 스크랩하지 못했습니다.'})
        
        # 컨텐츠 처리
        processor = ContentProcessor()
        title, processed_content = processor.process(content, images, app_info)
        
        # 세션에 데이터 저장
        session_data = {
            'url': url,
            'app_info': app_info,
            'category': category,
            'title': title,
            'content': processed_content,
            'preview': processed_content[:300] + ('...' if len(processed_content) > 300 else '')
        }
        
        # 세션에 저장
        session['scraped_data'] = json.dumps(session_data)
        
        return jsonify({
            'success': True, 
            'message': '스크래핑이 완료되었습니다.',
            'data': {
                'title': title,
                'preview': processed_content[:300] + ('...' if len(processed_content) > 300 else '')
            }
        })
        
    except Exception as e:
        logger.exception(f"스크래핑 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@app.route('/preview')
def preview():
    """스크랩 결과 미리보기 페이지"""
    if 'scraped_data' not in session:
        return render_template('error.html', message='스크랩된 데이터가 없습니다. 다시 스크랩해주세요.')
    
    try:
        scraped_data = json.loads(session['scraped_data'])
        return render_template('preview.html', data=scraped_data)
    except:
        return render_template('error.html', message='세션 데이터를 읽어올 수 없습니다.')

@app.route('/post', methods=['POST'])
def post_to_blog():
    """블로그 포스팅 API"""
    if 'scraped_data' not in session:
        return jsonify({'success': False, 'message': '스크랩된 데이터가 없습니다. 다시 스크랩해주세요.'})
    
    try:
        scraped_data = json.loads(session['scraped_data'])
        
        # 블로깅
        blogger = BloggerAPI()
        post_url = blogger.create_post(
            scraped_data['title'], 
            scraped_data['content'], 
            scraped_data['category']
        )
        
        if post_url:
            logger.info(f"포스팅 성공: {post_url}")
            return jsonify({
                'success': True, 
                'message': '포스팅이 성공적으로 완료되었습니다.',
                'post_url': post_url
            })
        else:
            logger.error("포스팅 실패")
            return jsonify({'success': False, 'message': '포스팅 중 오류가 발생했습니다.'})
            
    except Exception as e:
        logger.exception(f"포스팅 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

if __name__ == '__main__':
    # 템플릿 폴더가 없으면 생성
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # 정적 파일 폴더가 없으면 생성
    if not os.path.exists('static'):
        os.makedirs('static')
        
    # 개발 모드로 실행 (실제 운영 환경에서는 production 모드로 변경 필요)
    app.run(debug=True, host='0.0.0.0', port=5000) 