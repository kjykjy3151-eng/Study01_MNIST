"""마우스로 숫자를 그리면 학습된 CNN이 몇 번인지 맞혀 주는 손글씨 인식 앱.

실행 방법
    python train.py   # 먼저 학습해서 mnist_cnn.pt 를 만들고
    python app.py     # 그다음 이 앱을 실행합니다

사용 방법
    - 검은 캔버스 위에 마우스를 끌어 숫자를 크게 하나 그립니다.
    - 마우스에서 손을 떼면 자동으로 인식 결과가 갱신됩니다.
    - [지우기] 버튼이나 Esc 키로 캔버스를 비웁니다.
"""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

기준_폴더 = Path(__file__).resolve().parent

# 윈도우 터미널에서 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 맞춥니다.
# (pythonw.exe로 실행하면 sys.stdout이 None이라 AttributeError가 납니다)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def 가상환경으로_재실행():
    """PyTorch가 없는 파이썬으로 실행됐다면 .venv 환경으로 자기 자신을 다시 실행합니다.

    파일 탐색기에서 app.py를 더블클릭하면 시스템에 연결된 파이썬으로 실행되는데,
    거기에는 torch가 없어서 그냥 두면 창이 뜨지 않고 죽어 버립니다.
    그래서 torch를 불러올 수 있는지 먼저 확인하고, 안 되면 프로젝트 폴더 안의
    가상환경 실행기로 바꿔서 다시 실행합니다.

    반환:
        재실행을 했으면 True (호출한 쪽은 바로 종료해야 합니다). 아니면 False
    """
    # 이미 재실행된 프로세스라면 또 재실행하지 않습니다. (무한 반복 방지)
    if os.environ.get("손글씨앱_재실행") == "1":
        return False

    try:
        import torch  # noqa: F401
        return False  # 현재 파이썬으로 충분하므로 그대로 진행
    except ImportError:
        pass

    # 콘솔 창이 뜨지 않는 pythonw.exe를 우선 사용합니다.
    후보들 = [
        기준_폴더 / ".venv" / "Scripts" / "pythonw.exe",  # 윈도우
        기준_폴더 / ".venv" / "Scripts" / "python.exe",
        기준_폴더 / ".venv" / "bin" / "python",            # macOS / 리눅스
    ]
    실행기 = next((경로 for 경로 in 후보들 if 경로.exists()), None)

    if 실행기 is None:
        임시_루트 = tk.Tk()
        임시_루트.withdraw()
        messagebox.showerror(
            "실행 환경 없음",
            "PyTorch가 설치된 가상환경(.venv)을 찾지 못했습니다.\n\n"
            f"프로젝트 폴더: {기준_폴더}\n\n"
            "터미널에서 아래 명령으로 환경을 먼저 만들어 주세요.\n"
            "  python -m venv .venv\n"
            "  .venv\\Scripts\\pip install -r requirements.txt",
        )
        임시_루트.destroy()
        sys.exit(1)

    환경 = dict(os.environ, 손글씨앱_재실행="1", PYTHONIOENCODING="utf-8")
    subprocess.Popen([str(실행기), str(Path(__file__).resolve())],
                     cwd=str(기준_폴더), env=환경)
    return True


# 다른 곳에서 import할 때는 재실행하지 않고, 직접 실행했을 때만 확인합니다.
if __name__ == "__main__" and 가상환경으로_재실행():
    sys.exit(0)

import numpy as np
import torch
from PIL import Image, ImageDraw

from model import 모델_불러오기

# ----- 설정값 --------------------------------------------------------------
가중치_경로 = 기준_폴더 / "mnist_cnn.pt"
아이콘_경로 = 기준_폴더 / "아이콘.ico"

# 윈도우 작업 표시줄이 이 앱을 구분하는 식별자입니다.
# 바로 가기(.lnk)에 넣는 값과 반드시 같아야 하며, 영문·숫자·점만 씁니다.
앱_아이디 = "MNIST.HandwrittenDigitRecognizer.1"

캔버스_크기 = 280   # 화면에 보이는 그림판 한 변의 픽셀 수 (28의 10배)
붓_굵기 = 22        # 선 굵기. 28x28로 줄였을 때 MNIST와 비슷한 두께가 되도록 잡은 값
평균 = 0.1307       # 학습 때 사용한 정규화 값과 반드시 같아야 합니다.
표준편차 = 0.3081
# ---------------------------------------------------------------------------


def 전처리(원본_이미지):
    """손으로 그린 그림을 MNIST와 같은 형식의 28x28 이미지로 다듬습니다.

    MNIST는 '숫자를 20x20 안에 맞춰 넣고, 무게중심을 28x28의 한가운데로 옮긴'
    데이터입니다. 그림판에서 그린 글씨도 똑같은 규칙으로 맞춰 줘야
    학습한 모델이 제 실력을 냅니다.

    인자:
        원본_이미지: 검은 배경에 흰 글씨로 그려진 PIL 흑백 이미지
    반환:
        (28, 28) 모양의 numpy 배열(0.0~1.0). 그린 것이 없으면 None
    """
    배열 = np.array(원본_이미지, dtype=np.uint8)

    # 1) 글씨가 있는 영역(0이 아닌 픽셀)의 경계 상자를 찾습니다.
    칠해진_행 = np.where(배열.any(axis=1))[0]
    칠해진_열 = np.where(배열.any(axis=0))[0]
    if len(칠해진_행) == 0 or len(칠해진_열) == 0:
        return None  # 아무것도 그리지 않은 빈 캔버스

    위, 아래 = 칠해진_행[0], 칠해진_행[-1]
    왼쪽, 오른쪽 = 칠해진_열[0], 칠해진_열[-1]
    잘라낸_이미지 = 원본_이미지.crop((왼쪽, 위, 오른쪽 + 1, 아래 + 1))

    # 2) 가로세로 비율을 유지한 채 긴 변이 20픽셀이 되도록 축소합니다.
    너비, 높이 = 잘라낸_이미지.size
    비율 = 20.0 / max(너비, 높이)
    새_너비 = max(1, int(round(너비 * 비율)))
    새_높이 = max(1, int(round(높이 * 비율)))
    축소_이미지 = 잘라낸_이미지.resize((새_너비, 새_높이), Image.LANCZOS)

    # 3) 28x28 검은 도화지 한가운데에 일단 붙입니다.
    도화지 = Image.new("L", (28, 28), 0)
    도화지.paste(축소_이미지, ((28 - 새_너비) // 2, (28 - 새_높이) // 2))

    # 4) 픽셀의 무게중심을 계산해 정확히 중앙(13.5, 13.5)으로 평행 이동합니다.
    도화지_배열 = np.array(도화지, dtype=np.float32)
    전체_밝기 = 도화지_배열.sum()
    if 전체_밝기 > 0:
        행_좌표, 열_좌표 = np.indices(도화지_배열.shape)
        무게중심_y = (행_좌표 * 도화지_배열).sum() / 전체_밝기
        무게중심_x = (열_좌표 * 도화지_배열).sum() / 전체_밝기
        이동_x = int(round(13.5 - 무게중심_x))
        이동_y = int(round(13.5 - 무게중심_y))
        # AFFINE 변환은 '출력 좌표 → 입력 좌표' 방향이라 이동량의 부호가 반대입니다.
        도화지 = 도화지.transform(
            (28, 28), Image.AFFINE, (1, 0, -이동_x, 0, 1, -이동_y), fillcolor=0
        )

    # 5) 0~255 값을 0.0~1.0 으로 바꿔 돌려줍니다. (정규화는 호출한 쪽에서)
    return np.array(도화지, dtype=np.float32) / 255.0


def 작업표시줄_아이디_설정():
    """윈도우가 이 앱을 독립된 프로그램으로 인식하도록 식별자를 등록합니다.

    이 값을 지정하지 않으면 작업 표시줄이 앱을 그냥 '파이썬'으로 취급합니다.
    그러면 바로 가기를 작업 표시줄에 고정해도, 실제로 앱을 실행했을 때
    창이 고정된 아이콘과 묶이지 않고 별도의 단추로 따로 생깁니다.
    바로 가기(.lnk)에도 같은 값을 넣어 두어야 둘이 하나로 묶입니다.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(앱_아이디)
    except Exception:
        pass  # 아이디 등록에 실패해도 앱 동작 자체에는 문제가 없습니다.


class 손글씨인식앱:
    """Tkinter로 만든 그림판 + 숫자 인식 화면."""

    def __init__(self, 루트, 모델, 장치):
        self.루트 = 루트
        self.모델 = 모델
        self.장치 = 장치
        self.이전_좌표 = None  # 마우스를 끄는 동안 직전 점의 위치

        루트.title("손글씨 숫자 인식기")
        루트.resizable(False, False)

        # 창 왼쪽 위와 작업 표시줄에 표시될 아이콘
        if 아이콘_경로.exists():
            try:
                루트.iconbitmap(default=str(아이콘_경로))
            except tk.TclError:
                pass  # 아이콘을 못 읽어도 앱은 그대로 실행합니다.

        전체틀 = tk.Frame(루트, padx=16, pady=16, bg="#f5f5f5")
        전체틀.pack()

        # --- 왼쪽: 그림판 ---
        왼쪽틀 = tk.Frame(전체틀, bg="#f5f5f5")
        왼쪽틀.grid(row=0, column=0, padx=(0, 16), sticky="n")

        tk.Label(왼쪽틀, text="여기에 숫자를 크게 하나 그리세요",
                 font=("맑은 고딕", 11), bg="#f5f5f5").pack(pady=(0, 8))

        self.캔버스 = tk.Canvas(왼쪽틀, width=캔버스_크기, height=캔버스_크기,
                                bg="black", cursor="crosshair", highlightthickness=1,
                                highlightbackground="#888888")
        self.캔버스.pack()

        버튼틀 = tk.Frame(왼쪽틀, bg="#f5f5f5")
        버튼틀.pack(pady=(10, 0))
        tk.Button(버튼틀, text="지우기 (Esc)", width=14, font=("맑은 고딕", 10),
                  command=self.캔버스_비우기).pack(side=tk.LEFT, padx=4)
        tk.Button(버튼틀, text="다시 인식", width=14, font=("맑은 고딕", 10),
                  command=self.인식하기).pack(side=tk.LEFT, padx=4)

        # --- 오른쪽: 인식 결과 ---
        오른쪽틀 = tk.Frame(전체틀, bg="#f5f5f5")
        오른쪽틀.grid(row=0, column=1, sticky="n")

        tk.Label(오른쪽틀, text="인식 결과", font=("맑은 고딕", 11),
                 bg="#f5f5f5").pack(pady=(0, 4))
        self.결과_라벨 = tk.Label(오른쪽틀, text="?", font=("맑은 고딕", 64, "bold"),
                                  fg="#1a1a1a", bg="#f5f5f5", width=2)
        self.결과_라벨.pack()
        self.확신도_라벨 = tk.Label(오른쪽틀, text="숫자를 그려 주세요",
                                    font=("맑은 고딕", 11), fg="#555555", bg="#f5f5f5")
        self.확신도_라벨.pack(pady=(0, 10))

        tk.Label(오른쪽틀, text="숫자별 확률", font=("맑은 고딕", 10),
                 bg="#f5f5f5").pack(anchor="w")

        # 0~9 각각의 확률을 가로 막대로 보여 줍니다.
        self.막대들 = []
        self.확률_라벨들 = []
        for 숫자 in range(10):
            줄 = tk.Frame(오른쪽틀, bg="#f5f5f5")
            줄.pack(anchor="w", pady=1)
            tk.Label(줄, text=str(숫자), font=("Consolas", 10), width=2,
                     bg="#f5f5f5").pack(side=tk.LEFT)
            막대_캔버스 = tk.Canvas(줄, width=140, height=12, bg="#e0e0e0",
                                   highlightthickness=0)
            막대_캔버스.pack(side=tk.LEFT, padx=4)
            막대 = 막대_캔버스.create_rectangle(0, 0, 0, 12, fill="#3b82f6", width=0)
            확률_라벨 = tk.Label(줄, text="0.0%", font=("Consolas", 9), width=6,
                                 anchor="w", bg="#f5f5f5", fg="#555555")
            확률_라벨.pack(side=tk.LEFT)
            self.막대들.append((막대_캔버스, 막대))
            self.확률_라벨들.append(확률_라벨)

        # 실제로 모델에 들어가는 28x28 이미지를 확대해서 보여 주는 미리보기
        tk.Label(오른쪽틀, text="모델이 보는 28x28 이미지", font=("맑은 고딕", 10),
                 bg="#f5f5f5").pack(anchor="w", pady=(10, 2))
        self.미리보기_캔버스 = tk.Canvas(오른쪽틀, width=112, height=112, bg="black",
                                        highlightthickness=1, highlightbackground="#888888")
        self.미리보기_캔버스.pack(anchor="w")

        # 화면에 보이는 캔버스와 똑같은 그림을 PIL 이미지에도 그려 둡니다.
        # (Tkinter 캔버스에서는 픽셀 값을 직접 읽어 올 수 없기 때문입니다)
        self.그림 = Image.new("L", (캔버스_크기, 캔버스_크기), 0)
        self.그리기도구 = ImageDraw.Draw(self.그림)

        # 마우스와 키보드 이벤트 연결
        self.캔버스.bind("<Button-1>", self.그리기_시작)
        self.캔버스.bind("<B1-Motion>", self.그리는_중)
        self.캔버스.bind("<ButtonRelease-1>", self.그리기_끝)
        루트.bind("<Escape>", lambda 이벤트: self.캔버스_비우기())

    # ----- 그리기 관련 -----
    def 점_찍기(self, x, y):
        """지정한 좌표에 붓 굵기만큼의 둥근 점을 화면과 PIL 이미지에 함께 찍습니다."""
        반지름 = 붓_굵기 / 2
        self.캔버스.create_oval(x - 반지름, y - 반지름, x + 반지름, y + 반지름,
                                fill="white", outline="white")
        self.그리기도구.ellipse([x - 반지름, y - 반지름, x + 반지름, y + 반지름], fill=255)

    def 그리기_시작(self, 이벤트):
        self.이전_좌표 = (이벤트.x, 이벤트.y)
        self.점_찍기(이벤트.x, 이벤트.y)  # 점 하나만 찍어도 보이도록

    def 그리는_중(self, 이벤트):
        if self.이전_좌표 is None:
            self.이전_좌표 = (이벤트.x, 이벤트.y)
            return
        현재_좌표 = (이벤트.x, 이벤트.y)
        # 화면과 PIL 이미지에 같은 선을 그립니다.
        self.캔버스.create_line(self.이전_좌표[0], self.이전_좌표[1],
                                현재_좌표[0], 현재_좌표[1], fill="white",
                                width=붓_굵기, capstyle=tk.ROUND, smooth=True)
        self.그리기도구.line([self.이전_좌표, 현재_좌표], fill=255, width=붓_굵기)
        # PIL의 line은 끝을 둥글게 처리하지 않아, 이음매마다 원을 덧그려 줍니다.
        self.점_찍기(현재_좌표[0], 현재_좌표[1])
        self.이전_좌표 = 현재_좌표

    def 그리기_끝(self, 이벤트):
        self.이전_좌표 = None
        self.인식하기()  # 손을 떼면 바로 인식

    def 캔버스_비우기(self):
        """그림판과 결과 표시를 모두 초기 상태로 되돌립니다."""
        self.캔버스.delete("all")
        self.그리기도구.rectangle([0, 0, 캔버스_크기, 캔버스_크기], fill=0)
        self.미리보기_캔버스.delete("all")
        self.결과_라벨.config(text="?", fg="#1a1a1a")
        self.확신도_라벨.config(text="숫자를 그려 주세요")
        for (막대_캔버스, 막대), 확률_라벨 in zip(self.막대들, self.확률_라벨들):
            막대_캔버스.coords(막대, 0, 0, 0, 12)
            확률_라벨.config(text="0.0%", fg="#555555")

    # ----- 인식 관련 -----
    def 인식하기(self):
        """현재 그림을 모델에 넣어 예측 결과를 화면에 표시합니다."""
        정리된_이미지 = 전처리(self.그림)
        if 정리된_이미지 is None:
            return  # 빈 캔버스면 아무것도 하지 않음

        self.미리보기_갱신(정리된_이미지)

        # 학습 때와 똑같이 정규화한 뒤 (1, 1, 28, 28) 모양으로 만듭니다.
        정규화_이미지 = (정리된_이미지 - 평균) / 표준편차
        입력_텐서 = torch.from_numpy(정규화_이미지).unsqueeze(0).unsqueeze(0).to(self.장치)

        with torch.no_grad():
            로그확률 = self.모델(입력_텐서)
            확률 = torch.exp(로그확률)[0].cpu().numpy()  # 로그 확률 → 0~1 확률

        예측_숫자 = int(확률.argmax())
        확신도 = float(확률[예측_숫자]) * 100

        self.결과_라벨.config(text=str(예측_숫자),
                              fg="#1a7f37" if 확신도 >= 60 else "#b45309")
        self.확신도_라벨.config(text=f"확신도 {확신도:.1f}%")

        for 숫자, ((막대_캔버스, 막대), 확률_라벨) in enumerate(zip(self.막대들, self.확률_라벨들)):
            길이 = int(확률[숫자] * 140)
            막대_캔버스.coords(막대, 0, 0, 길이, 12)
            막대_캔버스.itemconfig(막대, fill="#2563eb" if 숫자 == 예측_숫자 else "#93c5fd")
            확률_라벨.config(text=f"{확률[숫자] * 100:4.1f}%",
                             fg="#1a1a1a" if 숫자 == 예측_숫자 else "#888888")

    def 미리보기_갱신(self, 이미지_배열):
        """모델에 들어가는 28x28 이미지를 4배로 키워 미리보기 칸에 그립니다."""
        확대_배열 = np.repeat(np.repeat((이미지_배열 * 255).astype(np.uint8), 4, axis=0), 4, axis=1)
        # PhotoImage는 참조가 사라지면 화면에서 지워지므로 객체에 보관합니다.
        self._미리보기_이미지 = tk.PhotoImage(width=112, height=112)
        # 한 줄씩 넣어야 빠릅니다. (픽셀 하나씩 호출하면 매우 느립니다)
        줄들 = " ".join(
            "{" + " ".join(f"#{값:02x}{값:02x}{값:02x}" for 값 in 행) + "}"
            for 행 in 확대_배열
        )
        self._미리보기_이미지.put(줄들)
        self.미리보기_캔버스.delete("all")
        self.미리보기_캔버스.create_image(0, 0, anchor="nw", image=self._미리보기_이미지)


def 메인():
    if not 가중치_경로.exists():
        print(f"[오류] 가중치 파일을 찾을 수 없습니다: {가중치_경로}")
        print("먼저 'python train.py' 를 실행해 모델을 학습시켜 주세요.")
        임시_루트 = tk.Tk()
        임시_루트.withdraw()
        messagebox.showerror(
            "가중치 없음",
            f"가중치 파일이 없습니다.\n\n{가중치_경로}\n\n"
            "먼저 터미널에서 'python train.py' 를 실행해 주세요.",
        )
        임시_루트.destroy()
        return

    작업표시줄_아이디_설정()  # 창을 만들기 전에 등록해야 효과가 있습니다.

    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"모델을 불러옵니다... (장치: {장치})")
    모델 = 모델_불러오기(가중치_경로, 장치)
    print("준비 완료! 창에 숫자를 그려 보세요.")

    루트 = tk.Tk()
    손글씨인식앱(루트, 모델, 장치)
    루트.mainloop()


if __name__ == "__main__":
    # 더블클릭으로 실행하면 콘솔이 없어서 오류 메시지가 보이지 않습니다.
    # 그래서 예상 못 한 오류는 대화상자로 띄워 줍니다.
    try:
        메인()
    except Exception:
        import traceback
        오류_내용 = traceback.format_exc()
        print(오류_내용)
        try:
            임시_루트 = tk.Tk()
            임시_루트.withdraw()
            messagebox.showerror("오류가 발생했습니다", 오류_내용)
            임시_루트.destroy()
        except Exception:
            pass
        sys.exit(1)
