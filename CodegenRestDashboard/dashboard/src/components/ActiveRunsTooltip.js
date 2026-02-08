import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemButton from '@mui/material/ListItemButton';
import Chip from '@mui/material/Chip';
import { formatDistanceToNow } from 'date-fns';

const ActiveRunsTooltip = ({ runs, onRunClick }) => {
  const activeRuns = runs.filter(run =>
    !run.result && (run.status === 'running' || run.status === 'in_progress' || run.status === 'pending')
  );

  if (activeRuns.length === 0) {
    return (
      <Box sx={{ p: 2, minWidth: 200 }}>
        <Typography variant="body2" color="text.secondary">
          No active runs
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2, minWidth: 300, maxWidth: 400 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Active Agent Runs ({activeRuns.length})
      </Typography>

      <List dense>
        {activeRuns.slice(0, 10).map((run) => (
          <ListItem key={run.id} disablePadding>
            <ListItemButton onClick={() => onRunClick(run)}>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      Run #{run.id}
                    </Typography>
                    <Chip
                      label={run.status || 'running'}
                      size="small"
                      color={run.status === 'running' ? 'primary' : 'default'}
                      variant="outlined"
                    />
                  </Box>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    {run.created_at ? formatDistanceToNow(new Date(run.created_at), { addSuffix: true }) : 'Unknown time'}
                  </Typography>
                }
              />
            </ListItemButton>
          </ListItem>
        ))}

        {activeRuns.length > 10 && (
          <ListItem>
            <ListItemText
              primary={
                <Typography variant="caption" color="text.secondary">
                  ... and {activeRuns.length - 10} more
                </Typography>
              }
            />
          </ListItem>
        )}
      </List>
    </Box>
  );
};

export default ActiveRunsTooltip;

