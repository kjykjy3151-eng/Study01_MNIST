"""자바스크립트 구현을 검증할 정답 데이터를 파이썬 쪽에서 만듭니다.

실행:
    ..\\..\\desktop_version\\.venv\\Scripts\\python.exe 골든_만들기.py

MNIST 평가셋 앞 200장을 10배로 확대해 '그림판에 그린 그림'으로 삼고,
데스크톱과 똑같은 전처리, 똑같은 모델을 거친 결과를 골든/ 에 저장합니다.
"""
# 2026-09-21 18:23 KST

import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

기준_폴더 = Path(__file__).resolve().parent
저장소_루트 = 기준_폴더.parent.parent
데스크톱_폴더 = 저장소_루트 / "desktop_version"

# 데스크톱 구현을 그대로 빌려 씁니다. 복사하면 두 구현이 조용히 어긋납니다.
sys.path.insert(0, str(데스크톱_폴더))
from app import 전처리, 평균, 표준편차          # noqa: E402
from model import 모델_불러오기                  # noqa: E402

from torchvision import datasets                 # noqa: E402

표본_개수 = 200
확대_배율 = 10       # 28 * 10 = 280. 데스크톱 캔버스와 같은 크기
골든_폴더 = 기준_폴더 / "골든"


def 메인():
    가중치_경로 = 데스크톱_폴더 / "mnist_cnn.pt"
    if not 가중치_경로.exists():
        print(f"[오류] 가중치 파일이 없습니다: {가중치_경로}")
        sys.exit(1)

    장치 = torch.device("cpu")
    모델 = 모델_불러오기(가중치_경로, 장치)

    평가_데이터셋 = datasets.MNIST(str(데스크톱_폴더 / "data"), train=False, download=True)

    원본들 = np.zeros((표본_개수, 28, 28), dtype=np.uint8)
    전처리들 = np.zeros((표본_개수, 28, 28), dtype=np.uint8)
    확률들 = np.zeros((표본_개수, 10), dtype="<f4")
    예측들 = np.zeros(표본_개수, dtype=np.uint8)

    for 번호 in range(표본_개수):
        이미지, _ = 평가_데이터셋[번호]
        원본 = np.array(이미지, dtype=np.uint8)
        원본들[번호] = 원본

        # 최근접 이웃으로 10배 확대해 280x280 캔버스 그림을 흉내 냅니다.
        확대 = np.repeat(np.repeat(원본, 확대_배율, axis=0), 확대_배율, axis=1)
        정리된 = 전처리(Image.fromarray(확대, mode="L"))
        if 정리된 is None:
            print(f"[오류] {번호}번 표본의 전처리 결과가 비었습니다.")
            sys.exit(1)
        전처리들[번호] = np.round(정리된 * 255.0).astype(np.uint8)

        정규화 = (정리된 - 평균) / 표준편차
        입력 = torch.from_numpy(정규화).unsqueeze(0).unsqueeze(0).to(장치)
        with torch.no_grad():
            확률 = torch.exp(모델(입력))[0].cpu().numpy()
        확률들[번호] = 확률.astype("<f4")
        예측들[번호] = int(확률.argmax())

    골든_폴더.mkdir(parents=True, exist_ok=True)
    (골든_폴더 / "원본_28.bin").write_bytes(원본들.tobytes())
    (골든_폴더 / "전처리_28.bin").write_bytes(전처리들.tobytes())
    (골든_폴더 / "확률.bin").write_bytes(확률들.tobytes())
    (골든_폴더 / "예측.bin").write_bytes(예측들.tobytes())

    print(f"골든 데이터 {표본_개수}개 저장 완료 -> {골든_폴더}")
    print(f"  예측 분포: {np.bincount(예측들, minlength=10)}")


if __name__ == "__main__":
    메인()
