# 자동 블로그 포스팅 프로그램

URL과 앱 정보를 입력하여 해당 페이지에서 컨텐츠(사진과 내용)를 스크랩하고, 스크랩한 내용을 적절히 수정하여 구글 블로그에 자동으로 포스팅하는 프로그램입니다.

## 설치 방법

1. 필요한 패키지 설치:
```
pip install -r requirements.txt
```

2. `.env` 파일 설정:
```
CLIENT_SECRET_FILE=your_client_secret.json
BLOG_ID=your_blog_id
```

## 사용 방법

```
python main.py
```

## 기능

- 웹페이지 컨텐츠 스크랩
- 이미지 다운로드 및 처리
- 컨텐츠 수정 및 포맷팅
- 구글 블로그 API를 통한 포스팅 자동화 