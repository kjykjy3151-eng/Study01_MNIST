// 2026-09-21 18:23 KST
//
// 캔버스 입력을 받아 전처리와 추론을 돌리고 결과를 화면에 그립니다.
// DOM 에 의존하는 코드는 이 파일에만 둡니다.

import { 모델_불러오기 } from "./모델.js";
import { 전처리 } from "./전처리.js";

const 캔버스_크기 = 280;   // 28 의 10배
const 붓_굵기 = 22;        // 28x28 로 줄였을 때 MNIST 와 비슷한 두께가 되는 값

const 그림판 = document.getElementById("그림판");
const 그리기 = 그림판.getContext("2d", { willReadFrequently: true });
const 미리보기 = document.getElementById("미리보기");
const 미리보기_그리기 = 미리보기.getContext("2d");
const 결과숫자_요소 = document.getElementById("결과숫자");
const 확신도_요소 = document.getElementById("확신도");
const 막대들_요소 = document.getElementById("막대들");
const 지우기_단추 = document.getElementById("지우기");
const 다시인식_단추 = document.getElementById("다시인식");

let 모델 = null;
let 그리는_중 = false;
let 이전_좌표 = null;

const 막대줄들 = [];
for (let 숫자 = 0; 숫자 < 10; 숫자++) {
    const 줄 = document.createElement("div");
    줄.className = "막대줄";
    줄.innerHTML = `<span class="숫자">${숫자}</span>`
        + `<span class="막대바깥"><span class="막대안"></span></span>`
        + `<span class="값">0.0%</span>`;
    막대들_요소.appendChild(줄);
    막대줄들.push({
        줄,
        막대: 줄.querySelector(".막대안"),
        값: 줄.querySelector(".값"),
    });
}

/** 캔버스를 검게 칠하고 붓 설정을 되돌립니다. */
function 캔버스_초기화() {
    그리기.fillStyle = "#000000";
    그리기.fillRect(0, 0, 캔버스_크기, 캔버스_크기);
    그리기.strokeStyle = "#ffffff";
    그리기.fillStyle = "#ffffff";
    그리기.lineWidth = 붓_굵기;
    그리기.lineCap = "round";
    그리기.lineJoin = "round";
}

/** 화면 좌표를 캔버스 내부 좌표로 바꿉니다.
 *
 * 캔버스가 CSS 로 줄어들어 보일 수 있으므로 비율을 곱해야 합니다.
 */
function 캔버스_좌표(이벤트) {
    const 상자 = 그림판.getBoundingClientRect();
    return {
        x: (이벤트.clientX - 상자.left) * (캔버스_크기 / 상자.width),
        y: (이벤트.clientY - 상자.top) * (캔버스_크기 / 상자.height),
    };
}

function 점_찍기(x, y) {
    그리기.beginPath();
    그리기.arc(x, y, 붓_굵기 / 2, 0, Math.PI * 2);
    그리기.fill();
}

그림판.addEventListener("pointerdown", (이벤트) => {
    if (모델 === null) return;
    그리는_중 = true;
    그림판.setPointerCapture(이벤트.pointerId);
    이전_좌표 = 캔버스_좌표(이벤트);
    점_찍기(이전_좌표.x, 이전_좌표.y);   // 점 하나만 찍어도 보이도록
});

그림판.addEventListener("pointermove", (이벤트) => {
    if (!그리는_중) return;
    const 현재 = 캔버스_좌표(이벤트);
    그리기.beginPath();
    그리기.moveTo(이전_좌표.x, 이전_좌표.y);
    그리기.lineTo(현재.x, 현재.y);
    그리기.stroke();
    이전_좌표 = 현재;
});

function 그리기_끝내기() {
    if (!그리는_중) return;
    그리는_중 = false;
    이전_좌표 = null;
    인식하기();   // 손을 떼면 바로 인식
}

그림판.addEventListener("pointerup", 그리기_끝내기);
그림판.addEventListener("pointercancel", 그리기_끝내기);

지우기_단추.addEventListener("click", 비우기);
다시인식_단추.addEventListener("click", 인식하기);
document.addEventListener("keydown", (이벤트) => {
    // 모델을 아직 못 불러왔을 때는 비우지 않습니다. 비우면 화면에 떠 있는
    // 적재 실패 문구가 "숫자를 그려 주세요." 로 덮여, 앱이 멀쩡해 보이는데
    // 그려도 아무 일이 없는 상태가 됩니다. 지우기 단추도 같은 이유로 꺼 둡니다.
    if (이벤트.key === "Escape" && 모델 !== null) 비우기();
});

/** 그림판과 결과 표시를 처음 상태로 되돌립니다. */
function 비우기() {
    캔버스_초기화();
    미리보기_그리기.clearRect(0, 0, 28, 28);
    결과숫자_요소.textContent = "?";
    결과숫자_요소.className = "결과숫자";
    확신도_요소.textContent = "숫자를 그려 주세요.";
    확신도_요소.className = "확신도";
    for (const { 줄, 막대, 값 } of 막대줄들) {
        줄.classList.remove("으뜸");
        막대.style.width = "0%";
        값.textContent = "0.0%";
    }
}

/** 모델이 보는 28x28 을 미리보기 칸에 그립니다. */
function 미리보기_갱신(이미지) {
    const 화소 = 미리보기_그리기.createImageData(28, 28);
    for (let i = 0; i < 784; i++) {
        const 밝기 = Math.round(이미지[i] * 255);
        화소.data[i * 4] = 밝기;
        화소.data[i * 4 + 1] = 밝기;
        화소.data[i * 4 + 2] = 밝기;
        화소.data[i * 4 + 3] = 255;
    }
    미리보기_그리기.putImageData(화소, 0, 0);
}

/** 현재 그림을 모델에 넣어 결과를 화면에 표시합니다. */
function 인식하기() {
    if (모델 === null) return;

    const 화소 = 그리기.getImageData(0, 0, 캔버스_크기, 캔버스_크기).data;
    const 회색조 = new Uint8Array(캔버스_크기 * 캔버스_크기);
    // 검은 배경에 흰 글씨만 그리므로 빨강 채널 하나만 봐도 충분합니다.
    for (let i = 0; i < 회색조.length; i++) 회색조[i] = 화소[i * 4];

    const 정리된 = 전처리(회색조, 캔버스_크기, 캔버스_크기);
    if (정리된 === null) return;   // 빈 캔버스면 아무것도 하지 않음

    미리보기_갱신(정리된);

    const 입력 = new Float32Array(784);
    for (let i = 0; i < 784; i++) {
        입력[i] = (정리된[i] - 모델.평균) / 모델.표준편차;
    }
    const 확률 = 모델.예측(입력);

    let 예측_숫자 = 0;
    for (let 숫자 = 1; 숫자 < 10; 숫자++) {
        if (확률[숫자] > 확률[예측_숫자]) 예측_숫자 = 숫자;
    }
    const 확신도 = 확률[예측_숫자] * 100;

    결과숫자_요소.textContent = String(예측_숫자);
    결과숫자_요소.className = 확신도 >= 60 ? "결과숫자 확신" : "결과숫자 애매";
    확신도_요소.className = "확신도";
    확신도_요소.textContent = `확신도 ${확신도.toFixed(1)}%`;

    for (let 숫자 = 0; 숫자 < 10; 숫자++) {
        const { 줄, 막대, 값 } = 막대줄들[숫자];
        막대.style.width = `${확률[숫자] * 100}%`;
        값.textContent = `${(확률[숫자] * 100).toFixed(1)}%`;
        줄.classList.toggle("으뜸", 숫자 === 예측_숫자);
    }
}

/** 시작할 때 모델을 내려받습니다. */
async function 시작() {
    캔버스_초기화();
    지우기_단추.disabled = true;
    다시인식_단추.disabled = true;
    try {
        모델 = await 모델_불러오기("가중치/");
        지우기_단추.disabled = false;
        다시인식_단추.disabled = false;
        확신도_요소.textContent = "숫자를 그려 주세요.";
    } catch (오류) {
        확신도_요소.className = "확신도 오류";
        확신도_요소.textContent = `모델을 불러오지 못했습니다. ${오류.message}`;
    }
}

시작();
