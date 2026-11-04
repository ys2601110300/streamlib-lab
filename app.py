# ============================================================
# [실습 5-1] 퀴즈 JSON 먼저 눈으로 보기 — Colab 에서 실행 (요청 1번)
# ------------------------------------------------------------
# client 는 실습 0-1 셀에서 만든 것을 그대로 씁니다 (런타임이 끊겼으면 0-1 부터 다시)
# ============================================================
import json

# 문제 하나 = 질문 · 보기 4개 · 정답 번호(0~3) · 해설
QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "choices": {"type": "array", "items": {"type": "string"}, "description": "보기 4개"},
                    "answer_index": {"type": "integer", "description": "정답 보기의 번호 (0부터 셈)"},
                    "explanation": {"type": "string", "description": "정답 해설 한 문장"},
                },
                "required": ["question", "choices", "answer_index", "explanation"],
            },
        }
    },
    "required": ["questions"],
}

reply = client.interactions.create(
    model="gemini-3.5-flash-lite",
    store=False,
    input="주제 '파이썬 리스트' 에 대해 쉬움 난이도 문제 2개를 만들어 줘.",
    response_format={"type": "text", "mime_type": "application/json", "schema": QUIZ_SCHEMA},
)
quiz = json.loads(reply.output_text)                      # JSON 글 → 파이썬 딕셔너리
print(json.dumps(quiz, ensure_ascii=False, indent=2))     # 보기 좋게 찍기
