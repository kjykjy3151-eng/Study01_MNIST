// 2026-09-21 18:23 KST
//
// 웹 버전 구현이 데스크톱(파이썬) 구현과 같은 답을 내는지 확인합니다.
//
// 실행:
//     node 테스트/검증.mjs
//
// 골든 데이터는 테스트/골든_만들기.py 가 만듭니다.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { 모델_만들기 } from "../js/모델.js";
import { 전처리 } from "../js/전처리.js";

const 기준_폴더 = dirname(fileURLToPath(import.meta.url));
const 골든_폴더 = join(기준_폴더, "골든");
const 가중치_폴더 = join(기준_폴더, "..", "가중치");

const 표본_개수 = 200;

/** 파일을 바이트 배열로 읽습니다. */
function 바이트_읽기(경로) {
    const 버퍼 = readFileSync(경로);
    const 복사본 = new Uint8Array(버퍼.length);
    복사본.set(버퍼);
    return 복사본;
}

/** 파일을 float32 배열로 읽습니다.
 *
 * readFileSync 가 돌려주는 Buffer 는 4바이트 경계에 맞지 않을 수 있어
 * 그대로 Float32Array 로 감싸면 RangeError 가 납니다. 그래서 복사합니다.
 */
function float32_읽기(경로) {
    return new Float32Array(바이트_읽기(경로).buffer);
}

/** 골든 폴더의 파일을 바이트 배열로 읽습니다. */
function 골든_읽기(이름) {
    return 바이트_읽기(join(골든_폴더, 이름));
}

/** 가중치 파일과 구조 정보를 읽어 모델을 만듭니다. */
function 시험용_모델() {
    const 구조 = JSON.parse(readFileSync(join(가중치_폴더, "구조.json"), "utf-8"));
    const 바이트 = 바이트_읽기(join(가중치_폴더, "mnist_cnn.bin"));
    return 모델_만들기(구조, 바이트.buffer);
}

/** 배열에서 가장 큰 값의 위치를 돌려줍니다. */
function 최댓값_위치(배열) {
    let 위치 = 0;
    for (let i = 1; i < 배열.length; i++) if (배열[i] > 배열[위치]) 위치 = i;
    return 위치;
}

test("시험 1: 같은 28x28 입력에서 PyTorch와 같은 확률을 낸다", () => {
    const 모델 = 시험용_모델();
    const 전처리_골든 = 골든_읽기("전처리_28.bin");
    const 확률_골든 = float32_읽기(join(골든_폴더, "확률.bin"));
    const 예측_골든 = 골든_읽기("예측.bin");

    let 최대_오차 = 0;
    for (let 번호 = 0; 번호 < 표본_개수; 번호++) {
        const 입력 = new Float32Array(784);
        for (let i = 0; i < 784; i++) {
            입력[i] = (전처리_골든[번호 * 784 + i] / 255 - 모델.평균) / 모델.표준편차;
        }
        const 확률 = 모델.예측(입력);
        for (let 숫자 = 0; 숫자 < 10; 숫자++) {
            최대_오차 = Math.max(최대_오차, Math.abs(확률[숫자] - 확률_골든[번호 * 10 + 숫자]));
        }
        assert.equal(최댓값_위치(확률), 예측_골든[번호], `${번호}번 표본의 예측이 다릅니다`);
    }
    assert.ok(최대_오차 < 1e-4, `확률 최대 오차가 ${최대_오차} 입니다`);
});

/** 28x28 원본을 최근접 이웃으로 10배 확대해 280x280 캔버스 그림을 만듭니다.
 *
 * 골든_만들기.py 의 np.repeat 두 번과 같은 연산입니다.
 */
function 열배_확대(원본_28) {
    const 확대 = new Uint8Array(280 * 280);
    for (let y = 0; y < 280; y++) {
        for (let x = 0; x < 280; x++) {
            확대[y * 280 + x] = 원본_28[((y / 10) | 0) * 28 + ((x / 10) | 0)];
        }
    }
    return 확대;
}

test("시험 2: 같은 그림에서 파이썬 전처리와 같은 28x28 을 만든다", () => {
    const 원본_골든 = 골든_읽기("원본_28.bin");
    const 전처리_골든 = 골든_읽기("전처리_28.bin");

    let 최대_오차 = 0;
    for (let 번호 = 0; 번호 < 표본_개수; 번호++) {
        const 원본 = 원본_골든.subarray(번호 * 784, (번호 + 1) * 784);
        const 결과 = 전처리(열배_확대(원본), 280, 280);
        assert.ok(결과 !== null, `${번호}번 표본의 전처리 결과가 비었습니다`);
        for (let i = 0; i < 784; i++) {
            const 기대 = 전처리_골든[번호 * 784 + i] / 255;
            최대_오차 = Math.max(최대_오차, Math.abs(결과[i] - 기대));
        }
    }
    assert.ok(최대_오차 < 2 / 255, `픽셀 최대 오차가 ${최대_오차 * 255} (255 기준) 입니다`);
});

test("시험 3: 전처리부터 추론까지 이어 붙여도 예측이 모두 일치한다", () => {
    const 모델 = 시험용_모델();
    const 원본_골든 = 골든_읽기("원본_28.bin");
    const 예측_골든 = 골든_읽기("예측.bin");

    for (let 번호 = 0; 번호 < 표본_개수; 번호++) {
        const 원본 = 원본_골든.subarray(번호 * 784, (번호 + 1) * 784);
        const 정리된 = 전처리(열배_확대(원본), 280, 280);
        const 입력 = new Float32Array(784);
        for (let i = 0; i < 784; i++) {
            입력[i] = (정리된[i] - 모델.평균) / 모델.표준편차;
        }
        assert.equal(
            최댓값_위치(모델.예측(입력)), 예측_골든[번호],
            `${번호}번 표본의 최종 예측이 데스크톱과 다릅니다`
        );
    }
});

test("시험 4: 빈 캔버스는 null 을 돌려준다", () => {
    assert.equal(전처리(new Uint8Array(280 * 280), 280, 280), null);
});

test("시험 5: 점 하나만 찍어도 터지지 않는다", () => {
    const 회색조 = new Uint8Array(280 * 280);
    회색조[140 * 280 + 140] = 255;
    const 결과 = 전처리(회색조, 280, 280);
    assert.ok(결과 !== null);
    assert.equal(결과.length, 784);
    let 합 = 0;
    for (const 값 of 결과) 합 += 값;
    assert.ok(합 > 0, "결과가 전부 0 입니다");
});

test("시험 6: 가로로 길쭉한 획도 짧은 변이 사라지지 않는다", () => {
    const 회색조 = new Uint8Array(280 * 280);
    for (let x = 10; x < 270; x++) 회색조[140 * 280 + x] = 255;
    const 결과 = 전처리(회색조, 280, 280);
    assert.ok(결과 !== null);
    let 합 = 0;
    for (const 값 of 결과) 합 += 값;
    assert.ok(합 > 0, "높이가 0으로 줄어 그림이 사라졌습니다");
});

test("시험 7: 캔버스를 꽉 채워도 결과가 28x28 범위를 벗어나지 않는다", () => {
    const 회색조 = new Uint8Array(280 * 280).fill(255);
    const 결과 = 전처리(회색조, 280, 280);
    assert.ok(결과 !== null);
    assert.equal(결과.length, 784);
    for (const 값 of 결과) {
        assert.ok(값 >= 0 && 값 <= 1, `픽셀 값 ${값} 이 0~1 범위를 벗어났습니다`);
    }
});

export { 바이트_읽기, float32_읽기, 골든_읽기, 시험용_모델, 최댓값_위치, 표본_개수, 골든_폴더 };
