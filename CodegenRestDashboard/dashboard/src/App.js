import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Badge from '@mui/material/Badge';
import IconButton from '@mui/material/IconButton';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import Tooltip from '@mui/material/Tooltip';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import { io } from 'socket.io-client';
import toast, { Toaster } from 'react-hot-toast';

// Components
import ActiveRunsTooltip from './components/ActiveRunsTooltip';
import RunsList from './components/RunsList';
import RunLogsDialog from './components/RunLogsDialog';
import NewRunForm from './components/NewRunForm';
import TemplatesTab from './components/TemplatesTab';
import ChainSelector from './components/ChainSelector';
import { resumeAgentRun } from './services/apiService';

// Hooks
import useAutoRefresh from './hooks/useAutoRefresh';
import useNotifications from './hooks/useNotifications';

// Services
import { getAgentRuns } from './services/apiService';

// Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [activeRuns, setActiveRuns] = useState([]);
  const [allRuns, setAllRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [logsDialogOpen, setLogsDialogOpen] = useState(false);
  const [newRunDialogOpen, setNewRunDialogOpen] = useState(false);
  const [activeRunsTooltipOpen, setActiveRunsTooltipOpen] = useState(false);
  const [currentTab, setCurrentTab] = useState('active'); // 'active', 'past', 'templates'
  const [socket, setSocket] = useState(null);
  const [chainAnchorEl, setChainAnchorEl] = useState(null);
  const [chainRun, setChainRun] = useState(null);
  const [runChains, setRunChains] = useState({}); // { [runId]: Template[] }
  const [executedChains, setExecutedChains] = useState({}); // { [runId]: true }
  const prevAllRunsRef = React.useRef([]);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('http://localhost:3001');
    setSocket(newSocket);

    newSocket.on('runs_updated', () => {
      loadRuns();
    });

    newSocket.on('run_update', (data) => {
      // Handle individual run updates
      setAllRuns(prevRuns =>
        prevRuns.map(run =>
          run.id === data.runId ? { ...run, ...data.data } : run
        )
      );
    });

    return () => newSocket.close();
  }, []);

  // Load runs on mount and when tab changes
  const loadRuns = async () => {
    try {
      const activeRunsData = await getAgentRuns({ status: 'active' });
      const pastRunsData = await getAgentRuns({ status: 'completed' });

      setActiveRuns(activeRunsData.items || []);
      setAllRuns([...(activeRunsData.items || []), ...(pastRunsData.items || [])]);
    } catch (error) {
      console.error('Failed to load runs:', error);
      toast.error('Failed to load agent runs');
    }
  };

  useEffect(() => {
    loadRuns();
  }, [currentTab]);

  // Auto-refresh active runs
  useAutoRefresh(activeRuns, (updatedRuns) => {
    setActiveRuns(updatedRuns);
  });

  // Setup notifications
  useNotifications(activeRuns);

  const handleOpenLogs = (run) => {
    setSelectedRun(run);
    setLogsDialogOpen(true);
    if (socket) {
      socket.emit('subscribe', { runId: run.id });
    }
  };

  const handleResumeRun = async (run) => {
    try {
      await resumeAgentRun(run.id, {});
      toast.success(`Resumed run ${run.id}`);
    } catch (e) {
      toast.error(`Failed to resume run ${run.id}: ${e.message}`);
    }
  };

  const handleOpenChain = (run, anchorEl) => {
    setChainRun(run);
    setChainAnchorEl(anchorEl);
  };

  const handleApplyChainTemplates = (templates) => {
    if (!chainRun) return;
    setRunChains((prev) => ({ ...prev, [chainRun.id]: templates }));
  };

  const handleNewRun = () => {
    setNewRunDialogOpen(true);
  };

  const handleRunCreated = (newRun) => {
    setActiveRuns(prev => [newRun, ...prev]);
    setAllRuns(prev => [newRun, ...prev]);
    setNewRunDialogOpen(false);
    toast.success(`Agent run ${newRun.id} created successfully`);
  };

  const getActiveRunsCount = () => {
    return activeRuns.filter(run =>
      !run.result && (run.status === 'running' || run.status === 'in_progress' || run.status === 'pending')
    ).length;
  };

  // Execute chains when runs transition to completed
  useEffect(() => {
    const prev = prevAllRunsRef.current;
    const wasActive = (r) => r && !r.result && (r.status === 'running' || r.status === 'in_progress' || r.status === 'pending');
    const isCompleted = (r) => r && (r.result || r.status === 'completed' || r.status === 'success');

    const transitioned = allRuns.filter((curr) => {
      const prevRun = prev.find((p) => p.id === curr.id);
      return prevRun && wasActive(prevRun) && isCompleted(curr);
    });

    const runSequential = async (runId, templates) => {
      for (const t of templates) {
        try {
          await resumeAgentRun(runId, { prompt: t.prompt });
          toast.success(`Queued follow-up: ${t.name || 'template'} for run ${runId}`);
        } catch (e) {
          toast.error(`Failed to queue follow-up for run ${runId}: ${e.message}`);
          break;
        }
      }
    };

    transitioned.forEach((r) => {
      const templates = runChains[r.id];
      if (templates && templates.length && !executedChains[r.id]) {
        setExecutedChains((prevExec) => ({ ...prevExec, [r.id]: true }));
        runSequential(r.id, templates);
      }
    });

    prevAllRunsRef.current = allRuns;
  }, [allRuns, runChains]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Codegen Dashboard
            </Typography>

            {/* Active Runs Badge */}
            <ClickAwayListener onClickAway={() => setActiveRunsTooltipOpen(false)}>
              <div>
                <Tooltip
  // Execute chains when runs transition to completed
  useEffect(() => {
    const prev = prevAllRunsRef.current;

    const wasActive = (r) =>
      r && !r.result && (r.status === 'running' || r.status === 'in_progress' || r.status === 'pending');
    const isCompleted = (r) => r && (r.result || r.status === 'completed' || r.status === 'success');

    const transitioned = allRuns.filter((curr) => {
      const prevRun = prev.find((p) => p.id === curr.id);
      return prevRun && wasActive(prevRun) && isCompleted(curr);
    });

    const runSequential = async (runId, templates) => {
      for (const t of templates) {
        try {
          await resumeAgentRun(runId, { prompt: t.prompt });
          toast.success(`Queued follow-up: ${t.name || 'template'} for run ${runId}`);
        } catch (e) {
          toast.error(`Failed to queue follow-up for run ${runId}: ${e.message}`);
          break; // stop chain on error
        }
      }
    };

    transitioned.forEach((r) => {
      const templates = runChains[r.id];
      if (templates && templates.length && !executedChains[r.id]) {
        setExecutedChains((prevExec) => ({ ...prevExec, [r.id]: true }));
        runSequential(r.id, templates);
      }
    });

    prevAllRunsRef.current = allRuns;
  }, [allRuns, runChains]);

                  title={<ActiveRunsTooltip runs={activeRuns} onRunClick={handleOpenLogs} />}
                  open={activeRunsTooltipOpen}
                  onClose={() => setActiveRunsTooltipOpen(false)}
                  disableFocusListener
                  disableHoverListener
                  disableTouchListener
                  placement="bottom-end"
                  arrow
                >
                  <IconButton
                    color="inherit"
                    onClick={() => setActiveRunsTooltipOpen(!activeRunsTooltipOpen)}
                  >
                    <Badge badgeContent={getActiveRunsCount()} color="error">
                      <PlayArrowIcon />
                    </Badge>
                  </IconButton>
                </Tooltip>
              </div>
            </ClickAwayListener>
          </Toolbar>
        {/* Chain Selector Popover */}
        <ChainSelector
          open={Boolean(chainAnchorEl)}
          anchorEl={chainAnchorEl}
          onClose={() => { setChainAnchorEl(null); setChainRun(null); }}
          onApply={handleApplyChainTemplates}
        />

        </AppBar>

        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <RunsList
            runs={allRuns}

            activeRuns={activeRuns}
            currentTab={currentTab}
            onTabChange={setCurrentTab}
            onNewRun={handleNewRun}
            onOpenLogs={handleOpenLogs}
            onResumeRun={handleResumeRun}
            onOpenChain={handleOpenChain}
          />
        </Container>

        {/* Run Logs Dialog */}
        <RunLogsDialog
          open={logsDialogOpen}
          onClose={() => setLogsDialogOpen(false)}
          run={selectedRun}
          socket={socket}
        />

        {/* New Run Dialog */}
        <NewRunForm
          open={newRunDialogOpen}
          onClose={() => setNewRunDialogOpen(false)}
          onRunCreated={handleRunCreated}
        />

        {/* Templates Tab (conditionally rendered) */}
        {currentTab === 'templates' && (
          <TemplatesTab />
        )}
      </Box>

      <Toaster position="top-right" />
    </ThemeProvider>
  );
}

export default App;
