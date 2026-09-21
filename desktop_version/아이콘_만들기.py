"""손글씨 인식 앱의 아이콘(아이콘.ico)을 만드는 스크립트.

바탕 화면 바로 가기와 작업 표시줄, 창 왼쪽 위에 쓰입니다.
한 번만 실행하면 되고, 아이콘 모양을 바꾸고 싶을 때 다시 실행하면 됩니다.

    python 아이콘_만들기.py

작은 크기(16x16)에서도 알아볼 수 있도록, 어두운 둥근 사각형 위에
손글씨체 숫자 하나를 크고 굵게 올린 단순한 형태로 만듭니다.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

기준_폴더 = Path(__file__).resolve().parent
아이콘_경로 = 기준_폴더 / "아이콘.ico"

# 아이콘에 넣을 숫자와 색
표시_숫자 = "3"
배경색 = (17, 24, 39)      # 짙은 남색 (앱의 검은 캔버스와 어울리는 색)
글씨색 = (255, 255, 255)
강조색 = (59, 130, 246)    # 앱의 확률 막대와 같은 파란색

# 손글씨 느낌을 주는 글꼴을 운영체제별로 찾습니다.
# 하나도 없으면 PIL 기본 글꼴로 대체하므로, 어느 환경에서든 실행은 됩니다.
글꼴_후보 = [
    r"C:\Windows\Fonts\segoescb.ttf",              # 윈도우: Segoe Script Bold
    r"C:\Windows\Fonts\segoesc.ttf",               # 윈도우: Segoe Script
    "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",   # macOS
    "/System/Library/Fonts/Supplemental/Chalkduster.ttf",         # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",       # 리눅스
]


def 글꼴_고르기(글꼴_크기):
    """쓸 수 있는 손글씨체를 찾아 돌려줍니다. 없으면 PIL 기본 글꼴을 씁니다."""
    for 후보 in 글꼴_후보:
        if Path(후보).exists():
            return ImageFont.truetype(후보, 글꼴_크기)
    print("[알림] 손글씨체를 찾지 못해 기본 글꼴로 그립니다.")
    return ImageFont.load_default()


def 아이콘_그리기(크기):
    """한 변이 `크기`인 정사각형 아이콘 이미지를 그려 돌려줍니다.

    실제로는 4배 크기로 그린 뒤 줄여서, 가장자리를 부드럽게 만듭니다.
    """
    배율 = 4
    큰_크기 = 크기 * 배율
    그림 = Image.new("RGBA", (큰_크기, 큰_크기), (0, 0, 0, 0))
    그리기 = ImageDraw.Draw(그림)

    # 1) 둥근 사각형 배경
    여백 = 큰_크기 * 0.04
    반지름 = 큰_크기 * 0.22
    그리기.rounded_rectangle(
        [여백, 여백, 큰_크기 - 여백, 큰_크기 - 여백],
        radius=반지름, fill=배경색,
    )

    # 2) 아래쪽에 파란 밑줄 - 손글씨를 쓰는 줄을 상징합니다.
    줄_두께 = max(2, int(큰_크기 * 0.055))
    그리기.rounded_rectangle(
        [큰_크기 * 0.24, 큰_크기 * 0.775,
         큰_크기 * 0.76, 큰_크기 * 0.775 + 줄_두께],
        radius=줄_두께 / 2, fill=강조색,
    )

    # 3) 가운데에 손글씨체 숫자
    글꼴_크기 = int(큰_크기 * 0.70)
    글꼴 = 글꼴_고르기(글꼴_크기)
    왼쪽, 위, 오른쪽, 아래 = 그리기.textbbox((0, 0), 표시_숫자, font=글꼴)
    글자_x = (큰_크기 - (오른쪽 - 왼쪽)) / 2 - 왼쪽
    글자_y = 큰_크기 * 0.40 - (아래 - 위) / 2 - 위
    그리기.text((글자_x, 글자_y), 표시_숫자, font=글꼴, fill=글씨색)

    return 그림.resize((크기, 크기), Image.LANCZOS)


def 메인():
    # 윈도우가 상황에 맞는 크기를 골라 쓰도록 여러 해상도를 한 파일에 담습니다.
    크기들 = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    이미지들 = [아이콘_그리기(크기) for 크기 in 크기들]

    # 가장 큰 이미지를 기준으로 저장하면서 나머지 크기를 함께 포함시킵니다.
    이미지들[-1].save(아이콘_경로, format="ICO",
                      sizes=[(크기, 크기) for 크기 in 크기들])
    print(f"아이콘 저장 완료 → {아이콘_경로}")
    print(f"포함된 크기: {', '.join(f'{크기}x{크기}' for 크기 in 크기들)}")

    # 맥·리눅스의 Tk는 .ico를 읽지 못하므로, 창 아이콘용 PNG를 따로 만듭니다.
    # (app.py의 창_아이콘_설정()이 이 파일을 씁니다)
    PNG_경로 = 기준_폴더 / "아이콘.png"
    아이콘_그리기(128).save(PNG_경로)
    print(f"PNG 아이콘 저장 완료 → {PNG_경로} (맥·리눅스 창 아이콘용)")

    # 눈으로 확인하기 좋도록 미리보기 PNG도 하나 남깁니다.
    미리보기_경로 = 기준_폴더 / "아이콘_미리보기.png"
    아이콘_그리기(256).save(미리보기_경로)
    print(f"미리보기 저장 완료 → {미리보기_경로}")


if __name__ == "__main__":
    메인()
