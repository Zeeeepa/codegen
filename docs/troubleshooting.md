# Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using the Codebase Analysis Viewer.

## Installation Issues

### Package Not Found

**Issue**: `pip install codegen-on-oss` fails with "Package not found" error.

**Solution**:
- Ensure you're using the correct package name
- Check your internet connection
- Try updating pip: `pip install --upgrade pip`
- If installing from source, ensure you're in the correct directory

### Dependency Conflicts

**Issue**: Installation fails due to dependency conflicts.

**Solution**:
- Create a virtual environment: `python -m venv venv`
- Activate the virtual environment:
  - Windows: `venv\Scripts\activate`
  - Unix/MacOS: `source venv/bin/activate`
- Install the package in the virtual environment

### Permission Errors

**Issue**: Installation fails due to permission errors.

**Solution**:
- Use `pip install --user codegen-on-oss` to install for the current user only
- On Unix/MacOS, use `sudo pip install codegen-on-oss` (not recommended)
- Use a virtual environment as described above

## Repository Access Issues

### Repository Not Found

**Issue**: Analysis fails with "Repository not found" error.

**Solution**:
- Ensure the repository URL is correct
- Check that you have access to the repository
- For private repositories, ensure you have the necessary credentials
- For GitHub repositories, check that the GitHub API token has the necessary permissions

### Authentication Issues

**Issue**: Analysis fails with authentication errors.

**Solution**:
- Ensure you have the necessary credentials
- For GitHub repositories, check that your GitHub API token is valid
- For private repositories, ensure you have the necessary permissions
- Check your network connection

### Rate Limiting

**Issue**: Analysis fails due to GitHub API rate limiting.

**Solution**:
- Use a GitHub API token to increase rate limits
- Wait for rate limits to reset
- Reduce the number of repositories being analyzed
- Use local repositories instead of remote ones

## Analysis Issues

### Memory Issues

**Issue**: Analysis fails due to memory errors.

**Solution**:
- Analyze specific categories instead of all categories
- Reduce the depth of analysis
- Analyze smaller repositories
- Increase available memory
- Use a machine with more memory

### Slow Analysis

**Issue**: Analysis takes a long time to complete.

**Solution**:
- Analyze specific categories instead of all categories
- Reduce the depth of analysis
- Analyze smaller repositories
- Use a faster machine
- Use local repositories instead of remote ones

### Language Detection Issues

**Issue**: Analysis fails to detect the correct language.

**Solution**:
- Specify the language explicitly using the `--language` parameter
- Ensure the repository contains files in the expected language
- Check that the language is supported by the Codebase Analysis Viewer

### Import Resolution Issues

**Issue**: Analysis fails due to import resolution errors.

**Solution**:
- Ensure the repository is complete and contains all necessary files
- Check that the repository structure is correct
- For Python repositories, ensure that all dependencies are available
- Use the `--allow-external` parameter to allow external dependencies

## Comparison Issues

### Branch Not Found

**Issue**: Comparison fails with "Branch not found" error.

**Solution**:
- Ensure the branch name is correct
- Check that the branch exists in the repository
- For GitHub repositories, ensure you have access to the branch

### Comparison Takes Too Long

**Issue**: Comparison takes a long time to complete.

**Solution**:
- Compare specific categories instead of all categories
- Reduce the depth of comparison
- Compare smaller repositories
- Use a faster machine
- Use local repositories instead of remote ones

### Comparison Results Unexpected

**Issue**: Comparison results are not what you expected.

**Solution**:
- Check that you're comparing the correct repositories or branches
- Ensure that the repositories or branches have the expected differences
- Try comparing specific categories to focus on particular aspects
- Check the comparison parameters

## CLI Issues

### Command Not Found

**Issue**: `codegen-on-oss` command not found.

**Solution**:
- Ensure the package is installed correctly
- Check that the command is in your PATH
- Try using `python -m codegen_on_oss` instead
- If installed in a virtual environment, ensure the environment is activated

### Invalid Options

**Issue**: CLI reports invalid options.

**Solution**:
- Check the command syntax and options
- Use the help command for more information: `codegen-on-oss --help`
- Ensure you're using the correct version of the tool

### Output Format Issues

**Issue**: Output is not in the expected format.

**Solution**:
- Ensure the output format is one of: json, html, console
- Check that you have write access to the output file location
- Try a different output format

## Web Interface Issues

### Web Interface Not Loading

**Issue**: Web interface doesn't load in the browser.

**Solution**:
- Check that the server is running
- Ensure the port is not blocked by a firewall
- Try a different browser
- Check the server logs for errors

### Port Already in Use

**Issue**: Web interface fails to start due to port already in use.

**Solution**:
- Choose a different port: `codegen-on-oss web --port 8080`
- Find and stop the process using the port
- Restart your computer

### Visualization Not Rendering

**Issue**: Visualizations don't render in the web interface.

**Solution**:
- Ensure JavaScript is enabled in your browser
- Try a different browser
- Check for console errors in the browser developer tools
- Ensure you have a stable internet connection

## Common Error Messages

### "Repository not found"

**Cause**: The repository URL is incorrect or you don't have access to the repository.

**Solution**:
- Check the repository URL
- Ensure you have access to the repository
- For private repositories, ensure you have the necessary credentials

### "Branch not found"

**Cause**: The branch name is incorrect or the branch doesn't exist.

**Solution**:
- Check the branch name
- Ensure the branch exists in the repository
- For GitHub repositories, ensure you have access to the branch

### "Language not supported"

**Cause**: The specified language is not supported by the Codebase Analysis Viewer.

**Solution**:
- Check the supported languages
- Use a supported language
- If the language should be supported, check for typos

### "Analysis failed"

**Cause**: The analysis failed for various reasons.

**Solution**:
- Check the error message for more details
- Check the logs for more information
- Try analyzing specific categories instead of all categories
- Try reducing the depth of analysis

### "Comparison failed"

**Cause**: The comparison failed for various reasons.

**Solution**:
- Check the error message for more details
- Check the logs for more information
- Try comparing specific categories instead of all categories
- Try reducing the depth of comparison

## Getting Help

If you're still experiencing issues after trying the solutions in this guide, you can:

1. Check the [GitHub repository](https://github.com/username/codegen-on-oss) for known issues
2. Open a new issue on GitHub with details about your problem
3. Contact the maintainers for support
4. Check the documentation for more information

