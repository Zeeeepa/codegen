import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Chip from '@mui/material/Chip';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const TemplatesTab = () => {
  const [templates, setTemplates] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt: '',
    trigger_condition: 'completion', // 'completion', 'failure', 'always'
    variables: ''
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = () => {
    // Load from localStorage for now
    const saved = localStorage.getItem('codegen-templates');
    if (saved) {
      try {
        setTemplates(JSON.parse(saved));
      } catch (error) {
        console.error('Failed to load templates:', error);
      }
    }
  };

  const saveTemplates = (newTemplates) => {
    localStorage.setItem('codegen-templates', JSON.stringify(newTemplates));
    setTemplates(newTemplates);
  };

  const handleOpenDialog = (template = null) => {
    if (template) {
      setEditingTemplate(template);
      setFormData({
        name: template.name || '',
        description: template.description || '',
        prompt: template.prompt || '',
        trigger_condition: template.trigger_condition || 'completion',
        variables: template.variables ? JSON.stringify(template.variables, null, 2) : ''
      });
    } else {
      setEditingTemplate(null);
      setFormData({
        name: '',
        description: '',
        prompt: '',
        trigger_condition: 'completion',
        variables: ''
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingTemplate(null);
  };

  const handleSaveTemplate = () => {
    if (!formData.name.trim() || !formData.prompt.trim()) {
      toast.error('Name and prompt are required');
      return;
    }

    let variables = {};
    if (formData.variables.trim()) {
      try {
        variables = JSON.parse(formData.variables);
      } catch (error) {
        toast.error('Invalid JSON in variables field');
        return;
      }
    }

    const template = {
      id: editingTemplate ? editingTemplate.id : Date.now().toString(),
      name: formData.name.trim(),
      description: formData.description.trim(),
      prompt: formData.prompt.trim(),
      trigger_condition: formData.trigger_condition,
      variables,
      created_at: editingTemplate ? editingTemplate.created_at : new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    let newTemplates;
    if (editingTemplate) {
      newTemplates = templates.map(t => t.id === editingTemplate.id ? template : t);
      toast.success('Template updated successfully');
    } else {
      newTemplates = [...templates, template];
      toast.success('Template created successfully');
    }

    saveTemplates(newTemplates);
    handleCloseDialog();
  };

  const handleDeleteTemplate = (templateId) => {
    const newTemplates = templates.filter(t => t.id !== templateId);
    saveTemplates(newTemplates);
    toast.success('Template deleted successfully');
  };

  const getTriggerConditionColor = (condition) => {
    switch (condition) {
      case 'completion':
        return 'success';
      case 'failure':
        return 'error';
      case 'always':
        return 'primary';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Prompt Templates
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Template
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Create and manage prompt templates for chained agent runs. Templates can be triggered
        automatically when agent runs complete, allowing for multi-step workflows.
      </Typography>

      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {template.name}
                </Typography>

                {template.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                )}

                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip
                    label={template.trigger_condition}
                    size="small"
                    color={getTriggerConditionColor(template.trigger_condition)}
                    variant="outlined"
                  />
                </Box>

                <Typography variant="body2" sx={{ mb: 1 }}>
                  Prompt: {template.prompt.length > 100 ? `${template.prompt.substring(0, 100)}...` : template.prompt}
                </Typography>

                {template.variables && Object.keys(template.variables).length > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Variables: {Object.keys(template.variables).join(', ')}
                  </Typography>
                )}

                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  Updated {format(new Date(template.updated_at), 'PP')}
                </Typography>
              </CardContent>

              <CardActions>
                <IconButton onClick={() => handleOpenDialog(template)}>
                  <EditIcon />
                </IconButton>
                <IconButton onClick={() => handleDeleteTemplate(template.id)} color="error">
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {templates.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No templates created yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Create your first prompt template to enable chained agent runs
          </Typography>
        </Box>
      )}

      {/* Template Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingTemplate ? 'Edit Template' : 'Create New Template'}
        </DialogTitle>

        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <TextField
              label="Template Name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
              fullWidth
            />

            <TextField
              label="Description (Optional)"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              multiline
              rows={2}
              fullWidth
            />

            <TextField
              label="Prompt Template"
              value={formData.prompt}
              onChange={(e) => setFormData(prev => ({ ...prev, prompt: e.target.value }))}
              multiline
              rows={6}
              required
              placeholder="Enter the prompt template. Use {{variable}} syntax for dynamic values."
              fullWidth
            />

            <FormControl fullWidth>
              <InputLabel>Trigger Condition</InputLabel>
              <Select
                value={formData.trigger_condition}
                onChange={(e) => setFormData(prev => ({ ...prev, trigger_condition: e.target.value }))}
                label="Trigger Condition"
              >
                <MenuItem value="completion">On Completion</MenuItem>
                <MenuItem value="failure">On Failure</MenuItem>
                <MenuItem value="always">Always</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Variables (JSON, Optional)"
              value={formData.variables}
              onChange={(e) => setFormData(prev => ({ ...prev, variables: e.target.value }))}
              multiline
              rows={3}
              placeholder='{"run_id": "{{run_id}}", "result": "{{result}}"}'
              fullWidth
              helperText="JSON object defining variables available in the prompt template"
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveTemplate} variant="contained">
            {editingTemplate ? 'Update' : 'Create'} Template
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TemplatesTab;

