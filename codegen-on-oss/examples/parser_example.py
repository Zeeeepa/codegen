#!/usr/bin/env python3
"""
Example script demonstrating how to use the analyzers.parser module.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from codegen_on_oss.analyzers.parser import (
    TypeScriptParser,
    create_parser,
    parse_code,
    parse_file,
)


def parse_file_example():
    """Example of parsing a file."""
    # Create a sample Python file
    sample_file = Path("sample_code.py")
    with open(sample_file, "w") as f:
        f.write("""
import os
import sys
from pathlib import Path

def hello_world():
    print("Hello, World!")
    return True

class ExampleClass:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print(f"Hello, {self.name}!")
        return self.name
""")

    try:
        # Parse the file
        print(f"Parsing file: {sample_file}")
        ast = parse_file(sample_file)

        # Get symbols
        parser = create_parser("python")
        symbols = parser.get_symbols(ast)

        print(f"\nSymbols found ({len(symbols)}):")
        for symbol in symbols:
            if symbol["type"] == "class":
                print(
                    f"  Class: {symbol['name']} with methods: {', '.join(symbol['methods'])}"
                )
            elif symbol["type"] == "function":
                print(f"  Function: {symbol['name']}")
            elif symbol["type"] == "variable":
                print(f"  Variable: {symbol['name']}")

        # Get dependencies
        dependencies = parser.get_dependencies(ast)

        print(f"\nDependencies found ({len(dependencies)}):")
        for dep in dependencies:
            if dep["type"] == "import":
                if "alias" in dep:
                    print(f"  import {dep['module']} as {dep['alias']}")
                else:
                    print(f"  import {dep['module']}")
            elif dep["type"] == "from_import":
                print(f"  from {dep['module']} import {dep['name']}")

    finally:
        # Clean up
        if sample_file.exists():
            sample_file.unlink()


def parse_code_example():
    """Example of parsing code directly."""
    # Sample JavaScript code
    js_code = """
import { useState } from 'react';
import axios from 'axios';

function FetchData() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchData = async (url) => {
        try {
            setLoading(true);
            const response = await axios.get(url);
            setData(response.data);
            setError(null);
        } catch (err) {
            setError(err.message);
            setData(null);
        } finally {
            setLoading(false);
        }
    };

    return { data, loading, error, fetchData };
}

class DataProvider {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl
        });
    }

    async get(endpoint) {
        return await this.client.get(endpoint);
    }
}

export { FetchData, DataProvider };
"""

    # Parse the code
    print("\nParsing JavaScript code:")
    ast = parse_code(js_code, "javascript", "example.js")

    # Get symbols
    parser = create_parser("javascript")
    symbols = parser.get_symbols(ast)

    print(f"\nSymbols found ({len(symbols)}):")
    for symbol in symbols:
        if symbol["type"] == "class":
            print(
                f"  Class: {symbol['name']} with methods: {', '.join(symbol['methods'])}"
            )
        elif symbol["type"] == "function":
            print(f"  Function: {symbol['name']}")
        elif symbol["type"] == "variable":
            print(f"  Variable: {symbol['name']}")

    # Get dependencies
    dependencies = parser.get_dependencies(ast)

    print(f"\nDependencies found ({len(dependencies)}):")
    for dep in dependencies:
        if dep["type"] == "import":
            if "alias" in dep:
                print(f"  import {dep['module']} as {dep['alias']}")
            else:
                print(f"  import {dep['module']}")
        elif dep["type"] == "from_import":
            print(f"  from {dep['module']} import {dep['name']}")


def language_specific_parsers_example():
    """Example of using language-specific parsers."""
    # Sample TypeScript code
    ts_code = """
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface User {
    id: number;
    name: string;
    email: string;
}

@Component({
    selector: 'app-user-list',
    templateUrl: './user-list.component.html'
})
export class UserListComponent {
    users: User[] = [];
    loading: boolean = false;

    constructor(private http: HttpClient) {}

    ngOnInit(): void {
        this.getUsers();
    }

    getUsers(): void {
        this.loading = true;
        this.http.get<User[]>('/api/users')
            .subscribe({
                next: (data) => {
                    this.users = data;
                    this.loading = false;
                },
                error: (err) => {
                    console.error('Error fetching users', err);
                    this.loading = false;
                }
            });
    }
}
"""

    # Parse with TypeScript parser
    print("\nParsing TypeScript code with TypeScriptParser:")
    parser = TypeScriptParser()
    ast = parser.parse_code(ts_code, "example.ts")

    # Get symbols
    symbols = parser.get_symbols(ast)

    print(f"\nSymbols found ({len(symbols)}):")
    for symbol in symbols:
        if symbol["type"] == "class":
            print(
                f"  Class: {symbol['name']} with methods: {', '.join(symbol['methods'])}"
            )
        elif symbol["type"] == "function":
            print(f"  Function: {symbol['name']}")
        elif symbol["type"] == "variable":
            print(f"  Variable: {symbol['name']}")

    # Get dependencies
    dependencies = parser.get_dependencies(ast)

    print(f"\nDependencies found ({len(dependencies)}):")
    for dep in dependencies:
        if dep["type"] == "import":
            if "alias" in dep:
                print(f"  import {dep['module']} as {dep['alias']}")
            else:
                print(f"  import {dep['module']}")
        elif dep["type"] == "from_import":
            print(f"  from {dep['module']} import {dep['name']}")


if __name__ == "__main__":
    print("=== Parser Examples ===")
    parse_file_example()
    parse_code_example()
    language_specific_parsers_example()
    print("\nAll examples completed successfully!")
