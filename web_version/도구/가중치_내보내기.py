"""학습된 mnist_cnn.pt 를 웹 버전이 읽을 수 있는 원시 바이너리로 내보냅니다.

실행:
    ..\\..\\desktop_version\\.venv\\Scripts\\python.exe 가중치_내보내기.py

만들어지는 파일
    ../가중치/mnist_cnn.bin  리틀엔디언 float32를 정해진 순서로 이어 붙인 것
    ../가중치/구조.json      각 텐서의 이름, 모양, 오프셋과 정규화 상수
"""
# 2026-09-21 18:23 KST

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import torch

기준_폴더 = Path(__file__).resolve().parent
웹_폴더 = 기준_폴더.parent
원본_경로 = 웹_폴더.parent / "desktop_version" / "mnist_cnn.pt"
가중치_폴더 = 웹_폴더 / "가중치"

# 정규화 상수. desktop_version/train.py, app.py 와 반드시 같아야 합니다.
평균 = 0.1307
표준편차 = 0.3081

# 내보내는 순서입니다. 자바스크립트가 이 순서대로 잘라 읽으므로 바꾸면 안 됩니다.
내보낼_순서 = [
    ("합성곱1.weight", (32, 1, 3, 3)),
    ("합성곱1.bias", (32,)),
    ("합성곱2.weight", (64, 32, 3, 3)),
    ("합성곱2.bias", (64,)),
    ("완전연결1.weight", (128, 9216)),
    ("완전연결1.bias", (128,)),
    ("완전연결2.weight", (10, 128)),
    ("완전연결2.bias", (10,)),
]
기대_바이트 = 4_799_528


def 한국_시각():
    """생성 시각을 한국 표준시 문자열로 돌려줍니다."""
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")


def 메인():
    if not 원본_경로.exists():
        print(f"[오류] 가중치 파일을 찾을 수 없습니다: {원본_경로}")
        print("먼저 desktop_version 에서 train.py 로 학습해 주세요.")
        sys.exit(1)

    가중치_묶음 = torch.load(원본_경로, map_location="cpu")

    조각들 = []
    텐서_정보 = []
    시작 = 0
    for 이름, 기대_모양 in 내보낼_순서:
        if 이름 not in 가중치_묶음:
            print(f"[오류] 가중치에 {이름} 이(가) 없습니다. 모델 구조가 바뀌었는지 확인해 주세요.")
            sys.exit(1)
        텐서 = 가중치_묶음[이름]
        if tuple(텐서.shape) != 기대_모양:
            print(f"[오류] {이름} 의 모양이 {tuple(텐서.shape)} 입니다. {기대_모양} 이어야 합니다.")
            sys.exit(1)

        평탄한_값 = 텐서.detach().cpu().numpy().astype("<f4").ravel()
        조각들.append(평탄한_값.tobytes())
        텐서_정보.append({
            "이름": 이름,
            "모양": list(기대_모양),
            "시작": 시작,
            "개수": int(평탄한_값.size),
        })
        시작 += int(평탄한_값.size)

    가중치_폴더.mkdir(parents=True, exist_ok=True)
    이진_경로 = 가중치_폴더 / "mnist_cnn.bin"
    이진_경로.write_bytes(b"".join(조각들))

    실제_바이트 = 이진_경로.stat().st_size
    if 실제_바이트 != 기대_바이트:
        print(f"[오류] 만들어진 파일이 {실제_바이트} 바이트입니다. {기대_바이트} 바이트여야 합니다.")
        sys.exit(1)

    구조 = {
        "설명": "웹 버전 추론용 가중치. 도구/가중치_내보내기.py 가 만듭니다.",
        "만든_시각": 한국_시각(),
        "가중치_파일": "mnist_cnn.bin",
        "전체_바이트": 기대_바이트,
        "평균": 평균,
        "표준편차": 표준편차,
        "텐서들": 텐서_정보,
    }
    (가중치_폴더 / "구조.json").write_text(
        json.dumps(구조, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"내보내기 완료 -> {이진_경로} ({실제_바이트:,} 바이트)")
    print(f"구조 정보 저장 -> {가중치_폴더 / '구조.json'}")


if __name__ == "__main__":
    메인()
