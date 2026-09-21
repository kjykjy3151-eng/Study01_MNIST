"""MNIST 손글씨 숫자 인식을 위한 CNN 모델 정의 모듈.

학습 스크립트(train.py)와 손글씨 입력 앱(app.py)이 이 모듈의
모델 구조를 공유하므로, 구조를 바꾸면 반드시 다시 학습해야 합니다.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class 숫자인식CNN(nn.Module):
    """28x28 흑백 손글씨 이미지를 0~9 중 하나로 분류하는 합성곱 신경망.

    구조 요약
        입력 (1, 28, 28)
          -> 합성곱1 (32채널, 3x3) + ReLU        -> (32, 26, 26)
          -> 합성곱2 (64채널, 3x3) + ReLU        -> (64, 24, 24)
          -> 최대풀링 (2x2)                      -> (64, 12, 12)
          -> 드롭아웃(0.25) -> 평탄화            -> (9216,)
          -> 완전연결1 (128) + ReLU + 드롭아웃(0.5)
          -> 완전연결2 (10)  -> 로그 소프트맥스
    """

    def __init__(self):
        super().__init__()
        # 특징 추출부: 두 번의 합성곱으로 선/곡선 같은 획의 모양을 잡아냅니다.
        self.합성곱1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, stride=1)
        self.합성곱2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=1)

        # 과적합을 줄이기 위한 드롭아웃 두 개
        self.드롭아웃1 = nn.Dropout(0.25)
        self.드롭아웃2 = nn.Dropout(0.5)

        # 분류부: 추출된 특징을 10개 숫자 클래스 점수로 변환합니다.
        self.완전연결1 = nn.Linear(64 * 12 * 12, 128)
        self.완전연결2 = nn.Linear(128, 10)

    def forward(self, 입력):
        """순전파. PyTorch가 호출하는 규약상 이름은 forward 로 고정입니다.

        인자:
            입력: (배치, 1, 28, 28) 모양의 텐서
        반환:
            (배치, 10) 모양의 로그 확률 텐서
        """
        출력 = F.relu(self.합성곱1(입력))
        출력 = F.relu(self.합성곱2(출력))
        출력 = F.max_pool2d(출력, 2)      # 해상도를 절반으로 줄여 계산량 감소
        출력 = self.드롭아웃1(출력)
        출력 = torch.flatten(출력, 1)      # 배치 차원만 남기고 1차원으로 펼치기
        출력 = F.relu(self.완전연결1(출력))
        출력 = self.드롭아웃2(출력)
        출력 = self.완전연결2(출력)
        return F.log_softmax(출력, dim=1)  # NLLLoss 와 짝을 이루는 로그 확률


def 모델_불러오기(가중치_경로, 장치=None):
    """저장된 가중치 파일을 읽어 추론 준비가 끝난 모델을 돌려줍니다.

    인자:
        가중치_경로: mnist_cnn.pt 같은 state_dict 파일 경로
        장치: torch.device. 생략하면 CUDA 사용 가능 여부로 자동 결정
    반환:
        평가 모드(eval)로 전환된 숫자인식CNN 인스턴스
    """
    if 장치 is None:
        장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    모델 = 숫자인식CNN().to(장치)
    모델.load_state_dict(torch.load(가중치_경로, map_location=장치))
    모델.eval()  # 드롭아웃을 끄고 추론 모드로 전환
    return 모델
