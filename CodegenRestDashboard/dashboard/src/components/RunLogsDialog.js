import React, { useState, useEffect, useRef } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { format } from 'date-fns';
import { getAgentRun } from '../services/apiService';

const RunLogsDialog = ({ open, onClose, run, socket }) => {
  const [runDetails, setRunDetails] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (open && run) {
      loadRunDetails();
      subscribeToUpdates();
    }
  }, [open, run]);

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const loadRunDetails = async () => {
    if (!run) return;

    setLoading(true);
    try {
      const details = await getAgentRun(run.id);
      setRunDetails(details);

      // Initialize logs from run details
      const initialLogs = [];

      if (details.result) {
        initialLogs.push({
          timestamp: new Date().toISOString(),
          type: 'result',
          content: details.result,
          level: 'info'
        });
      }

      if (details.summary) {
        initialLogs.push({
          timestamp: new Date().toISOString(),
          type: 'summary',
          content: details.summary,
          level: 'info'
        });
      }

      setLogs(initialLogs);
    } catch (error) {
      console.error('Failed to load run details:', error);
      setLogs([{
        timestamp: new Date().toISOString(),
        type: 'error',
        content: `Failed to load run details: ${error.message}`,
        level: 'error'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const subscribeToUpdates = () => {
    if (!socket || !run) return;

    // Listen for run updates
    const handleRunUpdate = (data) => {
      if (data.runId === run.id) {
        setRunDetails(prev => ({ ...prev, ...data.data }));

        // Add update log
        const updateLog = {
          timestamp: new Date().toISOString(),
          type: 'update',
          content: `Run status updated to: ${data.data.status || 'unknown'}`,
          level: 'info'
        };
        setLogs(prev => [...prev, updateLog]);
      }
    };

    const handleWebhookUpdate = (data) => {
      if (data.runId === run.id) {
        const webhookLog = {
          timestamp: new Date().toISOString(),
          type: 'webhook',
          content: `Webhook received: ${data.event}`,
          level: 'info'
        };
        setLogs(prev => [...prev, webhookLog]);

        // Reload run details on webhook
        loadRunDetails();
      }
    };

    socket.on('run_update', handleRunUpdate);
    socket.on('run_webhook_update', handleWebhookUpdate);

    // Cleanup on unmount
    return () => {
      socket.off('run_update', handleRunUpdate);
      socket.off('run_webhook_update', handleWebhookUpdate);
    };
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  const renderLogContent = (log) => {
    if (log.type === 'result' && log.content) {
      // Try to detect if it's JSON
      try {
        const parsed = JSON.parse(log.content);
        return (
          <SyntaxHighlighter language="json" style={materialLight}>
            {JSON.stringify(parsed, null, 2)}
          </SyntaxHighlighter>
        );
      } catch {
        // Not JSON, render as plain text
        return <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{log.content}</Typography>;
      }
    }

    return <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{log.content}</Typography>;
  };

  if (!run) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">
            Agent Run #{run.id}
          </Typography>
          {runDetails && (
            <Chip
              label={runDetails.status || 'unknown'}
              color={getStatusColor(runDetails.status)}
              size="small"
            />
          )}
        </Box>
        {runDetails && (
          <Typography variant="body2" color="text.secondary">
            Created {runDetails.created_at ? format(new Date(runDetails.created_at), 'PPp') : 'Unknown time'}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Run Info */}
            {runDetails && (
              <Box sx={{ mb: 2 }}>
                {runDetails.summary && (
                  <Typography variant="body1" sx={{ mb: 1, fontWeight: 'bold' }}>
                    Summary: {runDetails.summary}
                  </Typography>
                )}

                {runDetails.web_url && (
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <a href={runDetails.web_url} target="_blank" rel="noopener noreferrer">
                      View in Codegen →
                    </a>
                  </Typography>
                )}

                {runDetails.github_pull_requests && runDetails.github_pull_requests.length > 0 && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                      GitHub Pull Requests:
                    </Typography>
                    {runDetails.github_pull_requests.map((pr, index) => (
                      <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                        <a href={pr.url} target="_blank" rel="noopener noreferrer">
                          {pr.title}
                        </a>
                      </Typography>
                    ))}
                  </Box>
                )}
              </Box>
            )}

            {/* Logs */}
            <Typography variant="h6" sx={{ mb: 2 }}>
              Logs & Output
            </Typography>

            <Box sx={{ flex: 1, overflow: 'auto', border: '1px solid #e0e0e0', borderRadius: 1, p: 2 }}>
              {logs.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No logs available yet...
                </Typography>
              ) : (
                logs.map((log, index) => (
                  <Paper
                    key={index}
                    elevation={0}
                    sx={{
                      p: 1,
                      mb: 1,
                      backgroundColor: log.level === 'error' ? '#ffebee' : '#f5f5f5',
                      borderLeft: `4px solid ${log.level === 'error' ? '#f44336' : '#2196f3'}`
                    }}
                  >
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                      {format(new Date(log.timestamp), 'HH:mm:ss')} - {log.type}
                    </Typography>
                    {renderLogContent(log)}
                  </Paper>
                ))
              )}
              <div ref={logsEndRef} />
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        {runDetails && runDetails.web_url && (
          <Button
            href={runDetails.web_url}
            target="_blank"
            rel="noopener noreferrer"
            variant="outlined"
          >
            View in Codegen
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default RunLogsDialog;

