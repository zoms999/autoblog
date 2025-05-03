#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# 로깅 설정
logger = logging.getLogger("자동블로그.ai_rewriter")

class AIRewriter:
    """
    Google Gemini AI를 사용하여 텍스트를 재작성하는 클래스
    """
    
    def __init__(self):
        """AIRewriter 초기화"""
        # 환경 변수에서 Google AI API 키 로드
        self.api_key = os.getenv('GOOGLE_AI_API_KEY')
        
        if not self.api_key:
            logger.warning("Google AI API 키가 설정되지 않았습니다. 재작성 기능이 비활성화됩니다.")
            self.is_available = False
        else:
            # Google Gemini API 초기화
            genai.configure(api_key=self.api_key)
            self.is_available = True
            logger.info("Google AI 재작성 기능이 활성화되었습니다.")
    
    def rewrite_content(self, title, content, goal="자연스러운 문장과 표현으로 저작권에 문제없게 재작성", referrer="", invite_code=""):
        """
        주어진 텍스트 콘텐츠를 재작성
        
        Args:
            title (str): 콘텐츠 제목
            content (str): 재작성할 HTML 콘텐츠
            goal (str): 재작성 목표 및 스타일 (기본값: 자연스러운 문장과 표현으로 저작권에 문제없게 재작성)
            referrer (str): 추천인 정보
            invite_code (str): 초대코드
            
        Returns:
            tuple: (성공 여부, 재작성된 텍스트 또는 오류 메시지)
        """
        if not self.is_available:
            return False, "Google AI API 키가 설정되지 않아 재작성 기능을 사용할 수 없습니다."
        
        try:
            # 추천인과 초대코드 관련 지시사항 설정
            referrer_instructions = ""
            if referrer or invite_code:
                referrer_instructions = f"""
7. 다음 정보를 본문 중간이나 마지막에 자연스럽게 포함시켜주세요:
   - 추천인: {referrer if referrer else "(없음)"}
   - 초대코드: {invite_code if invite_code else "(없음)"}
   
   만약 원본 글에 이미 추천인이나 초대코드 정보가 있다면, 위의 정보로 교체해주세요.
   원본 글에 추천인이나 초대코드 정보가 없다면, 적절한 위치에 자연스럽게 추가해주세요.
   예: "이 서비스는 추천인 {referrer}의 초대코드 {invite_code}를 통해 특별 혜택을 받을 수 있습니다."
"""
            else:
                referrer_instructions = """
7. 글 맥락에 맞게 추천인 시스템이나 초대코드에 대한 언급을 자연스럽게 추가해주세요.
   예: "추천인 코드를 통해 가입하면 추가 혜택을 받을 수 있습니다." 또는
   "친구 초대코드를 사용하면 첫 구매 시 할인 혜택이 있습니다."
"""
            
            # 프롬프트 작성
            prompt = f"""
당신은 전문적인 콘텐츠 작가입니다. 다음 블로그 포스트의 내용을 재작성해주세요.
재작성 목표: {goal}

제목: {title}

원본 콘텐츠:
{content}

재작성 시 다음 지침을 따라주세요:
1. HTML 태그는 그대로 유지하고 내용만 변경해주세요.
2. 원본의 주요 요점과 구조는 유지하면서 문장과 표현을 개선해주세요.
3. 더 자연스러운 한국어 표현으로 바꾸고, 어휘를 다양화해주세요.
4. 전문성과 가독성을 유지하면서 더 매력적인 글로 만들어주세요.
5. 저작권 문제를 피하기 위해 원본과 충분히 다르게 표현해주세요.
6. 이미지나 링크 태그의 URL은 변경하지 마세요.
{referrer_instructions}

재작성된 콘텐츠를 HTML 형식으로 제공해주세요.
"""

            # Gemini 모델 설정
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # 응답 생성
            response = model.generate_content(prompt)
            
            if not response.text:
                return False, "AI에서 응답을 받지 못했습니다."
            
            return True, response.text
            
        except Exception as e:
            logger.exception(f"텍스트 재작성 중 오류 발생: {str(e)}")
            return False, f"재작성 중 오류가 발생했습니다: {str(e)}"
    
    def is_rewriting_available(self):
        """
        재작성 기능의 가용성 확인
        
        Returns:
            bool: 재작성 기능 사용 가능 여부
        """
        return self.is_available 