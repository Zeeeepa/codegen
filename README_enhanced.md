# 🚀 Enhanced Chinese to English Translation Tool

An advanced, multithreaded Python application for translating Chinese code to English with a modern Tkinter GUI. This tool processes entire Python codebases, translating function names, variables, comments, and string literals while preserving code functionality.

## ✨ Key Features

### 🔥 New Enhanced Features
- **10x Multithreaded Processing** - 10 worker threads for parallel translation
- **Large Batch Processing** - Handles 100-500 items per batch for efficiency
- **Modern Tkinter GUI** - User-friendly interface with real-time progress tracking
- **GitHub Integration** - Clone and translate repositories directly from URLs
- **Smart Progress Tracking** - Detailed status logs and statistics display
- **Resume Capability** - Interrupted translations can be resumed
- **Thread-Safe Operations** - Robust concurrent processing with error handling

### 📋 Core Translation Features
- **Comprehensive Chinese Detection** - Function names, variables, comments, strings
- **Intelligent Translation** - CamelCase for identifiers, natural language for text
- **Cache Management** - JSON-based translation cache to avoid re-translation
- **Selective Processing** - Skip system directories and non-Python files
- **Error Recovery** - Graceful handling of API failures and network issues

## 🛠️ Installation & Setup

### Automatic Setup (Recommended)
```bash
# 1. Download the setup script
python setup_enhanced.py
```

This will automatically:
- Check system requirements
- Install Python dependencies  
- Clone the web-ui-python-sdk
- Verify the installation
- Run basic tests

### Manual Setup
```bash
# 1. Clone the web-ui-python-sdk
git clone https://github.com/Zeeeepa/web-ui-python-sdk.git

# 2. Install requirements
pip install requests tqdm tkinter-modern

# 3. Ensure both files are in the same directory:
#    - multiple_language_standalone_enhanced.py
#    - web-ui-python-sdk/ (directory)
```

### System Requirements
- **Python 3.7+**
- **Git** (for repository cloning)
- **Tkinter** (usually included with Python)
- **Internet connection** (for translation API)

#### Platform-Specific Notes:
- **Ubuntu/Debian**: `sudo apt-get install python3-tk git`  
- **macOS**: Usually included with Python
- **Windows**: Included with Python installation

## 🚀 Usage

### Launch the Application
```bash
python multiple_language_standalone_enhanced.py
```

### GUI Interface

#### 📁 Folder Selection
1. Click **"Browse Folder"** to open file explorer
2. Select the Python codebase directory
3. The path will be displayed in the input field

#### 🔗 Repository Selection  
1. Enter a GitHub URL in the **"Repository URL"** field:
   - Full URL: `https://github.com/username/repository`
   - Short format: `username/repository`
   - Example: `binary-husky/gpt_academic`
2. Click **"Clone Repo"** to download and select automatically

#### 🚀 Translation Process
1. After selecting source (folder or repo), click **"Start Translation"**
2. Monitor progress through:
   - **Progress bar** - Overall completion percentage
   - **Status display** - Current operation and statistics  
   - **Log window** - Detailed real-time activity
3. Use **"Cancel"** to stop translation at any time
4. **"Clear"** resets all selections and logs

### Translation Output

The tool creates:
```
source_directory/
source_directory_translated/          # Translated codebase
    _translate_cache.json             # Translation cache
    [all Python files with translations applied]
```

## 🔧 Technical Details

### Multithreading Architecture
- **10 Worker Threads** - Parallel translation processing
- **Large Batches** - 100-500 items per batch for optimal throughput
- **Thread-Safe Operations** - Coordinated cache updates and progress tracking
- **Smart Load Balancing** - Dynamic batch size variation

### Translation Process
1. **Directory Scanning** - Find all Python files, skip blacklisted directories
2. **Chinese Extraction** - Parse AST to identify Chinese content:
   - Function/class names
   - Variable names  
   - Import statements
   - String literals
   - Comments
3. **Cache Loading** - Load existing translations to avoid re-work
4. **Batch Processing** - Group items into large batches for efficiency
5. **Parallel Translation** - Distribute batches across worker threads
6. **Code Application** - Apply translations to create new codebase

### Translation Quality
- **Identifier Translation** - CamelCase naming conventions
- **Text Translation** - Natural language for strings/comments
- **Context Preservation** - Semantic meaning maintained
- **Error Handling** - Failed translations marked for retry

## 📊 Performance & Statistics

### Typical Performance
- **10x Speed Improvement** over single-threaded processing
- **Large Repositories** - Handle 1000+ files efficiently
- **Batch Efficiency** - 100-500 items per API call
- **Resume Capability** - Continue from where you left off

### Progress Tracking
The GUI displays:
- **Real-time Progress** - Completion percentage and current status
- **Detailed Statistics** - Files processed, translations completed, success rates
- **Activity Logs** - Thread activity, batch completion, error reporting  
- **Final Summary** - Complete statistics and output locations

## 🎯 Examples

### Example 1: Translating a Local Project
1. Launch the tool: `python multiple_language_standalone_enhanced.py`
2. Click "Browse Folder" and select your Python project
3. Click "Start Translation"
4. Monitor progress in real-time
5. Find translated code in `project_name_translated/`

### Example 2: Translating from GitHub
1. Launch the application
2. Enter `binary-husky/gpt_academic` in Repository URL field
3. Click "Clone Repo" (downloads automatically)
4. Click "Start Translation" 
5. Access results in `gpt_academic_translated/`

### Example 3: Resume Interrupted Translation
1. If translation was interrupted, simply restart the tool
2. Select the same source directory
3. The cache will be loaded automatically
4. Only untranslated items will be processed

## 🛠️ Troubleshooting

### Common Issues

**"Failed to import web-ui-python-sdk"**
- Ensure the SDK is cloned in the same directory as the script
- Run `python setup_enhanced.py` to verify installation

**"Tkinter not available"**  
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Ensure Python includes tkinter support

**"Git clone failed"**
- Check internet connection
- Verify repository URL format
- Ensure Git is installed: `git --version`

**Translation API Errors**
- Check internet connection
- API may have rate limits - wait and retry
- Some batches may fail but others will continue

**Memory Issues with Large Repositories**
- The tool is optimized for large codebases
- If issues persist, try smaller repositories first
- Monitor system resources during processing

### Debug Mode
For detailed debugging:
1. Check the Status Log in the GUI
2. Look for error messages in the console
3. Verify SDK initialization success
4. Check file permissions for output directory

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional language support
- Alternative translation APIs
- GUI enhancements
- Performance optimizations
- Error handling improvements

## 📄 License

This project builds upon the [web-ui-python-sdk](https://github.com/Zeeeepa/web-ui-python-sdk) which is licensed under MIT License.

## 🙏 Acknowledgments

- **web-ui-python-sdk** by Zeeeepa - Core translation API client
- **Z.AI API** - Translation service
- **Python Community** - Threading, GUI, and parsing libraries

## 📞 Support

For issues and questions:
1. Check this README and troubleshooting section
2. Review the Status Log output for error details
3. Open an issue with:
   - System information (OS, Python version)
   - Error messages from logs
   - Steps to reproduce the issue

---

**Happy Translating! 🎉**