import React, { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import { createAgentRun } from '../services/apiService';
import toast from 'react-hot-toast';

const MODEL_OPTIONS = [
  'Sonnet 4.5',
  'GPT-5',
  'GPT 5 Codex',
  'Claude opus 4.5',
  'Grok 4',
  'Grok 4 Fast reasoning',
  'Grok Code Fast 1'
];

const AGENT_TYPE_OPTIONS = [
  { value: 'codegen', label: 'Codegen' },
  { value: 'claude_code', label: 'Claude Code' }
];

const NewRunForm = ({ open, onClose, onRunCreated }) => {
  const [formData, setFormData] = useState({
    prompt: '',
    model: '',
    agent_type: 'codegen',
    repo_id: '',
    metadata: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (event) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!formData.prompt.trim()) {
      toast.error('Prompt is required');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        prompt: formData.prompt.trim(),
        agent_type: formData.agent_type
      };

      if (formData.model) {
        payload.model = formData.model;
      }

      if (formData.repo_id) {
        payload.repo_id = parseInt(formData.repo_id);
      }

      if (formData.metadata.trim()) {
        try {
          payload.metadata = JSON.parse(formData.metadata);
        } catch (error) {
          toast.error('Invalid JSON in metadata field');
          setLoading(false);
          return;
        }
      }

      const newRun = await createAgentRun(payload);
      onRunCreated(newRun);

      // Reset form
      setFormData({
        prompt: '',
        model: '',
        agent_type: 'codegen',
        repo_id: '',
        metadata: ''
      });

    } catch (error) {
      console.error('Failed to create run:', error);
      toast.error(`Failed to create agent run: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          Create New Agent Run
        </DialogTitle>

        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <TextField
              label="Prompt"
              multiline
              rows={4}
              value={formData.prompt}
              onChange={handleChange('prompt')}
              required
              placeholder="Describe what you want the agent to do..."
              fullWidth
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Model (Optional)</InputLabel>
                <Select
                  value={formData.model}
                  onChange={handleChange('model')}
                  label="Model (Optional)"
                >
                  <MenuItem value="">
                    <em>Use organization default</em>
                  </MenuItem>
                  {MODEL_OPTIONS.map((model) => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Agent Type</InputLabel>
                <Select
                  value={formData.agent_type}
                  onChange={handleChange('agent_type')}
                  label="Agent Type"
                >
                  {AGENT_TYPE_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <TextField
              label="Repository ID (Optional)"
              type="number"
              value={formData.repo_id}
              onChange={handleChange('repo_id')}
              placeholder="Numeric repository ID"
              fullWidth
            />

            <TextField
              label="Metadata (JSON, Optional)"
              multiline
              rows={2}
              value={formData.metadata}
              onChange={handleChange('metadata')}
              placeholder='{"key": "value"}'
              fullWidth
              helperText="Additional JSON metadata to store with the run"
            />

            <Typography variant="body2" color="text.secondary">
              Note: The agent run will execute asynchronously. You can monitor its progress
              in the dashboard and view results once completed.
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !formData.prompt.trim()}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            {loading ? 'Creating...' : 'Create Run'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default NewRunForm;

