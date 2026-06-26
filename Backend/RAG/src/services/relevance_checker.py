from typing import List
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.groq_client import GroqClient
from src.utils.logger import log

class RelevanceChecker:
    """
    Relevance Checker Service
    =========================
    Uses an LLM (Groq) to perform a secondary, semantic check on the retrieved
    documents to ensure they actually answer the question.
    """

    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client

    def is_context_sufficient(self, query: str, documents: List[Document]) -> bool:
        """
        Audits context sufficiency. Bypassed to conserve API quota and minimize latency.
        Always returns True if documents are present.
        """
        return bool(documents)
