import React, { useEffect, useState } from 'react';
import Popover from '@mui/material/Popover';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import Checkbox from '@mui/material/Checkbox';
import ListItemText from '@mui/material/ListItemText';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';

const ChainSelector = ({ anchorEl, open, onClose, onApply }) => {
  const [templates, setTemplates] = useState([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState({}); // id -> boolean

  useEffect(() => {
    if (open) {
      try {
        const saved = localStorage.getItem('codegen-templates');
        const list = saved ? JSON.parse(saved) : [];
        setTemplates(list);
      } catch {
        setTemplates([]);
      }
      setQuery('');
      setSelected({});
    }
  }, [open]);

  const filtered = templates.filter((t) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    return (
      (t.name || '').toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q) ||
      (t.prompt || '').toLowerCase().includes(q)
    );
  });

  const toggle = (id) => {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleApply = () => {
    const chosen = templates.filter((t) => selected[t.id]);
    onApply && onApply(chosen);
    onClose && onClose();
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      PaperProps={{ sx: { width: 360, maxHeight: 420 } }}
    >
      <Box sx={{ p: 2, pb: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Add Follow-up Templates
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Selected templates will run sequentially when this run completes.
        </Typography>
        <TextField
          size="small"
          fullWidth
          placeholder="Search templates..."
          sx={{ mt: 1.5 }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </Box>
      <Divider />
      <Box sx={{ px: 1, py: 0.5 }}>
        <List dense sx={{ maxHeight: 260, overflow: 'auto' }}>
          {filtered.length === 0 && (
            <ListItem>
              <ListItemText
                primary={<Typography variant="body2">No templates found</Typography>}
                secondary={<Typography variant="caption">Create templates in the Templates tab</Typography>}
              />
            </ListItem>
          )}
          {filtered.map((t) => (
            <ListItem key={t.id} disablePadding secondaryAction={null} onClick={() => toggle(t.id)}>
              <Checkbox size="small" edge="start" tabIndex={-1} checked={!!selected[t.id]} onChange={() => toggle(t.id)} />
              <ListItemText
                primary={<Typography variant="body2" noWrap>{t.name}</Typography>}
                secondary={
                  <Typography variant="caption" color="text.secondary" noWrap>
                    {t.description || t.prompt}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>
      </Box>
      <Divider />
      <Box sx={{ p: 1.5, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
        <Button onClick={onClose} size="small">Cancel</Button>
        <Button variant="contained" size="small" onClick={handleApply} disabled={Object.values(selected).every((v) => !v)}>
          Apply
        </Button>
      </Box>
    </Popover>
  );
};

export default ChainSelector;

