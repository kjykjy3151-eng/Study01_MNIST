# CLAUDE.md — 데스크톱 버전

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

이 문서는 데스크톱(파이썬, Tkinter) 버전만 다룬다. 웹 버전은
`../web_version/CLAUDE.md` 를, 저장소 전체 구조는 `../CLAUDE.md` 를 보라.

## 언어 규칙

이 저장소의 코드와 주석은 **한글로 작성한다.** 독스트링, 인라인 주석, 사용자에게
보이는 문자열(`print`, GUI 라벨, 오류 메시지, `argparse` 도움말), 직접 정의하는
클래스·함수·변수 이름까지 모두 한글을 쓴다. 예: `숫자인식CNN`, `전처리`, `학습_로더`.

프레임워크가 이름을 고정하는 부분만 영어를 유지한다. `nn.Module`의 `forward`,
`__init__` 같은 특수 메서드, 라이브러리 API 인자명(`in_channels`, `batch_size`)이
여기 해당한다. 이런 경우 이름은 그대로 두고 독스트링으로 한글 설명을 붙인다.

## 환경

Python은 시스템 PATH에 없다. 가상환경 두 개를 각각 직접 지정해서 써야 한다.

| 환경 | 위치 | Python | 용도 |
| --- | --- | --- | --- |
| `.venv` | `desktop_version/.venv` | 3.12 | PyTorch 2.14+cpu, torchvision. **이 프로젝트의 기본 환경** |
| `.venv-tf` | 저장소 루트 | 3.13 | TensorFlow 2.21 (별도 실험용, 본 앱은 쓰지 않음) |

`.venv` 가 이 폴더 안에 있는 것은 우연이 아니다. 아래 명령들과
`가상환경으로_재실행()`, 실행 스크립트 세 개가 모두 **자기 파일 옆의 `.venv`** 를
찾기 때문에, 폴더를 통째로 옮겨도 코드를 고칠 필요가 없다. 이 성질을 깨뜨리지 말라.
웹 쪽 개발용 스크립트도 torch 가 필요해 이 환경을 빌려 쓴다.

환경을 분리한 이유는 TensorFlow와 PyTorch가 numpy 버전을 두고 충돌하기 때문이다.
또한 TensorFlow는 Python 3.14용 휠이 없어 3.13이 상한이고, Windows 네이티브에서는
2.11부터 GPU를 지원하지 않는다.

PyTorch DLL 로드에는 Visual C++ 재배포 패키지가 필요하다. 없으면
`c10.dll` 로드 실패(`WinError 126`)가 난다.

## 크로스 플랫폼 규칙

앱은 Windows와 macOS 양쪽에서 동작해야 한다. 교수님이 맥으로 채점할 수 있기 때문이다.
OS에 의존하는 부분은 다음 세 곳뿐이며, 새 코드를 넣을 때도 이 패턴을 따른다.

1. **글꼴** — `app.본문_글꼴` / `app.고정폭_글꼴` 을 쓴다. 글꼴 이름을 직접 적지 않는다.
   맥에 없는 `맑은 고딕`을 지정하면 Tk가 제멋대로 대체하며 창 크기가 틀어진다.
2. **창 아이콘** — `.ico` 는 윈도우 전용이고 맥의 Tk는 읽지 못해 `TclError` 가 난다.
   `창_아이콘_설정()` 이 윈도우면 `iconbitmap(.ico)`, 아니면 `iconphoto(.png)` 를 쓴다.
   `아이콘_만들기.py` 는 `.ico` 와 `.png` 를 함께 만든다.
3. **윈도우 전용 기능** — 작업 표시줄 고정(`작업표시줄_아이디_설정`)은
   `sys.platform != "win32"` 면 즉시 반환한다.

실행 파일은 OS별로 따로 둔다. `.command`(맥), `.bat`(윈도우), `.ps1`(윈도우).

**`.gitattributes` 를 함부로 고치지 않는다.** `.command` 가 CRLF로 체크아웃되면
맥에서 셔뱅이 깨져 `bad interpreter: /bin/bash^M` 으로 실행 자체가 실패한다.
`.bat` 은 cp949로 저장되어 있어 git이 텍스트로 다루면 깨지므로 `-text` 로 묶어 둔다.

맥 분기는 실제 기기 없이도 `sys.platform` 을 `"darwin"` 으로 바꾸고 `app` 을
`importlib.reload()` 하면 검증할 수 있다. 단 **torch 를 먼저 import 한 뒤**
플랫폼을 바꿔야 한다. 그러지 않으면 torch 가 `.so` 파일을 찾다가 실패한다.

## 명령

아래 명령은 모두 **`desktop_version` 폴더 안에서** 실행한다. 저장소 루트에서
실행하려면 경로 앞에 `desktop_version\` 을 붙인다
(예: `desktop_version\.venv\Scripts\python.exe desktop_version\train.py`).

학습 (CPU 기준 5 에포크에 약 24분, 완료 시 `mnist_cnn.pt` 저장):

```bash
.venv\Scripts\python.exe train.py
```

```bash
.venv\Scripts\python.exe train.py --에포크 10 --배치크기 128
```

앱 실행:

```bash
.venv\Scripts\python.exe app.py
```

아이콘 재생성 (`아이콘_만들기.py`의 `표시_숫자`, `배경색`, `강조색` 수정 후):

```bash
.venv\Scripts\python.exe 아이콘_만들기.py
```

자동화된 테스트 스위트는 없다. 변경을 검증할 때는 학습된 가중치를 불러
평가셋 정확도(기준: 99.17%)와 `app.전처리` 경로를 함께 확인한다.

다만 `app.전처리()` 와 모델 구조를 건드렸다면 웹 버전의 대조 시험이 그 변경을
잡아낸다. 저장소 루트에서 `node web_version/테스트/검증.mjs` 를 돌려 보라.
전처리를 고쳤다면 `web_version/테스트/골든_만들기.py` 를, 모델을 고쳐 재학습했다면
`web_version/도구/가중치_내보내기.py` 를 먼저 다시 실행해야 한다.

## 구조

`model.py` → `train.py` / `app.py` 순으로 의존한다. 학습과 추론이 **같은 모델 구조와
같은 정규화 상수를 공유**하는 것이 이 코드베이스의 핵심 제약이다.

- **`model.py`** — `숫자인식CNN` (합성곱 32→64, 최대풀링, 드롭아웃, 완전연결 128→10,
  로그 소프트맥스). `모델_불러오기()`가 가중치를 읽어 `eval()` 상태로 돌려준다.
- **`train.py`** — MNIST를 받아 학습하고 `mnist_cnn.pt`에 `state_dict`를 저장한다.
- **`app.py`** — Tkinter 그림판. 마우스를 떼면 `인식하기()`가 돌고, 숫자별 확률 막대와
  모델이 실제로 보는 28x28 미리보기를 함께 표시한다.

### 반드시 함께 바꿔야 하는 것들

모델 구조를 바꾸면 `mnist_cnn.pt`가 무효가 되므로 **반드시 재학습**해야 한다.

정규화 상수 `평균 = 0.1307`, `표준편차 = 0.3081`은 `train.py`와 `app.py`에 각각
정의되어 있다. **한쪽만 바꾸면 추론이 조용히 망가진다.**

### 인식률을 지탱하는 두 가지 장치

이 둘은 장식이 아니라 실제 인식률을 좌우하므로 함부로 제거하면 안 된다.

1. **`app.전처리()`** — 그린 그림을 MNIST와 같은 규칙으로 맞춘다. 경계 상자를 잘라
   긴 변이 20px이 되게 줄이고, 28x28에 붙인 뒤 픽셀 **무게중심을 (13.5, 13.5)로 이동**
   시킨다. MNIST 자체가 그렇게 만들어진 데이터라, 이 과정 없이 단순 축소만 하면
   실제 인식률이 크게 떨어진다.
2. **학습 데이터 증강** — `train.데이터로더_준비()`의 `RandomAffine`
   (회전 ±10°, 이동 ±10%, 확대축소 90~110%). 마우스 글씨는 MNIST 원본보다
   위치와 기울기가 제각각이라 이 증강이 실사용 정확도를 끌어올린다.

### 더블클릭 실행 구조

`app.py`는 `.venv` 밖의 파이썬으로 실행돼도 동작한다. `가상환경으로_재실행()`이
`import torch`를 시도해 실패하면 `.venv\Scripts\pythonw.exe`로 자기 자신을 다시
실행한다. 무한 반복은 환경 변수 `손글씨앱_재실행`으로 막는다. 이 함수는
**torch·numpy·PIL을 import 하기 전에** 실행되어야 하므로 파일 상단에 위치한다.

작업 표시줄 고정이 제대로 동작하려면 바로 가기의 `PKEY_AppUserModel_ID` 속성과
`app.앱_아이디`(`작업표시줄_아이디_설정()`이 등록)가 **같은 값**이어야 한다.
다르면 고정한 아이콘과 실행 중인 창이 별개의 단추로 갈라진다.

바로 가기는 `바로가기_만들기.ps1`이 생성한다. `.lnk` 파일 안에는 만든 PC의
**절대 경로와 컴퓨터 이름**이 기록되고 다른 PC에서는 경로가 달라 동작하지 않으므로,
`.gitignore`로 저장소에서 제외한다. 이 스크립트는 한글 주석 때문에
**UTF-8 BOM으로 저장**해야 한다(BOM이 없으면 PowerShell 5.1이 cp949로 읽어 깨진다).

`.py` 확장자는 `HKCU\Software\Classes\.py` → `Python.NoConFile` → `pyw.exe`로
연결해 두었다(사용자 계정 범위, 관리자 권한 불필요).

## Windows 환경에서 반복적으로 부딪힌 함정

- 프로젝트 경로에 **한글과 공백**이 모두 들어 있다(`C:\3장 손글씨 앱\...`). 경로는 항상 인용한다.
- **배치 파일**: `if (...)` 블록 안의 `echo` 문에 괄호가 있으면 cmd 파서가 블록을
  조기에 닫아 `was unexpected at this time` 오류가 난다. `goto`로 분기한다.
  또 배치 파일은 UTF-8이 아닌 **ANSI(cp949)** 로 저장해야 한글이 깨지지 않는다.
- **PowerShell 5.1**: `.ps1` 파일을 BOM 없는 UTF-8로 저장하면 한글 리터럴이 깨져
  파싱 오류가 난다. 스크립트는 ASCII로 쓰고 한글은 파라미터로 넘긴다.
- **PowerShell의 형변환 연산자는 COM 객체에 `QueryInterface`를 하지 않는다.**
  `[IShellLinkW]$obj` 같은 캐스팅은 실패하므로, 바로 가기를 다루는 로직은
  `Add-Type`으로 컴파일한 C# 안에 넣어야 한다.
- 백그라운드로 띄운 앱이 출력 파이프를 붙잡고 있으면 이를 실행한 셸 명령이
  끝나지 않는다. 앱 실행은 출력을 캡처하지 않는 방식으로 한다.
- `pythonw.exe`로 실행하면 `sys.stdout`이 `None`이라 `sys.stdout.reconfigure()`가
  `AttributeError`를 낸다. 각 스크립트 상단에서 `try/except`로 감싸 둔 이유다.
  콘솔이 없어 오류가 보이지 않으므로 `app.py`는 예외를 대화상자로 띄운다.
