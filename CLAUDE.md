<!-- 2026-09-21 18:23 KST -->

# CLAUDE.md

이 저장소는 MNIST 손글씨 숫자 인식 앱을 두 가지로 제공한다.

| 폴더 | 무엇 | 자세한 지침 |
| --- | --- | --- |
| `desktop_version/` | 파이썬, Tkinter 데스크톱 앱과 학습 코드 | `desktop_version/CLAUDE.md` |
| `web_version/` | 외부 라이브러리 없는 순수 자바스크립트 웹 앱 | `web_version/CLAUDE.md` |

## 언어 규칙

이 저장소의 코드와 주석은 **한글로 작성한다.** 독스트링, 인라인 주석,
사용자에게 보이는 문자열, 직접 정의하는 클래스, 함수, 변수 이름까지 모두
한글을 쓴다. 프레임워크가 이름을 고정하는 부분(`forward`, `__init__`,
DOM API 이름, 라이브러리 인자명)만 영어를 유지하고, 그런 경우에는 독스트링으로
한글 설명을 붙인다.

## 가상환경

파이썬 가상환경은 `desktop_version/.venv` 하나뿐이다. 데스크톱 앱과 학습이
이것을 쓰고, 웹 쪽 개발용 스크립트(가중치 내보내기, 골든 데이터 생성)도
torch 가 필요해 같은 환경을 빌려 쓴다.

`.venv` 가 `desktop_version/` 안에 있는 것은 우연이 아니다. 데스크톱 쪽
파일들은 모두 자기 위치를 기준으로 경로를 만들기 때문에, `.venv` 까지 한
덩어리로 두면 폴더를 옮겨도 코드를 고칠 필요가 없다. 이 성질을 깨뜨리지 말라.

`.venv-tf` 는 TensorFlow 별도 실험용이며 어느 쪽 코드도 참조하지 않는다.

## 세 곳이 함께 움직여야 하는 것

모델 구조와 정규화 상수(`평균 = 0.1307`, `표준편차 = 0.3081`)는 아래 세 곳이
반드시 같아야 한다. 한 곳만 바꾸면 **추론이 조용히 망가진다.**

1. `desktop_version/train.py` — 학습할 때 쓰는 값
2. `desktop_version/app.py`, `desktop_version/model.py` — 데스크톱 추론
3. `web_version/가중치/구조.json` — 웹 추론 (내보내기 스크립트가 기록)

모델 구조를 바꾸면 `mnist_cnn.pt` 가 무효가 되므로 **재학습**한 뒤,
`web_version/도구/가중치_내보내기.py` 로 웹 가중치를 다시 만들고
`node web_version/테스트/검증.mjs` 로 두 구현이 여전히 같은 답을 내는지
확인해야 한다.

## 전처리 규칙

`desktop_version/app.py` 의 `전처리()` 와 `web_version/js/전처리.js` 는
**같은 알고리즘의 두 구현**이다. 한쪽을 고치면 다른 쪽도 고치고,
`web_version/테스트/골든_만들기.py` 를 다시 돌린 뒤 검증을 통과시켜야 한다.

## 배포

GitHub Pages 로 저장소 전체를 게시한다. **빌드 단계는 없다.** 웹 버전이 외부
라이브러리도 번들러도 쓰지 않으므로 파일을 그대로 올리기만 하면 된다.
웹 앱 주소는 `.../Study01_MNIST/web_version/` 이고, 루트 `index.html` 이
그리로 보내 준다. 루트의 빈 `.nojekyll` 은 Pages 의 Jekyll 처리를 끈다.

`.github/workflows/pages.yml` 이 배포를 맡는다. 설정을 `Deploy from a branch` 의
`main` / `(root)` 로 바꾸면 그 워크플로 파일은 지워도 된다. 설계 문서는
워크플로 없는 쪽을 전제로 쓰였는데, 실제 저장소 설정이 달라 이렇게 맞췄다.

**Pages 사이트 생성은 워크플로가 스스로 하지 못한다.** 사이트 생성은 저장소
관리 권한을 요구하는데 워크플로의 `GITHUB_TOKEN` 에는 그 권한이 없고,
`permissions:` 로 요청할 수도 없다. `configure-pages` 의 `enablement: true` 도
`Resource not accessible by integration` 으로 거부된다. 사이트가 없는 상태로
워크플로를 돌리면 `Get Pages site failed ... Not Found` 로 실패한다.

최초 1회는 **저장소 관리 권한이 있는 계정 토큰**으로 켠다. Settings → Pages 에서
Source 를 `GitHub Actions` 로 지정해도 되고, `repo` 스코프로 로그인한 `gh` 로
아래 한 줄을 실행해도 된다. 실제로 이 저장소는 이 명령으로 켰다.

```bash
gh api --method POST repos/kjykjy3151-eng/Study01_MNIST/pages -f build_type=workflow
```

한 번 켠 뒤에는 `gh workflow run pages.yml --ref main` 으로 언제든 다시 배포할
수 있다. 사이트가 이미 있으면 `enablement: true` 가 남아 있어도 실패하지 않는다.

## 설계 문서

- 설계: `docs/superpowers/specs/2026-09-21-웹-데스크톱-분리-설계.md`
- 구현 계획: `docs/superpowers/plans/2026-09-21-웹-데스크톱-분리.md`

`CLAUDE_전역.md` 는 전역 지침의 사본이며 이 저장소의 규칙이 아니다.
