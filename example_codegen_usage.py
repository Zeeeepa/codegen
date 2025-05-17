#!/usr/bin/env python3
"""Example script showing how to use the CodegenEmbeddingProvider with Codegen's FileIndex"""

import argparse
import sys

from codegen_embedding_provider import CodegenEmbeddingManager, patch_codegen_file_index

# This example assumes you have Codegen installed
try:
    from codegen.extensions.index.file_index import FileIndex
    from codegen.sdk.core.codebase import Codebase
except ImportError:
    print("Error: Codegen package not found. Please install it first.")
    print("You can install it with: pip install codegen")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Example of using alternative embedding providers with Codegen")
    parser.add_argument("--repo-path", required=True, help="Path to the repository to index")
    parser.add_argument("--provider", choices=["openai", "deepseek"], default="openai", help="Embedding provider to use")
    parser.add_argument("--api-key", required=True, help="API key for the provider")
    parser.add_argument("--model", help="Embedding model to use (optional)")
    parser.add_argument("--query", help="Search query (if not provided, only indexing will be performed)")
    parser.add_argument("--results", type=int, default=5, help="Number of results to return")

    args = parser.parse_args()

    # Initialize Codegen codebase
    print(f"Initializing codebase from: {args.repo_path}")
    codebase = Codebase(args.repo_path)

    # Create FileIndex
    print("Creating FileIndex instance")
    file_index = FileIndex(codebase)

    # Initialize embedding manager
    print(f"Initializing embedding manager with provider: {args.provider}")
    embedding_manager = CodegenEmbeddingManager(
        provider=args.provider,
        api_key=args.api_key
    )

    # Patch the FileIndex
    print("Patching FileIndex to use custom embedding provider")
    restore_fn = patch_codegen_file_index(file_index, embedding_manager, args.model)

    try:
        # Create the index
        print("Creating index (this may take a while for large codebases)...")
        file_index.create()

        # Save the index
        print("Saving index...")
        file_index.save()

        # Perform search if query is provided
        if args.query:
            print(f"Searching for: {args.query}")
            results = file_index.similarity_search(args.query, k=args.results)

            print(f"\nTop {len(results)} results:")
            print("-" * 80)
            for i, (file, score) in enumerate(results, 1):
                print(f"{i}. {file.filepath} (Score: {score:.4f})")
                print(f"   {file.language}, {len(file.content)} bytes")
                # Print a snippet of the file content (first 100 chars)
                content_preview = file.content[:100].replace("\n", " ")
                print(f"   Preview: {content_preview}...")
                print()

    finally:
        # Restore original method
        print("Restoring original FileIndex method")
        restore_fn()

    print("Done!")


if __name__ == "__main__":
    main()

