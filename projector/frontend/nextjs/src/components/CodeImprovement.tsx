import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
  IconButton,
  Divider,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface CodeImprovementProps {
  projectId?: string;
}

const CodeImprovement = ({ projectId }: CodeImprovementProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Check file extension
    const validExtensions = ['.py', '.js', '.ts', '.jsx', '.tsx'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      setError(`Invalid file type. Please upload a file with one of these extensions: ${validExtensions.join(', ')}`);
      return;
    }

    // Check file size (200MB limit)
    const maxSize = 200 * 1024 * 1024; // 200MB in bytes
    if (file.size > maxSize) {
      setError(`File size exceeds the 200MB limit.`);
      return;
    }

    setFile(file);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    if (projectId) {
      formData.append('project_id', projectId);
    }

    try {
      const response = await axios.post('/api/code-improvement/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred while analyzing the code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Code Improvement
      </Typography>
      <Typography variant="body1" paragraph>
        Upload a code file to get AI-powered improvement suggestions and automated refactoring.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper
        sx={{
          p: 3,
          mb: 3,
          border: '2px dashed',
          borderColor: dragActive ? 'primary.main' : 'divider',
          backgroundColor: dragActive ? 'rgba(25, 118, 210, 0.08)' : 'background.paper',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 200,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-upload')?.click()}
      >
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".py,.js,.ts,.jsx,.tsx"
        />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Drag and drop file here
        </Typography>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          or click to browse files
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Limit 200MB per file • PY, JS, TS, JSX, TSX
        </Typography>
        {file && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1 }} />
            <Typography variant="body2">{file.name}</Typography>
          </Box>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="contained"
          startIcon={<CloudUploadIcon />}
          onClick={handleUpload}
          disabled={!file || loading}
        >
          {loading ? 'Analyzing...' : 'Analyze Code'}
        </Button>
        <Button variant="outlined" onClick={() => document.getElementById('file-upload')?.click()}>
          Browse files
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {result && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Analysis Results
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Improvement Suggestions
            </Typography>
            <ul>
              {result.suggestions.map((suggestion: any, index: number) => (
                <li key={index}>
                  <Typography variant="body1">{suggestion.description}</Typography>
                  {suggestion.code && (
                    <Box
                      component="pre"
                      sx={{
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '0.875rem',
                        mt: 1,
                      }}
                    >
                      <code>{suggestion.code}</code>
                    </Box>
                  )}
                </li>
              ))}
            </ul>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Refactoring Options
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {result.refactoring_options.map((option: any, index: number) => (
                <Button
                  key={index}
                  variant="outlined"
                  startIcon={<DescriptionIcon />}
                  onClick={() => {
                    // Handle refactoring option
                  }}
                >
                  {option.name}
                </Button>
              ))}
            </Box>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default CodeImprovement;
