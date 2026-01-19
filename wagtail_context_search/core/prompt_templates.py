"""
Prompt templates for RAG generation.
"""

from typing import Any, Dict, List, Optional, Tuple


class PromptTemplate:
    """Manages prompt templates for RAG."""

    DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant for this website. Your role is to answer questions based on the provided context from the website's content.

Guidelines:
- Answer questions accurately based on the provided context
- If the context doesn't contain enough information, say so
- Cite specific pages or sources when relevant
- Be concise but thorough
- Use a friendly and professional tone"""

    DEFAULT_USER_TEMPLATE = """Context from website:

{context}

Question: {question}

Please provide a helpful answer based on the context above."""

    def __init__(self, system_prompt: Optional[str] = None, user_template: Optional[str] = None):
        """
        Initialize prompt template.

        Args:
            system_prompt: System prompt for the LLM
            user_template: Template for user prompt with {context} and {question} placeholders
        """
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.user_template = user_template or self.DEFAULT_USER_TEMPLATE

    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            documents: List of document dicts with 'text', 'metadata', etc.

        Returns:
            Formatted context string
        """
        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "Untitled")
            url = metadata.get("url", "")
            
            context_parts.append(f"[Source {i}: {title}]")
            if url:
                context_parts.append(f"URL: {url}")
            context_parts.append(f"Content: {doc.get('text', '')}")
            context_parts.append("")  # Empty line between sources

        return "\n".join(context_parts)

    def build_prompt(self, question: str, documents: List[Dict[str, Any]]) -> Tuple[str, str]:
        """
        Build system and user prompts from question and documents.

        Args:
            question: User's question
            documents: Retrieved documents

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        context = self.format_context(documents)
        user_prompt = self.user_template.format(
            context=context,
            question=question,
        )
        return self.system_prompt, user_prompt
