"""
Phase 5: LLM + RAG Chat Engine

Local LLM integration with RAG for analyzing stock data.

TODO: Implement RAG pipeline:
- Embedding generation (local or OpenAI API)
- Vector store (Chroma, Pinecone, etc.)
- Retrieval from financial data
- LLM response generation via Ollama
"""

import ollama


def get_ollama_response(prompt: str, model: str = "mistral") -> str:
    """
    Get response from local Ollama LLM.
    
    Args:
        prompt: User query
        model: Model name (default: mistral)
    
    Returns:
        LLM response text
        
    TODO: Implement Ollama API call
    """
    pass


def retrieve_context(query: str, limit: int = 5) -> list[str]:
    """
    Retrieve relevant data context for RAG.
    
    Args:
        query: User question
        limit: Number of documents to retrieve
    
    Returns:
        List of relevant data contexts
        
    TODO: Implement vector store retrieval
    """
    pass


def chat_with_rag(query: str, model: str = "mistral") -> str:
    """
    Chat interface with RAG on financial data.
    
    Args:
        query: User question
        model: LLM model to use
    
    Returns:
        RAG-enhanced response
        
    TODO: Implement:
    1. Retrieve context from data
    2. Build prompt with context
    3. Get LLM response
    4. Return formatted answer
    """
    pass
