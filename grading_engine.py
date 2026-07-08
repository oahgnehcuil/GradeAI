import os
import sys
import time
from dotenv import load_dotenv

# 所有 API 與環境變數的黑魔法設定，完全收容在後端引擎
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"
sys.modules['trio'] = None

from openai import OpenAI

class GradingEngine:
    def __init__(self):
        """初始化引擎時，自動從系統環境變數讀取 API Key"""
        load_dotenv()
        api_key = os.environ.get("GCP_API_KEY")
        
        if not api_key:
            raise ValueError("❌ 系統找不到環境變數 `GCP_API_KEY`，請確保已在伺服器或電腦中設定。")
            
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key
        )
        self.model_name = "gemini-2.5-flash"

    def _call_gemini_with_retry(self, messages: list, max_retries: int = 5) -> str:
        """核心呼叫函式，內建自動重試機制"""
        delay = 2
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(delay)
                delay *= 2
        return ""

    def run_ocr(self, base64_images: list) -> str:
        """多模態文字辨識 (OCR)"""
        content_list = [
            {
                "type": "text",
                "text": "請幫我辨識這些圖片中的所有文字。如果裡面包含數學公式，請將數學公式轉換為標準的 LaTeX 格式輸出。"
            }
        ]
        for b64_str in base64_images:
            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_str}"}
            })
        messages = [{"role": "user", "content": content_list}]
        return self._call_gemini_with_retry(messages)

    def grade_answer(self, student_id: str, student_answer: str, exam_question: str, rubric: str) -> str:
        """依據題目與評分標準進行批改"""
        system_prompt = "你是一位嚴格且公平的老師。請根據提供的「考試題目」與「參考答案與評分標準」，對學生的作答內容進行批改，給出每題得分、扣分原因，以及總分。"
        user_content = f"""
【考試題目】
{exam_question}

【參考答案與評分標準】
{rubric}

--------------------------------------------------
【學生作答內容 (學號: {student_id})】
{student_answer}
--------------------------------------------------

請依據上述標準進行批改，並用以下格式輸出：
1. 每題得分與詳細評語（指出錯誤在哪裡，若使用 LaTeX 公式請以 $ 包覆）
2. 總分：XX / 總滿分
3. 給學生的鼓勵或建議
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        return self._call_gemini_with_retry(messages)