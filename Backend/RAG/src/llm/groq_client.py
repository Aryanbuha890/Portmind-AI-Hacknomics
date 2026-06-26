"""
Groq Client Module
====================
Wraps Groq API for answer generation in the RAG pipeline.

Features:
    - Structured output parsing (answer, sources, confidence).
    - Token usage tracking.
"""

import re
from typing import List, Optional, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

from src.llm.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from src.utils.logger import log
from src.utils.config import get_settings


class GroqClient:
    """
    High-level client for Groq-based answer generation.

    Encapsulates prompt formatting, LLM invocation, and response parsing.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialise the Groq LLM client.

        Args:
            model:       Override Groq model name.
            temperature: Override sampling temperature.
            max_tokens:  Override max output tokens.
        """
        settings = get_settings()

        self.model_name = model or settings.groq_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens

        self._llm = ChatGroq(
            model=self.model_name,
            api_key=settings.groq_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=0,
        )

        log.info(
            "GroqClient ready – model={}, temp={}, max_tokens={}",
            self.model_name,
            self.temperature,
            self.max_tokens,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_context(documents: List[Document]) -> str:
        """
        Format retrieved documents into a numbered context block.
        """
        context_parts: List[str] = []
        for i, doc in enumerate(documents, start=1):
            source = doc.metadata.get("source_file", "Unknown")
            page = doc.metadata.get("page", "N/A")
            score = doc.metadata.get("rerank_score", None)
            score_str = f" (relevance: {score:.4f})" if score is not None else ""
            context_parts.append(
                f"[{i}] Source: {source} | Page: {page}{score_str}\n{doc.page_content}"
            )
        return "\n\n".join(context_parts)

    @staticmethod
    def _parse_response(raw_text: str, documents: List[Document]) -> Dict[str, Any]:
        """
        Parse the structured LLM response into a dict.
        """
        answer_match = re.search(
            r"\*\*Answer:\*\*\s*(.*?)(?=\*\*Sources:\*\*|\*\*Confidence:\*\*|$)",
            raw_text,
            re.DOTALL,
        )
        if answer_match:
            answer = answer_match.group(1).strip()
        else:
            answer = raw_text.strip()
            sources_idx = answer.find("**Sources:**")
            if sources_idx != -1:
                answer = answer[:sources_idx].strip()
            
            conf_idx = answer.find("**Confidence:**")
            if conf_idx != -1:
                answer = answer[:conf_idx].strip()

        sources_match = re.search(
            r"\*\*Sources:\*\*\s*(.*?)(?=\*\*Confidence:\*\*|$)",
            raw_text,
            re.DOTALL,
        )
        if sources_match:
            raw_sources = sources_match.group(1).strip()
            sources = [s.strip() for s in raw_sources.split(",") if s.strip()]
        else:
            sources = list(
                {doc.metadata.get("source_file", "Unknown") for doc in documents}
            )

        confidence_match = re.search(
            r"\*\*Confidence:\*\*\s*(High|Medium|Low)",
            raw_text,
            re.IGNORECASE,
        )
        confidence = confidence_match.group(1).capitalize() if confidence_match else "Medium"

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_answer(
        self,
        question: str,
        documents: List[Document],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not documents:
            log.warning("No context documents – generating answer without context.")
            return {
                "answer": (
                    "I don't have enough information in the knowledge base to "
                    "answer this question. Please upload relevant maritime safety "
                    "documents and try again."
                ),
                "sources": [],
                "confidence": "Low",
            }

        context = self._format_context(documents)
        user_prompt = RAG_USER_PROMPT.format(context=context, question=question)
        sys_prompt = system_prompt or RAG_SYSTEM_PROMPT

        log.info("Generating answer for: '{}'", question[:80])

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self._llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            raw_text = "".join(parts)
        else:
            raw_text = str(content)

        log.debug("Raw LLM response length: {} chars", len(raw_text))

        parsed = self._parse_response(raw_text, documents)
        log.info("Answer generated – confidence={}", parsed["confidence"])
        return parsed

    def health_check(self) -> bool:
        """
        Verify that the Groq API key is present.
        """
        settings = get_settings()
        return bool(settings.groq_api_key)
