# Codegen Embedding Provider

This tool allows you to use alternative embedding providers with Codegen's file indexing system. By default, Codegen uses OpenAI's embedding API for semantic code search, but this tool enables you to switch to other providers like DeepSeek.

## Features

- Seamless integration with Codegen's `FileIndex` class
- Support for multiple embedding providers (currently OpenAI and DeepSeek)
- Easy to extend with additional providers
- Simple patching mechanism that doesn't require modifying Codegen's source code

## Installation

1. Ensure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install requests numpy
```

3. Place the `codegen_embedding_provider.py` file in your project directory

## Usage with Codegen

### Basic Usage

```python
from codegen.extensions.index.file_index import FileIndex
from codegen.sdk.core.codebase import Codebase
from codegen_embedding_provider import CodegenEmbeddingManager, patch_codegen_file_index

# Initialize your codebase
codebase = Codebase("/path/to/repo")

# Create a FileIndex instance
file_index = FileIndex(codebase)

# Initialize the embedding manager with your preferred provider
embedding_manager = CodegenEmbeddingManager(
    provider="deepseek",  # or "openai"
    api_key="your_api_key_here"
)

# Patch the FileIndex to use your provider
restore_fn = patch_codegen_file_index(file_index, embedding_manager)

# Now use the FileIndex as normal
file_index.create()  # This will use your specified provider for embeddings
results = file_index.similarity_search("find user authentication code", k=5)

# If needed, restore the original embedding method
restore_fn()
```

### Using with DeepSeek

Since DeepSeek doesn't currently offer a direct embeddings API, the DeepSeek provider will fall back to using OpenAI's API. You'll need to provide an OpenAI API key when using the DeepSeek provider:

```python
# Initialize with DeepSeek but it will use OpenAI for embeddings
embedding_manager = CodegenEmbeddingManager(
    provider="deepseek",
    api_key="your_openai_api_key_here"  # This should be an OpenAI API key
)
```

### Command Line Testing

You can test the embedding functionality directly from the command line:

```bash
python codegen_embedding_provider.py openai "your_openai_api_key" "This is a test text" "text-embedding-3-small"
```

## Adding New Providers

To add support for additional embedding providers:

1. Create a new provider class that inherits from `EmbeddingProvider`
2. Implement the `get_embeddings` method
3. Add the new provider to the `PROVIDERS` dictionary in the `CodegenEmbeddingManager` class

Example:

```python
class CustomEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.custom.com"):
        super().__init__(api_key)
        self.base_url = base_url
        
    def get_embeddings(self, texts: List[str], model: str = None) -> List[List[float]]:
        # Implementation for your custom provider
        pass

# Add to the PROVIDERS dictionary
CodegenEmbeddingManager.PROVIDERS["custom"] = CustomEmbeddingProvider
```

## How It Works

The tool uses a simple patching mechanism to replace Codegen's `_get_embeddings` method in the `FileIndex` class with our own implementation that routes requests through the specified provider. This approach allows you to switch providers without modifying Codegen's source code.

## Limitations

- DeepSeek provider currently falls back to OpenAI since DeepSeek doesn't offer a direct embeddings API
- The patch is temporary and only affects the specific `FileIndex` instance you patch
- You'll need to re-apply the patch if you create a new `FileIndex` instance

## License

MIT

