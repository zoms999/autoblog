#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("자동블로그.blogger")

class BloggerAPI:
    """구글 블로그 API를 이용한 자동 포스팅 클래스"""
    
    # 필요한 API 범위 설정
    SCOPES = ['https://www.googleapis.com/auth/blogger']
    
    def __init__(self):
        """BloggerAPI 초기화"""
        self.credentials = None
        self.service = None
        self.blog_id = os.getenv('BLOG_ID')
        self.token_file = 'token.json'
        
        # 환경 변수에서 클라이언트 시크릿 파일 경로 가져오기
        client_secret_env = os.getenv('CLIENT_SECRET_FILE')
        self.client_secret_file = client_secret_env if client_secret_env else 'client_secret.json'
        
        # 디버그 정보 출력
        logger.info(f"클라이언트 시크릿 파일 경로: {self.client_secret_file}")
        
        # 인증 및 서비스 초기화
        self._authenticate()
    
    def _authenticate(self):
        """Google API 인증"""
        try:
            # 클라이언트 시크릿 파일 확인
            if not os.path.exists(self.client_secret_file):
                logger.error(f"클라이언트 시크릿 파일을 찾을 수 없습니다: {self.client_secret_file}")
                print(f"클라이언트 시크릿 파일이 필요합니다. 구글 클라우드 콘솔에서 다운로드한 JSON 파일을 {self.client_secret_file}로 저장해주세요.")
                return
                
            # 기존 토큰이 있는지 확인
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_info(
                    json.load(open(self.token_file))
                )
            
            # 토큰이 없거나 만료된 경우
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # 새로운 인증 플로우 실행
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_file, self.SCOPES)
                    
                    # Google Cloud Console에 설정된 리디렉션 URI에 맞게 설정
                    print("\n구글 인증을 시작합니다. 브라우저가 열리면 Google 계정으로 로그인하여 권한을 허용해주세요.")
                    
                    # 리디렉션 URI를 정확히 지정 (Google Cloud Console에 설정된 것과 일치해야 함)
                    redirect_uri = 'http://localhost:8080/oauth/callback'
                    
                    try:
                        self.credentials = flow.run_local_server(
                            port=8080,
                            redirect_uri_trailing_slash=False,
                            authorization_prompt_message="브라우저에서 구글 로그인을 완료한 후 이 창으로 돌아오세요."
                        )
                        print("인증이 성공적으로 완료되었습니다!")
                    except Exception as auth_error:
                        logger.error(f"인증 중 오류 발생: {str(auth_error)}")
                        print(f"인증 중 오류가 발생했습니다: {str(auth_error)}")
                        
                        if "redirect_uri_mismatch" in str(auth_error):
                            print("\n=== OAuth 리디렉션 URI 오류 ===")
                            print("현재 사용 중인 리디렉션 URI가 Google Cloud Console에 등록된 것과 일치하지 않습니다.")
                            print(f"사용 중인 URI: {redirect_uri}")
                            print("\nGoogle Cloud Console에서 다음 URI 중 하나 이상이 등록되어 있는지 확인하세요:")
                            print("1. http://localhost:8080/oauth/callback")
                            print("2. http://localhost:8080")
                            print("3. http://localhost")
                            return
                
                # 토큰 저장
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # 블로거 API 서비스 생성
            self.service = build('blogger', 'v3', credentials=self.credentials)
            logger.info("Google Blogger API 인증 성공")
            
            # 블로그 ID 확인
            if not self.blog_id:
                self._get_blog_id()
                
        except Exception as e:
            logger.exception(f"Google API 인증 중 오류 발생: {str(e)}")
            print(f"Google API 인증 중 오류가 발생했습니다: {str(e)}")
            
            if "redirect_uri_mismatch" in str(e):
                print("\n=== OAuth 리디렉션 URI 오류 ===")
                print("Google Cloud Console에서 다음 URI 중 하나 이상이 등록되어 있는지 확인하세요:")
                print("1. http://localhost:8080/oauth/callback")
                print("2. http://localhost:8080")
                print("3. http://localhost")
    
    def _get_blog_id(self):
        """사용자의 블로그 ID 조회"""
        try:
            blogs = self.service.blogs().listByUser(userId='self').execute()
            if 'items' in blogs and blogs['items']:
                # 첫 번째 블로그 선택
                self.blog_id = blogs['items'][0]['id']
                logger.info(f"블로그 ID 조회 성공: {self.blog_id}")
                print(f"블로그 '{blogs['items'][0]['name']}'가 선택되었습니다.")
                
                # 환경 변수 설정 안내
                print(f"다음 설정을 .env 파일에 추가하세요: BLOG_ID={self.blog_id}")
            else:
                logger.error("사용자 블로그를 찾을 수 없습니다.")
                print("연결된 구글 계정에 블로그가 없습니다. 블로거에서 블로그를 생성한 후 다시 시도해주세요.")
        except Exception as e:
            logger.exception(f"블로그 ID 조회 중 오류 발생: {str(e)}")
            print(f"블로그 정보 조회 중 오류가 발생했습니다: {str(e)}")
    
    def create_post(self, title, content, labels=None):
        """
        블로그에 새 포스트 생성
        
        Args:
            title (str): 포스트 제목
            content (str): 포스트 내용 (HTML)
            labels (str or list): 포스트 라벨(카테고리)
            
        Returns:
            str: 생성된 포스트 URL (성공 시) 또는 None (실패 시)
        """
        if not self.service or not self.blog_id:
            logger.error("API 서비스가 초기화되지 않았거나 블로그 ID가 없습니다.")
            return None
        
        try:
            # 라벨 처리
            if labels:
                if isinstance(labels, str):
                    labels = [label.strip() for label in labels.split(',')]
            else:
                labels = []
            
            # 포스트 생성
            post = {
                'kind': 'blogger#post',
                'title': title,
                'content': content,
                'labels': labels,
            }
            
            logger.info(f"블로그 포스트 생성 시도: {title}")
            result = self.service.posts().insert(
                blogId=self.blog_id, 
                body=post,
                isDraft=False,  # 바로 공개
                fetchImages=True  # 이미지 자동 업로드 활성화
            ).execute()
            
            logger.info(f"블로그 포스트 생성 성공: {result['title']} (ID: {result['id']})")
            return result.get('url')
            
        except HttpError as error:
            logger.exception(f"API 오류 발생: {error.resp.status} {error.content}")
            return None
        except Exception as e:
            logger.exception(f"포스트 생성 중 오류 발생: {str(e)}")
            return None
            
    def get_posts(self, max_results=10):
        """최근 포스트 목록 조회"""
        if not self.service or not self.blog_id:
            logger.error("API 서비스가 초기화되지 않았거나 블로그 ID가 없습니다.")
            return []
            
        try:
            posts = self.service.posts().list(
                blogId=self.blog_id,
                maxResults=max_results,
                status='live'
            ).execute()
            
            return posts.get('items', [])
        except Exception as e:
            logger.exception(f"포스트 목록 조회 중 오류 발생: {str(e)}")
            return [] 