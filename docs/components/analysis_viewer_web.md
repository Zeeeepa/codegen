# Analysis Viewer Web Interface

The Analysis Viewer Web Interface provides a browser-based graphical interface for analyzing and comparing codebases. It offers a user-friendly way to access the functionality of the Codebase Analyzer and Codebase Comparator components.

## Overview

The Analysis Viewer Web Interface is built on top of the Codebase Analyzer and Codebase Comparator components, providing a convenient web-based interface for analyzing and comparing codebases. It supports analyzing a single codebase, comparing two codebases, and visualizing the results with interactive charts and graphs.

## Features

- **User-Friendly Interface**: Intuitive web interface for analyzing and comparing codebases
- **Interactive Visualizations**: Dynamic charts and graphs for visualizing analysis and comparison results
- **Repository Management**: Easily manage and switch between repositories
- **Customizable Analysis**: Select specific categories and options for analysis and comparison
- **Result Sharing**: Generate shareable links to analysis and comparison results
- **Export Options**: Export results in multiple formats (JSON, HTML, PDF)
- **Responsive Design**: Works on desktop and mobile devices

## Interface Components

The Analysis Viewer Web Interface consists of the following main components:

1. **Repository Selection**: Select repositories to analyze or compare
2. **Analysis Options**: Configure analysis and comparison options
3. **Results Dashboard**: View analysis and comparison results
4. **Visualization Panel**: Interactive charts and graphs for visualizing results
5. **Export Panel**: Export results in various formats

## Usage Guide

### Launching the Web Interface

The web interface can be launched using the CLI:

```bash
# Launch the web interface
codegen-on-oss web

# Launch the web interface on a specific port
codegen-on-oss web --port 8080

# Launch the web interface on a specific host
codegen-on-oss web --host 0.0.0.0

# Create a shareable link
codegen-on-oss web --share

# Don't open the browser automatically
codegen-on-oss web --no-browser
```

### Analyzing a Codebase

1. Open the web interface in your browser
2. In the Repository Selection panel, enter the URL or path of the repository to analyze
3. Configure analysis options in the Analysis Options panel
4. Click the "Analyze" button
5. View the results in the Results Dashboard and Visualization Panel

### Comparing Codebases

1. Open the web interface in your browser
2. In the Repository Selection panel, enter the URLs or paths of the repositories to compare
3. Configure comparison options in the Analysis Options panel
4. Click the "Compare" button
5. View the comparison results in the Results Dashboard and Visualization Panel

### Sharing Results

1. After analyzing or comparing codebases, click the "Share" button
2. Copy the generated link
3. Share the link with others to allow them to view the results

### Exporting Results

1. After analyzing or comparing codebases, click the "Export" button
2. Select the export format (JSON, HTML, PDF)
3. Click "Download" to download the results in the selected format

## Visualization Types

The Analysis Viewer Web Interface provides various visualization types for different analysis and comparison results:

1. **Bar Charts**: For comparing numerical metrics like file counts, symbol counts, etc.
2. **Pie Charts**: For visualizing distributions like files by language, symbol types, etc.
3. **Network Graphs**: For visualizing dependencies between modules, functions, etc.
4. **Tree Maps**: For visualizing hierarchical data like directory structures, class hierarchies, etc.
5. **Heat Maps**: For visualizing complexity metrics, usage frequency, etc.
6. **Line Charts**: For visualizing trends over time like commit frequency, code growth, etc.
7. **Diff Views**: For visualizing code differences between repositories or branches

## Customization Options

The Analysis Viewer Web Interface provides various customization options:

1. **Theme**: Choose between light and dark themes
2. **Layout**: Customize the layout of the interface
3. **Chart Types**: Select different chart types for visualizations
4. **Color Schemes**: Choose different color schemes for visualizations
5. **Data Filtering**: Filter data shown in visualizations
6. **Sorting Options**: Sort data in different ways

## Troubleshooting

### Common Issues

1. **Web Interface Not Loading**
   - Check that the server is running
   - Ensure the port is not blocked by a firewall
   - Try a different browser

2. **Repository Not Found**
   - Ensure the repository URL or path is correct
   - Check that you have access to the repository

3. **Analysis Taking Too Long**
   - For large codebases, analysis can take time
   - Try analyzing specific categories instead of all categories
   - Reduce the depth of analysis

4. **Visualization Not Rendering**
   - Ensure JavaScript is enabled in your browser
   - Try a different browser
   - Check for console errors in the browser developer tools

5. **Export Failing**
   - Ensure you have a stable internet connection
   - Try a different export format
   - Check for console errors in the browser developer tools

### Error Messages

- **"Repository not found"**: Ensure the repository URL or path is correct
- **"Analysis failed"**: Check the server logs for more information
- **"Visualization error"**: Check the browser console for more information
- **"Export failed"**: Try a different export format or check your internet connection

