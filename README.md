Soldesk 그래픽 기반의 실시간 AI 서비스를 활용한 Cross-flatform 개발자 양성과정 6회차 최종 프로젝트 4조의 프로젝트입니다.

 비디오를 이용한 정보 전달에 도움을 주기 위해 기획되었으며 Spring과 Django 두 서버를 이용해 구현하였습니다
이는 그 중 Spring에 해당하는 서버의 코드입니다.

주요 기능 
1. 영상에서 자막(텍스트) 추출
2. 태그 추천
3. 요약 텍스트 생성
4. 타임라인 생성
5. 영상 정보 레이아웃 작성
6. 문의 게시판
7. 로그인 관련 기능


사용전 
- GoogleCloud-api 사용을 위해 서비스 계정을 생성하고 활성화 해야 합니다.
리소스의 경로를 수정해야 합니다.


주의 
- 저작권, 용량의 문제로 인해 fine-tuning을 마친 모델은 제공할 수 없습니다. 따라서 현재는 자체적으로 fine-tuning 된 모델을 사용하는 버전이 아니라 pretrained된 모델을 사용하는 상태로 되어있습니다. 조정된 모델이 있다면 모델을 지정하는 부분을 주석화하고, 주석화 되어있는 부분을 활성화 해야합니다.
- 모델을 서버에 미리 로딩해두는 버전의 코드가 아닙니다.(리소스 이슈) 리소스가 충분하다면 주석화되어있는 모델을 미리 로딩해두는 부분을 활성화해야 합니다.


모델 출처 
- https://github.com/seujung/KoBART-summarization

데이터 출처
- https://www.aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=data&dataSetSn=591
