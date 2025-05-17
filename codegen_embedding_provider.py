#!/usr/bin/env python3
import sys

import requests


class EmbeddingProvider:
    """Base class for embedding providers"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts"""
        msg = "Subclasses must implement get_embeddings"
        raise NotImplementedError(msg)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider implementation"""
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com"):
        super().__init__(api_key)
        self.base_url = base_url

    def get_embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts using OpenAI API"""
        url = f"{self.base_url}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Clean texts
        texts = [text.replace("\\n", " ") for text in texts]

        data = {
            "model": model or "text-embedding-3-small",
            "input": texts
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return [data.get("embedding", []) for data in result.get("data", [])]
        else:
            print(f"Error getting embeddings: {response.status_code}")
            print(f"Details: {response.text}")
            return []


class DeepSeekEmbeddingProvider(EmbeddingProvider):
    """DeepSeek embedding provider implementation"""
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        super().__init__(api_key)
        self.base_url = base_url
        # Since DeepSeek doesn't have a direct embeddings API, we'll use OpenAI as fallback
        self.openai_fallback = OpenAIEmbeddingProvider(api_key, "https://api.openai.com")

    def get_embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts
        Note: This implementation uses OpenAI as a fallback since DeepSeek doesn't offer a direct embeddings API
        """
        print("Warning: DeepSeek doesn't have a direct embeddings API. Using OpenAI as fallback.")
        return self.openai_fallback.get_embeddings(texts, model or "text-embedding-3-small")


class CodegenEmbeddingManager:
    """Manager for embedding providers in Codegen"""

    PROVIDERS = {
        "openai": OpenAIEmbeddingProvider,
        "deepseek": DeepSeekEmbeddingProvider
    }

    def __init__(self, provider: str = "openai", api_key: str | None = None, base_url: str | None = None):
        """Initialize the embedding manager

        Args:
            provider: The embedding provider to use ('openai' or 'deepseek')
            api_key: API key for the provider
            base_url: Base URL for the provider's API (optional)
        """
        if provider not in self.PROVIDERS:
            providers_list = ", ".join(self.PROVIDERS.keys())
            msg = f"Unsupported provider: {provider}. Supported providers: {providers_list}"
            raise ValueError(msg)

        if not api_key:
            msg = "API key is required"
            raise ValueError(msg)

        provider_class = self.PROVIDERS[provider]
        if base_url:
            self.provider = provider_class(api_key, base_url)
        else:
            self.provider = provider_class(api_key)

    def get_embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Get embeddings for a list of texts using the current provider"""
        return self.provider.get_embeddings(texts, model)


# Patch for Codegen's FileIndex class
def patch_codegen_file_index(file_index, embedding_manager, model=None):
    """Patch a Codegen FileIndex instance to use our embedding provider

    Args:
        file_index: The FileIndex instance to patch
        embedding_manager: The CodegenEmbeddingManager instance
        model: The embedding model to use (optional)
    """
    # Store the original _get_embeddings method
    original_get_embeddings = file_index._get_embeddings

    # Define a new _get_embeddings method that uses our provider
    def new_get_embeddings(texts):
        return embedding_manager.get_embeddings(texts, model)

    # Replace the method
    file_index._get_embeddings = new_get_embeddings

    # Return a function to restore the original method if needed
    def restore_original():
        file_index._get_embeddings = original_get_embeddings

    return restore_original


# Example usage
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python codegen_embedding_provider.py [provider] [api_key] [text_to_embed] [model]")
        print("Providers: openai, deepseek")
        sys.exit(1)

    provider = sys.argv[1]
    api_key = sys.argv[2]
    text = sys.argv[3]
    model = sys.argv[4] if len(sys.argv) > 4 else None

    try:
        manager = CodegenEmbeddingManager(provider, api_key)
        embeddings = manager.get_embeddings([text], model)

        if embeddings:
            # Print first 5 dimensions and total dimensions
            first_embedding = embeddings[0]
            print(f"Embedding dimensions: {len(first_embedding)}")
            print(f"First 5 dimensions: {first_embedding[:5]}")
            print("Embedding successfully generated!")
        else:
            print("Failed to generate embedding.")

    except Exception as e:
        print(f"Error: {e!s}")
        sys.exit(1)

