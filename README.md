# 자동 블로그 포스팅 프로그램

URL과 앱 정보를 입력하여 해당 페이지에서 컨텐츠(사진과 내용)를 스크랩하고, 스크랩한 내용을 적절히 수정하여 구글 블로그에 자동으로 포스팅하는 프로그램입니다.

## 주요 기능

- 웹페이지 컨텐츠 및 이미지 스크랩
- 컨텐츠 자동 처리 및 포맷팅
- 구글 블로그 API를 통한 포스팅 자동화
- Google Gemini AI를 사용한 컨텐츠 재작성 (저작권 문제 방지)
- 직관적인 웹 인터페이스 제공

## 설치 방법

1. 저장소 클론:
```
git clone https://github.com/zoms999/autoblog.git
cd autoblog
```

2. 필요한 패키지 설치:
```
pip install -r requirements.txt
```

3. 환경 변수 설정 (.env 파일 생성):
```
# 플라스크 설정
SECRET_KEY=your_secret_key_here

# Google API 인증 정보
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here

# 블로그 설정
BLOG_ID=your_blog_id_here

# Google AI (Gemini) API 설정
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
```

4. Google API 인증 설정:
- [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
- Blogger API v3와 OAuth 클라이언트 ID 활성화
- OAuth 클라이언트 ID와 시크릿 발급받기
- 발급받은 정보로 client_secret.json 파일 생성

5. Google AI 설정 (선택적):
- [Google AI Studio](https://aistudio.google.com/)에서 API 키 발급
- .env 파일에 API 키 추가

## 사용 방법

1. 웹 애플리케이션 실행:
```
python app.py
```

2. 웹 브라우저에서 접속:
```
http://localhost:5000
```

3. 사용 단계:
   - URL, 앱 정보, 카테고리 입력
   - 스크랩 시작 버튼 클릭
   - 스크랩 결과 미리보기
   - 필요시 AI로 컨텐츠 재작성
   - 블로그에 포스팅

## 구조

- `app.py`: Flask 웹 애플리케이션 메인
- `scraper.py`: 웹 스크래핑 기능
- `content_processor.py`: 컨텐츠 처리
- `blogger.py`: Google Blogger API 연동
- `ai_rewriter.py`: Google Gemini API를 이용한 텍스트 재작성

## 상세 설정 방법

자세한 설정 방법은 [SETUP.md](SETUP.md) 파일을 참조하세요. 