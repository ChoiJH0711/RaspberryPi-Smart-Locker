# Raspberry Pi Smart Locker

웹에서 두 락커를 배정하고 잠금·해제·반납하는 라즈베리파이 스마트 락커 시스템입니다.

- 개인 프로젝트 / 최종현
- Python, Flask, HTML, CSS, MySQL
- Flask-SQLAlchemy, PyMySQL, Flask-WTF, python-dotenv, gpiozero
- Raspberry Pi, 서보모터 2개, RGB LED 2개

## 주요 기능
- 회원가입, 비밀번호 해시 저장, 로그인·로그아웃과 세션 관리
- 본인에게 배정된 락커만 제어, 사용자당 락커 1개 배정 제한
- 1·2번 락커 배정, 잠금·해제 및 반납
- 서보모터 각도 제어, 잠금은 빨강·해제는 초록 LED 표시
- 사용자·락커 상태·작동 이력 데이터베이스 저장
- 서버 재시작 시 DB 상태에 따른 하드웨어 상태 복원
- CSRF 보호와 환경변수를 통한 설정 분리
- GPIO_ENABLED=false 설정을 통한 하드웨어 호출 생략 모드

## 구성
- app.py: 웹 라우트, 인증, DB 모델과 락커 상태 처리
- hardware.py: GPIO, 서보모터 및 LED 제어
- templates/: 로그인·회원가입 및 락커 관리 화면
- static/style.css: 웹 화면 스타일
- schema.sql: 개인정보·접속 비밀번호 없는 MySQL 스키마
- .env.example: 설정 예시

## 실행
1. MySQL에서 schema.sql을 실행하고 별도 애플리케이션 계정을 준비합니다.
2. .env.example을 .env로 복사하고 DB 접속 정보와 임의의 SECRET_KEY를 설정합니다.
3. 라즈베리파이에서 다음 명령을 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

같은 네트워크의 브라우저에서 http://<라즈베리파이주소>:5000 에 접속합니다.
GPIO 없이 확인할 경우 .env에서 GPIO_ENABLED=false로 설정합니다.
이 경우에도 MySQL 연결과 스키마가 필요합니다.

## GPIO 기본 배치 (BCM)
| 락커 | 빨강 LED | 초록 LED | 파랑 LED | 서보 |
|---|---|---|---|---|
| 1 | 17 | 27 | 22 | 12 |
| 2 | 23 | 24 | 25 | 13 |

잠금 90도, 해제 0도가 기본값이며 실제 기구와 배선에 맞게 환경변수로 조정합니다.

## 검증 범위
소스와 설정 구성을 확인했습니다. 실제 MySQL 연동과 GPIO 장치 동작 검증은 이 업로드 과정에서 수행하지 않았습니다.
