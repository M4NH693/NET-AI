import os
from google import genai
from google.genai import types
from app.services.llm.base import BaseLLM

class GeminiLLM(BaseLLM):
    async def generate_response(self, contents: list[dict], system_instruction: str) -> tuple[str, int | None]:
        """
        Call Google Gemini API asynchronously using the new google-genai SDK.
        """
        api_key = os.getenv("API_KEY")
        if api_key:
            api_key = api_key.strip().strip("'\"")
            
        if not api_key or api_key == "your_gemini_api_key_here" or not api_key.strip():
            warning_text = (
                "⚠️ **Cảnh báo từ hệ thống:** Chưa cấu hình Gemini API Key hoặc khóa không hợp lệ.\n\n"
                "Vui lòng thiết lập biến `API_KEY` hợp lệ trong tệp `.env` ở thư mục gốc của dự án để bắt đầu trò chuyện với Trợ lý AI:\n"
                "```env\nAPI_KEY=AIzaSy...\n```\n\n"
                "*Lưu ý: Nếu bạn vừa thêm API Key, hãy nhớ khởi động lại máy chủ Uvicorn để nạp lại cấu hình.*"
            )
            return warning_text, None

        # 1. Map standard roles (user/assistant) to Gemini API roles (user/model)
        gemini_contents = []
        for msg in contents:
            gemini_role = "model" if msg["role"] == "assistant" else "user"
            gemini_contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # 2. Configure generate content settings
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )

        try:
            # 3. Initialize client and make async call via client.aio
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=gemini_contents,
                config=config
            )
            
            # 4. Parse text response and actual token usage from metadata
            ai_text = response.text or "Không nhận được phản hồi từ AI."
            actual_tokens = None
            if response.usage_metadata:
                # candidates_token_count is the token count of the generated response
                actual_tokens = response.usage_metadata.candidates_token_count
                
            return ai_text, actual_tokens
            
        except Exception as e:
            error_text = f"❌ **Lỗi gọi Gemini API:** {str(e)}"
            return error_text, None
