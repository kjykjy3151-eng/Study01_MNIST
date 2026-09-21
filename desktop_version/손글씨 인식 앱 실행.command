#!/bin/bash
# 손글씨 인식 앱 실행기 (macOS / 리눅스)
#
# 파인더에서 이 파일을 더블클릭하면 앱이 실행됩니다.
# 처음 한 번은 실행 권한을 줘야 할 수 있습니다.
#     chmod +x "손글씨 인식 앱 실행.command"

# 이 스크립트가 있는 폴더로 이동합니다. (파인더는 홈 폴더에서 실행하기 때문)
cd "$(dirname "$0")" || exit 1

# 가상환경 파이썬을 찾습니다.
파이썬=""
for 후보 in ".venv/bin/python" ".venv/bin/python3"; do
    if [ -x "$후보" ]; then
        파이썬="$후보"
        break
    fi
done

if [ -z "$파이썬" ]; then
    echo "[오류] 가상환경 .venv 를 찾을 수 없습니다."
    echo "터미널에서 아래 명령으로 먼저 환경을 만들어 주세요."
    echo "    python3 -m venv .venv"
    echo "    .venv/bin/python -m pip install -r requirements.txt"
    echo ""
    echo "창을 닫으려면 아무 키나 누르세요."
    read -r -n 1
    exit 1
fi

if [ ! -f "mnist_cnn.pt" ]; then
    echo "[오류] 학습된 가중치 mnist_cnn.pt 가 없습니다."
    echo "터미널에서 아래 명령으로 먼저 학습해 주세요."
    echo "    .venv/bin/python train.py"
    echo ""
    echo "창을 닫으려면 아무 키나 누르세요."
    read -r -n 1
    exit 1
fi

# 앱을 실행합니다. 터미널 창을 바로 닫아도 앱이 유지되도록 백그라운드로 띄웁니다.
"$파이썬" app.py &

# 파인더에서 실행하면 터미널 창이 함께 열립니다. 잠깐 뒤 스스로 닫히도록 종료합니다.
exit 0
