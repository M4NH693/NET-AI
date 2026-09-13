import os
from google import genai


class EmbeddingService:
    @staticmethod
    def _get_client():
        api_key = os.getenv("API_KEY")
        if api_key:
            api_key = api_key.strip().strip("'\"")
        if not api_key:
            raise ValueError("Chưa cấu hình API_KEY trong file .env")
        return genai.Client(api_key=api_key)

    @staticmethod
    async def embed_text(text: str) -> list[float]:
        """
        Embed a single text segment using Gemini's gemini-embedding-2 model.
        Returns a list of 768 floats.
        """
        client = EmbeddingService._get_client()
        response = await client.aio.models.embed_content(
            model="gemini-embedding-2",
            contents=text
        )
        if not response.embeddings or len(response.embeddings) == 0:
            raise Exception("Không lấy được embedding từ Gemini API.")
        return response.embeddings[0].values

    @staticmethod
    async def embed_texts(texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of text segments using Gemini's gemini-embedding-2 model.
        """
        if not texts:
            return []
        client = EmbeddingService._get_client()
        response = await client.aio.models.embed_content(
            model="gemini-embedding-2",
            contents=texts
        )
        if not response.embeddings:
            raise Exception("Không lấy được embeddings từ Gemini API.")
        return [emb.values for emb in response.embeddings]
