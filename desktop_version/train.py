"""MNIST 데이터셋으로 손글씨 숫자 인식 CNN을 학습하고 가중치를 저장하는 스크립트.

실행 예시
    python train.py                 # 기본 설정(5 에포크)으로 학습
    python train.py --에포크 10     # 에포크 수를 바꿔서 학습

학습이 끝나면 가중치가 mnist_cnn.pt 파일로 저장되고,
app.py 가 그 파일을 읽어 손글씨를 인식합니다.
"""

import argparse
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import 숫자인식CNN

# 윈도우 터미널에서 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 맞춥니다.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# MNIST 학습 데이터 전체의 평균과 표준편차 (정규화에 사용하는 관례적인 값)
평균 = 0.1307
표준편차 = 0.3081

# 이 스크립트가 있는 폴더를 기준으로 경로를 잡아, 어디서 실행해도 동작하게 합니다.
기준_폴더 = Path(__file__).resolve().parent


def 데이터로더_준비(배치크기, 평가_배치크기, 데이터_폴더):
    """MNIST를 내려받아 학습용/평가용 DataLoader 두 개를 만들어 돌려줍니다.

    학습용에는 약간의 회전·이동·확대축소를 무작위로 적용합니다.
    마우스로 그린 글씨는 MNIST 원본보다 위치와 기울기가 제각각이라,
    이런 증강을 넣어야 실제 앱에서의 인식률이 눈에 띄게 좋아집니다.
    """
    학습_변환 = transforms.Compose([
        transforms.RandomAffine(
            degrees=10,              # ±10도 회전
            translate=(0.1, 0.1),    # 가로·세로로 최대 10% 이동
            scale=(0.9, 1.1),        # 90~110% 확대/축소
        ),
        transforms.ToTensor(),                     # 0~255 → 0.0~1.0 텐서
        transforms.Normalize((평균,), (표준편차,)),  # 평균 0, 표준편차 1 근처로 정규화
    ])

    # 평가할 때는 증강 없이 원본 그대로 사용합니다.
    평가_변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((평균,), (표준편차,)),
    ])

    학습_데이터셋 = datasets.MNIST(데이터_폴더, train=True, download=True, transform=학습_변환)
    평가_데이터셋 = datasets.MNIST(데이터_폴더, train=False, download=True, transform=평가_변환)

    학습_로더 = DataLoader(학습_데이터셋, batch_size=배치크기, shuffle=True)
    평가_로더 = DataLoader(평가_데이터셋, batch_size=평가_배치크기, shuffle=False)
    return 학습_로더, 평가_로더


def 한_에포크_학습(모델, 장치, 학습_로더, 최적화기, 현재_에포크, 출력_간격=100):
    """한 에포크 동안 모델을 학습시키고 평균 손실을 돌려줍니다."""
    모델.train()  # 드롭아웃을 켜는 학습 모드
    누적_손실 = 0.0

    for 배치_번호, (이미지, 정답) in enumerate(학습_로더):
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)

        최적화기.zero_grad()            # 이전 배치의 기울기 초기화
        예측 = 모델(이미지)             # 순전파
        손실 = F.nll_loss(예측, 정답)   # 로그 소프트맥스와 짝이 되는 손실 함수
        손실.backward()                 # 역전파로 기울기 계산
        최적화기.step()                 # 가중치 갱신

        누적_손실 += 손실.item()

        if 배치_번호 % 출력_간격 == 0:
            진행_개수 = 배치_번호 * len(이미지)
            전체_개수 = len(학습_로더.dataset)
            진행률 = 100.0 * 배치_번호 / len(학습_로더)
            print(f"  에포크 {현재_에포크} [{진행_개수:5d}/{전체_개수} ({진행률:3.0f}%)]  손실: {손실.item():.4f}")

    return 누적_손실 / len(학습_로더)


def 평가(모델, 장치, 평가_로더):
    """평가 데이터셋으로 평균 손실과 정확도를 측정해 돌려줍니다."""
    모델.eval()  # 드롭아웃을 끄는 평가 모드
    누적_손실 = 0.0
    맞힌_개수 = 0

    with torch.no_grad():  # 평가 중에는 기울기를 계산하지 않아 메모리·속도가 절약됩니다.
        for 이미지, 정답 in 평가_로더:
            이미지, 정답 = 이미지.to(장치), 정답.to(장치)
            예측 = 모델(이미지)
            누적_손실 += F.nll_loss(예측, 정답, reduction="sum").item()
            예측_숫자 = 예측.argmax(dim=1)  # 가장 점수가 높은 클래스를 선택
            맞힌_개수 += 예측_숫자.eq(정답).sum().item()

    전체_개수 = len(평가_로더.dataset)
    평균_손실 = 누적_손실 / 전체_개수
    정확도 = 100.0 * 맞힌_개수 / 전체_개수
    return 평균_손실, 정확도, 맞힌_개수, 전체_개수


def 인자_파싱():
    """명령줄 인자를 읽어 옵니다."""
    파서 = argparse.ArgumentParser(description="MNIST 손글씨 숫자 인식 CNN 학습")
    파서.add_argument("--에포크", type=int, default=5, help="학습 반복 횟수 (기본값: 5)")
    파서.add_argument("--배치크기", type=int, default=64, help="학습 배치 크기 (기본값: 64)")
    파서.add_argument("--평가배치크기", type=int, default=1000, help="평가 배치 크기 (기본값: 1000)")
    파서.add_argument("--학습률", type=float, default=1.0, help="Adadelta 학습률 (기본값: 1.0)")
    파서.add_argument("--감마", type=float, default=0.7, help="에포크마다 학습률에 곱할 값 (기본값: 0.7)")
    파서.add_argument("--시드", type=int, default=1, help="난수 시드 (기본값: 1)")
    파서.add_argument("--데이터폴더", type=str, default=str(기준_폴더 / "data"),
                      help="MNIST 데이터를 내려받아 둘 폴더")
    파서.add_argument("--저장경로", type=str, default=str(기준_폴더 / "mnist_cnn.pt"),
                      help="학습된 가중치를 저장할 경로 (기본값: mnist_cnn.pt)")
    파서.add_argument("--CPU강제", action="store_true", help="GPU가 있어도 CPU로만 학습")
    return 파서.parse_args()


def 메인():
    인자 = 인자_파싱()
    torch.manual_seed(인자.시드)  # 실행할 때마다 같은 결과가 나오도록 고정

    GPU사용 = torch.cuda.is_available() and not 인자.CPU강제
    장치 = torch.device("cuda" if GPU사용 else "cpu")

    print("=" * 60)
    print("MNIST 손글씨 숫자 인식 CNN 학습을 시작합니다.")
    print(f"  사용 장치   : {장치}")
    print(f"  에포크      : {인자.에포크}")
    print(f"  배치 크기   : {인자.배치크기}")
    print(f"  저장 경로   : {인자.저장경로}")
    print("=" * 60)

    print("\n[1/3] MNIST 데이터셋을 준비합니다. (처음 한 번은 내려받기 때문에 시간이 걸립니다)")
    학습_로더, 평가_로더 = 데이터로더_준비(인자.배치크기, 인자.평가배치크기, 인자.데이터폴더)
    print(f"  학습 샘플 {len(학습_로더.dataset)}개, 평가 샘플 {len(평가_로더.dataset)}개 준비 완료")

    모델 = 숫자인식CNN().to(장치)
    최적화기 = optim.Adadelta(모델.parameters(), lr=인자.학습률)
    # 에포크가 지날수록 학습률을 줄여 마무리를 안정적으로 만듭니다.
    스케줄러 = optim.lr_scheduler.StepLR(최적화기, step_size=1, gamma=인자.감마)

    print("\n[2/3] 학습을 시작합니다.")
    시작_시각 = time.time()
    for 현재_에포크 in range(1, 인자.에포크 + 1):
        평균_학습손실 = 한_에포크_학습(모델, 장치, 학습_로더, 최적화기, 현재_에포크)
        평균_손실, 정확도, 맞힌_개수, 전체_개수 = 평가(모델, 장치, 평가_로더)
        스케줄러.step()
        print(f"  ▶ 에포크 {현재_에포크} 완료 | 학습 손실 {평균_학습손실:.4f} | "
              f"평가 손실 {평균_손실:.4f} | 정확도 {맞힌_개수}/{전체_개수} ({정확도:.2f}%)\n")

    걸린_시간 = time.time() - 시작_시각
    print(f"학습에 걸린 시간: {걸린_시간 / 60:.1f}분")

    print("[3/3] 학습된 가중치를 저장합니다.")
    torch.save(모델.state_dict(), 인자.저장경로)
    print(f"  저장 완료 → {인자.저장경로}")
    print("\n이제 'python app.py' 를 실행해 손글씨를 직접 그려 보세요!")


if __name__ == "__main__":
    메인()
