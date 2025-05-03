/**
 * 자동 블로그 포스팅 프로그램 JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // 폼 요소
    const scrapeForm = document.getElementById('scrapeForm');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    // 결과 표시 요소
    const previewCard = document.getElementById('previewCard');
    const previewTitle = document.getElementById('previewTitle');
    const previewContent = document.getElementById('previewContent');
    const postBtn = document.getElementById('postBtn');
    
    // 알림 메시지 요소
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');
    
    /**
     * 스크랩 폼 제출 이벤트 처리
     */
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 로딩 상태 표시
            scrapeBtn.disabled = true;
            loadingSpinner.classList.remove('d-none');
            scrapeBtn.querySelector('span:not(.spinner-border)') 
                ? scrapeBtn.querySelector('span:not(.spinner-border)').textContent = ' 스크래핑 중...'
                : scrapeBtn.appendChild(document.createTextNode(' 스크래핑 중...'));
            
            // 알림 메시지 초기화
            successAlert.classList.add('d-none');
            errorAlert.classList.add('d-none');
            
            // 폼 데이터 수집
            const formData = new FormData(scrapeForm);
            
            // 스크랩 API 호출
            fetch('/scrape', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // 로딩 상태 해제
                scrapeBtn.disabled = false;
                loadingSpinner.classList.add('d-none');
                scrapeBtn.innerHTML = '스크랩 시작';
                
                if (data.success) {
                    // 성공 시 결과 표시
                    successAlert.textContent = data.message;
                    successAlert.classList.remove('d-none');
                    errorAlert.classList.add('d-none');
                    
                    // 미리보기 카드 업데이트
                    previewTitle.textContent = data.data.title;
                    previewContent.innerHTML = data.data.preview;
                    previewCard.classList.remove('d-none');
                    
                    // 스크롤 이동
                    previewCard.scrollIntoView({ behavior: 'smooth' });
                } else {
                    // 실패 시 오류 메시지 표시
                    errorAlert.textContent = data.message;
                    errorAlert.classList.remove('d-none');
                    successAlert.classList.add('d-none');
                    previewCard.classList.add('d-none');
                }
            })
            .catch(error => {
                // 네트워크 오류 등 예외 처리
                console.error('Error:', error);
                scrapeBtn.disabled = false;
                loadingSpinner.classList.add('d-none');
                scrapeBtn.innerHTML = '스크랩 시작';
                
                errorAlert.textContent = '요청 중 오류가 발생했습니다: ' + error.message;
                errorAlert.classList.remove('d-none');
                successAlert.classList.add('d-none');
                previewCard.classList.add('d-none');
            });
        });
    }
    
    /**
     * 포스팅 버튼 이벤트 처리 (인덱스 페이지)
     */
    if (postBtn) {
        postBtn.addEventListener('click', function() {
            // 버튼 상태 변경
            postBtn.disabled = true;
            postBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 포스팅 중...';
            
            // 포스팅 API 호출
            fetch('/post', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 성공 시 메시지 표시
                    successAlert.textContent = data.message;
                    successAlert.classList.remove('d-none');
                    
                    if (data.post_url) {
                        // 게시글 링크 추가
                        successAlert.innerHTML = `${data.message} <a href="${data.post_url}" target="_blank" class="alert-link">게시글 보기</a>`;
                    }
                    
                    errorAlert.classList.add('d-none');
                    postBtn.innerHTML = '포스팅 완료!';
                    postBtn.classList.remove('btn-success');
                    postBtn.classList.add('btn-outline-success');
                } else {
                    // 실패 시 오류 메시지
                    errorAlert.textContent = data.message;
                    errorAlert.classList.remove('d-none');
                    successAlert.classList.add('d-none');
                    postBtn.innerHTML = '다시 시도';
                    postBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                errorAlert.textContent = '요청 중 오류가 발생했습니다: ' + error.message;
                errorAlert.classList.remove('d-none');
                successAlert.classList.add('d-none');
                postBtn.innerHTML = '다시 시도';
                postBtn.disabled = false;
            });
        });
    }
}); 