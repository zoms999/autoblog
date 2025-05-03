#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session  # Flask-Session 추가
from dotenv import load_dotenv
from scraper import WebScraper
from content_processor import ContentProcessor
from blogger import BloggerAPI
from ai_rewriter import AIRewriter

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

# 세션 설정 강화
app.config['SESSION_TYPE'] = 'filesystem'  # 파일시스템 기반 세션 저장
app.config['SESSION_PERMANENT'] = False  # 브라우저 종료 시 세션 만료
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 세션 유효 시간 30분
app.config['SESSION_USE_SIGNER'] = True  # 세션 쿠키 서명
app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경에서는 False (HTTPS 요구 여부)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript에서 세션 쿠키 접근 방지
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # 세션 파일 저장 경로

# Flask-Session 초기화
Session(app)

# 임시 데이터 저장을 위한 전역 변수
# 실제 프로덕션에서는 데이터베이스 사용을 권장
scraped_data = {}

# AI 재작성 기능 초기화
ai_rewriter = AIRewriter()

@app.route('/')
def index():
    """메인 페이지"""
    # AI 재작성 기능의 가용성 전달
    is_ai_available = ai_rewriter.is_rewriting_available()
    return render_template('index.html', is_ai_available=is_ai_available)

@app.route('/scrape', methods=['POST'])
def scrape():
    """웹 스크래핑 API"""
    try:
        # 세션 초기화 (이전 데이터 완전 제거)
        if 'scraped_data' in session:
            del session['scraped_data']
            
        # 요청 데이터 파싱
        url = request.form.get('url', '').strip()
        app_info = request.form.get('app_info', '').strip()
        category = request.form.get('category', '').strip()
        referrer = request.form.get('referrer', '').strip()
        invite_code = request.form.get('invite_code', '').strip()
        
        # URL 검증
        if not url or not url.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'message': '유효한 URL을 입력해주세요 (http:// 또는 https:// 포함).'})
            
        if not app_info:
            return jsonify({'success': False, 'message': '앱 정보는 필수 입력 항목입니다.'})
            
        # 원본 URL 저장 (반드시 보존)
        original_url = url
        logger.info(f"스크래핑 시작 - 사용자 입력 URL: {original_url}")
        
        # 스크래핑 실행
        scraper = WebScraper()
        content, images = scraper.scrape(original_url)
        
        if not content:
            return jsonify({'success': False, 'message': '컨텐츠를 스크랩하지 못했습니다.'})
        
        # 컨텐츠 처리 전 URL 다시 확인
        if content.get('url') != original_url:
            logger.warning(f"URL 불일치 감지! 사용자 입력: {original_url}, 스크래퍼 반환: {content.get('url')}")
            # URL 불일치 시 사용자가 입력한 원본 URL 강제 사용
            content['url'] = original_url
            logger.info(f"URL 강제 복원: {original_url}")
        
        # 컨텐츠 처리
        processor = ContentProcessor()
        title, processed_content = processor.process(content, images, app_info)
        
        # 디버깅용 로그
        logger.info(f"처리된 컨텐츠 - 제목: {title}, URL: {original_url}")
        
        # 세션에 데이터 저장
        session_data = {
            'url': original_url,  # 사용자 입력 원본 URL 저장
            'app_info': app_info,
            'category': category,
            'referrer': referrer,
            'invite_code': invite_code,
            'title': title,
            'content': processed_content,
            'original_content': processed_content,  # 원본 콘텐츠 저장 (후에 비교용)
            'preview': processed_content[:300] + ('...' if len(processed_content) > 300 else ''),
            'is_rewritten': False  # 재작성 여부 플래그
        }
        
        # 세션에 저장 (확실하게 적용되도록 직접 할당)
        session['scraped_data'] = json.dumps(session_data)
        session.modified = True  # 세션 변경 명시적 표시
        
        # 세션이 제대로 저장되었는지 확인
        logger.info(f"세션에 저장된 URL: {json.loads(session['scraped_data']).get('url')}")
        
        return jsonify({
            'success': True, 
            'message': '스크래핑이 완료되었습니다.',
            'data': {
                'title': title,
                'url': original_url,  # 원본 URL 전달
                'preview': processed_content[:300] + ('...' if len(processed_content) > 300 else ''),
                'is_ai_available': ai_rewriter.is_rewriting_available()
            }
        })
        
    except Exception as e:
        logger.exception(f"스크래핑 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@app.route('/preview')
def preview():
    """스크랩 결과 미리보기 페이지"""
    if 'scraped_data' not in session:
        logger.error("세션에 'scraped_data'가 없음 - 미리보기 접근 불가")
        return render_template('error.html', message='스크랩된 데이터가 없습니다. 다시 스크랩해주세요.')
    
    try:
        # 세션 데이터 로드
        scraped_data = json.loads(session['scraped_data'])
        
        # URL 확인 및 로깅 (디버깅용)
        session_url = scraped_data.get('url', '없음')
        logger.info(f"미리보기 접근 - 세션 URL: {session_url}")
        
        # 세션 데이터 검증
        if not session_url or not scraped_data.get('title') or not scraped_data.get('content'):
            logger.error(f"세션 데이터 불완전: URL={session_url}, 제목={scraped_data.get('title', '없음')}")
            # 세션 데이터 초기화
            del session['scraped_data']
            session.modified = True
            return render_template('error.html', message='세션 데이터가 불완전합니다. 다시 스크랩해주세요.')
        
        is_ai_available = ai_rewriter.is_rewriting_available()
        return render_template('preview.html', data=scraped_data, is_ai_available=is_ai_available)
    except Exception as e:
        logger.exception(f"미리보기 렌더링 중 오류: {str(e)}")
        # 세션 데이터 초기화
        if 'scraped_data' in session:
            del session['scraped_data']
            session.modified = True
        return render_template('error.html', message='세션 데이터를 읽어올 수 없습니다. 다시 스크랩해주세요.')

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

@app.route('/rewrite', methods=['POST'])
def rewrite_content():
    """AI를 사용한 컨텐츠 재작성 API"""
    if 'scraped_data' not in session:
        return jsonify({'success': False, 'message': '스크랩된 데이터가 없습니다. 다시 스크랩해주세요.'})
    
    try:
        # 세션에서 데이터 가져오기
        scraped_data = json.loads(session['scraped_data'])
        
        # 재작성 목표 설정
        goal = request.form.get('goal', "자연스러운 문장과 표현으로 저작권에 문제없게 재작성")
        
        # 제목과 원본 내용
        title = scraped_data['title']
        content = scraped_data.get('original_content', scraped_data['content'])
        
        # 추천인과 초대코드 정보
        referrer = scraped_data.get('referrer', '')
        invite_code = scraped_data.get('invite_code', '')
        
        # AI 재작성 요청
        logger.info(f"컨텐츠 재작성 시작: {title}")
        success, rewritten_text = ai_rewriter.rewrite_content(
            title, 
            content, 
            goal,
            referrer=referrer, 
            invite_code=invite_code
        )
        
        if success:
            # 재작성 성공: 세션 데이터 업데이트
            scraped_data['content'] = rewritten_text
            scraped_data['is_rewritten'] = True
            session['scraped_data'] = json.dumps(scraped_data)
            
            logger.info("컨텐츠 재작성 완료")
            return jsonify({
                'success': True,
                'message': '컨텐츠가 성공적으로 재작성되었습니다.',
                'preview': rewritten_text[:300] + ('...' if len(rewritten_text) > 300 else '')
            })
        else:
            # 재작성 실패
            logger.error(f"컨텐츠 재작성 실패: {rewritten_text}")
            return jsonify({'success': False, 'message': rewritten_text})
            
    except Exception as e:
        logger.exception(f"컨텐츠 재작성 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@app.route('/restore', methods=['POST'])
def restore_original():
    """원본 컨텐츠로 복원 API"""
    if 'scraped_data' not in session:
        return jsonify({'success': False, 'message': '복원할 데이터가 없습니다.'})
    
    try:
        # 세션에서 데이터 가져오기
        scraped_data = json.loads(session['scraped_data'])
        
        # 원본 컨텐츠가 있는지 확인
        if 'original_content' not in scraped_data:
            return jsonify({'success': False, 'message': '원본 컨텐츠를 찾을 수 없습니다.'})
        
        # 원본 컨텐츠로 복원
        scraped_data['content'] = scraped_data['original_content']
        scraped_data['is_rewritten'] = False
        session['scraped_data'] = json.dumps(scraped_data)
        
        logger.info("원본 컨텐츠로 복원 완료")
        return jsonify({
            'success': True,
            'message': '원본 컨텐츠로 복원되었습니다.',
            'preview': scraped_data['original_content'][:300] + ('...' if len(scraped_data['original_content']) > 300 else '')
        })
        
    except Exception as e:
        logger.exception(f"원본 복원 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@app.route('/edit', methods=['POST'])
def edit_content():
    """콘텐츠 직접 편집 API"""
    if 'scraped_data' not in session:
        return jsonify({'success': False, 'message': '편집할 데이터가 없습니다. 다시 스크랩해주세요.'})
    
    try:
        # 세션에서 데이터 가져오기
        scraped_data = json.loads(session['scraped_data'])
        
        # 편집된 제목과 내용 가져오기
        edited_title = request.form.get('title', '').strip()
        edited_content = request.form.get('content', '').strip()
        
        # 데이터 검증
        if not edited_title or not edited_content:
            return jsonify({'success': False, 'message': '제목과 내용은 필수 입력 항목입니다.'})
        
        # 변경 사항 로깅
        logger.info(f"콘텐츠 수동 편집: {scraped_data.get('title')} -> {edited_title}")
        
        # 세션 데이터 업데이트
        scraped_data['title'] = edited_title
        scraped_data['content'] = edited_content
        scraped_data['is_edited'] = True  # 편집 여부 플래그
        
        # 세션에 저장
        session['scraped_data'] = json.dumps(scraped_data)
        session.modified = True
        
        logger.info("콘텐츠 수동 편집 완료")
        return jsonify({
            'success': True,
            'message': '콘텐츠가 성공적으로 수정되었습니다.',
            'title': edited_title,
            'preview': edited_content[:300] + ('...' if len(edited_content) > 300 else '')
        })
        
    except Exception as e:
        logger.exception(f"콘텐츠 편집 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

if __name__ == '__main__':
    # 템플릿 폴더가 없으면 생성
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # 정적 파일 폴더가 없으면 생성
    if not os.path.exists('static'):
        os.makedirs('static')
        
    # 세션 저장소 폴더가 없으면 생성
    session_dir = os.path.join(os.getcwd(), 'flask_session')
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
        logger.info(f"세션 저장소 디렉토리 생성: {session_dir}")
        
    # 개발 모드로 실행 (실제 운영 환경에서는 production 모드로 변경 필요)
    app.run(debug=True, host='0.0.0.0', port=5000) 