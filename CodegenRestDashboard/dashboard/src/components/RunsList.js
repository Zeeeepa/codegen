import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import PushPinIcon from '@mui/icons-material/PushPin';
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined';
import SubjectIcon from '@mui/icons-material/Subject';
import Tooltip from '@mui/material/Tooltip';
import { formatDistanceToNow } from 'date-fns';

const RunsList = ({
  runs,
  activeRuns,
  currentTab,
  onTabChange,
  onNewRun,
  onOpenLogs,
  onResumeRun,
  onOpenChain,
}) => {
  const [pinnedRuns, setPinnedRuns] = useState(new Set());

  const handleTabChange = (event, newValue) => {
    onTabChange(newValue);
  };

  const togglePin = (runId, event) => {
    event.stopPropagation();
    const newPinned = new Set(pinnedRuns);
    if (newPinned.has(runId)) {
      newPinned.delete(runId);
    } else {
      newPinned.add(runId);
    }
    setPinnedRuns(newPinned);
  };

  const getFilteredRuns = () => {
    let filtered = [];

    switch (currentTab) {
      case 'active':
        filtered = runs.filter(
          (run) =>
            !run.result &&
            (run.status === 'running' || run.status === 'in_progress' || run.status === 'pending')
        );
        break;
      case 'past':
        filtered = runs.filter(
          (run) =>
            run.result ||
            run.status === 'completed' ||
            run.status === 'success' ||
            run.status === 'failed'
        );
        break;
      default:
        filtered = runs;
    }

    // Sort: pinned runs first, then by creation date (newest first)
    return filtered.sort((a, b) => {
      const aPinned = pinnedRuns.has(a.id);
      const bPinned = pinnedRuns.has(b.id);

      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;

      const aDate = new Date(a.created_at || 0);
      const bDate = new Date(b.created_at || 0);
      return bDate - aDate;
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
      case 'in_progress':
      case 'pending':
        return 'primary';
      case 'completed':
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (run) => {
    if (
      !run.result &&
      (run.status === 'running' || run.status === 'in_progress' || run.status === 'pending')
    ) {
      return 'Active';
    }
    if (run.result || run.status === 'completed' || run.status === 'success') {
      return 'Completed';
    }
    if (run.status === 'failed') {
      return 'Failed';
    }
    return run.status || 'Unknown';
  };

  const isActive = (run) =>
    !run.result &&
    (run.status === 'running' || run.status === 'in_progress' || run.status === 'pending');

  const isCompleted = (run) => run.result || run.status === 'completed' || run.status === 'success';

  const handleCardClick = (run, event) => {
    if (isCompleted(run)) {
      onResumeRun && onResumeRun(run);
    } else if (isActive(run)) {
      onOpenChain && onOpenChain(run, event.currentTarget);
    } else {
      onOpenLogs && onOpenLogs(run);
    }
  };

  const filteredRuns = getFilteredRuns();

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Tabs value={currentTab} onChange={handleTabChange} sx={{ minHeight: 36 }}>
          <Tab label="Active Runs" value="active" sx={{ minHeight: 36 }} />
          <Tab label="Past Runs" value="past" sx={{ minHeight: 36 }} />
          <Tab label="Templates" value="templates" sx={{ minHeight: 36 }} />
        </Tabs>

        <Button variant="contained" startIcon={<AddIcon />} onClick={onNewRun} sx={{ ml: 2 }}>
          New Run
        </Button>
      </Box>

      <Grid container spacing={2}>
        {filteredRuns.map((run) => (
          <Grid item xs={12} sm={6} md={4} key={run.id}>
            <Card
              sx={{
                cursor: 'pointer',
                transition: 'all 0.15s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-1px)',
                  boxShadow: 2,
                },
                border: pinnedRuns.has(run.id) ? '2px solid #1976d2' : '1px solid #e0e0e0',
              }}
              onClick={(e) => handleCardClick(run, e)}
              role="button"
              tabIndex={0}
              aria-label={`Run ${run.id} ${getStatusLabel(run)}`}
            >
              <CardContent sx={{ p: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="subtitle1" component="div" sx={{ fontWeight: 600 }}>
                    Run #{run.id}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View logs">
                      <IconButton
                        size="small"
                        aria-label="view logs"
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenLogs && onOpenLogs(run);
                        }}
                      >
                        <SubjectIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={pinnedRuns.has(run.id) ? 'Unpin' : 'Pin'}>
                      <IconButton
                        size="small"
                        aria-label={pinnedRuns.has(run.id) ? 'unpin run' : 'pin run'}
                        onClick={(e) => togglePin(run.id, e)}
                        color={pinnedRuns.has(run.id) ? 'primary' : 'default'}
                      >
                        {pinnedRuns.has(run.id) ? <PushPinIcon fontSize="small" /> : <PushPinOutlinedIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                  <Chip
                    label={getStatusLabel(run)}
                    size="small"
                    color={getStatusColor(run.status)}
                    variant={run.result ? 'filled' : 'outlined'}
                  />
                  {run.source_type && (
                    <Chip label={run.source_type} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                  )}
                </Box>

                {run.created_at && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    Created {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
                  </Typography>
                )}

                {run.summary && (
                  <Typography variant="body2" sx={{ mt: 0.5 }} noWrap>
                    {run.summary.length > 100 ? `${run.summary.substring(0, 100)}...` : run.summary}
                  </Typography>
                )}

                {run.web_url && (
                  <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                    View in Codegen →
                  </Typography>
                )}

                {run.github_pull_requests && run.github_pull_requests.length > 0 && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                    {run.github_pull_requests.length} PR{run.github_pull_requests.length > 1 ? 's' : ''}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredRuns.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <Typography variant="h6" color="text.secondary">
            {currentTab === 'active' ? 'No active runs' : 'No past runs'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {currentTab === 'active' ? 'Create a new run to get started' : 'Completed runs will appear here'}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default RunsList;

