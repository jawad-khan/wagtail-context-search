"""
RAG answer generation using LLM.
"""

from typing import Any, Dict, List

from wagtail_context_search.backends.llm import get_llm_backend
from wagtail_context_search.core.prompt_templates import PromptTemplate
from wagtail_context_search.settings import get_config


class RAGGenerator:
    """Handles answer generation using RAG pipeline."""

    def __init__(self, config: Dict = None):
        """
        Initialize RAG generator.

        Args:
            config: Configuration dict (uses default if None)
        """
        self.config = config or get_config()
        self.llm = get_llm_backend(
            self.config.get("LLM_BACKEND", "openai"),
            self.config,
        )
        
        # Get prompt template
        template = self.config.get("PROMPT_TEMPLATE")
        if template:
            # If custom template provided, use it
            self.prompt_template = PromptTemplate(user_template=template)
        else:
            self.prompt_template = PromptTemplate()

    def generate_answer(
        self,
        question: str,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate an answer using RAG.

        Args:
            question: User's question
            documents: Retrieved documents

        Returns:
            Dict with 'answer', 'sources', and optionally 'streaming'
        """
        if not documents:
            return {
                "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing it or check if the content has been indexed.",
                "sources": [],
            }

        # Build prompts
        system_prompt, user_prompt = self.prompt_template.build_prompt(
            question, documents
        )

        # Generate answer
        answer = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # Extract sources
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            sources.append({
                "title": metadata.get("title", "Untitled"),
                "url": metadata.get("url", ""),
                "score": doc.get("score", 0.0),
            })

        return {
            "answer": answer,
            "sources": sources,
        }

    def stream_answer(
        self,
        question: str,
        documents: List[Dict[str, Any]],
    ):
        """
        Generate a streaming answer using RAG.

        Args:
            question: User's question
            documents: Retrieved documents

        Yields:
            Chunks of the answer as they are generated
        """
        if not documents:
            yield "I couldn't find any relevant information to answer your question."
            return

        # Build prompts
        system_prompt, user_prompt = self.prompt_template.build_prompt(
            question, documents
        )

        # Stream answer
        for chunk in self.llm.stream_generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
        ):
            yield chunk
