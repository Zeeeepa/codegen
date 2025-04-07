import { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  Tabs,
  Tab,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Slider,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  FormControlLabel,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Settings as SettingsIcon,
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Code as CodeIcon,
  Build as BuildIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { useRouter } from 'next/router';

interface Project {
  id: string;
  name: string;
  git_url: string;
  slack_channel: string | null;
  max_parallel_tasks: number;
  documents: string[];
  features: Record<string, any>;
  implementation_plan: ImplementationPlan | null;
  created_at: string;
  updated_at: string;
}

interface ImplementationPlan {
  description?: string;
  tasks: Task[];
}

interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  dependencies: string[];
  completed_at?: number;
}

interface ChatMessage {
  role: string;
  content: string;
}

interface HomeProps {
  toggleTheme: () => void;
  theme: any;
}

export default function Home({ toggleTheme, theme }: HomeProps) {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectIndex, setSelectedProjectIndex] = useState<number>(0);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProjectDialog, setShowNewProjectDialog] = useState<boolean>(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState<boolean>(false);
  const [newProjectName, setNewProjectName] = useState<string>('');
  const [newProjectGitUrl, setNewProjectGitUrl] = useState<string>('');
  const [newProjectSlackChannel, setNewProjectSlackChannel] = useState<string>('');
  const [newProjectConcurrency, setNewProjectConcurrency] = useState<number>(2);
  const [documentTabIndex, setDocumentTabIndex] = useState<number>(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState<string>('');
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (projects.length > 0 && selectedProjectIndex < projects.length) {
      setSelectedProject(projects[selectedProjectIndex]);
      fetchRecentActivity(projects[selectedProjectIndex].id);
    }
  }, [projects, selectedProjectIndex]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/projects');
      setProjects(response.data);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch projects');
      setLoading(false);
    }
  };

  const fetchRecentActivity = async (projectId: string) => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/recent-activity`);
      setRecentActivity(response.data.recent_merges || []);
    } catch (err: any) {
      console.error('Failed to fetch recent activity:', err);
    }
  };

  const createProject = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/projects', {
        name: newProjectName,
        git_url: newProjectGitUrl,
        slack_channel: newProjectSlackChannel || null,
        max_parallel_tasks: newProjectConcurrency,
      });
      
      setProjects([...projects, response.data]);
      setSelectedProjectIndex(projects.length);
      setShowNewProjectDialog(false);
      setNewProjectName('');
      setNewProjectGitUrl('');
      setNewProjectSlackChannel('');
      setNewProjectConcurrency(2);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
      setLoading(false);
    }
  };

  const updateProjectSettings = async () => {
    if (!selectedProject) return;

    try {
      setLoading(true);
      const response = await axios.put(`/api/projects/${selectedProject.id}`, {
        name: selectedProject.name,
        git_url: selectedProject.git_url,
        slack_channel: selectedProject.slack_channel,
        max_parallel_tasks: selectedProject.max_parallel_tasks,
      });
      
      const updatedProjects = [...projects];
      updatedProjects[selectedProjectIndex] = response.data;
      setProjects(updatedProjects);
      setSelectedProject(response.data);
      setShowSettingsDialog(false);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update project settings');
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: string, status: string) => {
    if (!selectedProject) return;

    try {
      const response = await axios.put(`/api/projects/${selectedProject.id}/tasks/${taskId}`, {
        status,
      });
      
      if (selectedProject.implementation_plan) {
        const updatedTasks = selectedProject.implementation_plan.tasks.map(task => {
          if (task.id === taskId) {
            return { ...task, status };
          }
          return task;
        });
        
        const updatedProject = {
          ...selectedProject,
          implementation_plan: {
            ...selectedProject.implementation_plan,
            tasks: updatedTasks,
          },
        };
        
        const updatedProjects = [...projects];
        updatedProjects[selectedProjectIndex] = updatedProject;
        setProjects(updatedProjects);
        setSelectedProject(updatedProject);
      }
    } catch (err: any) {
      console.error('Failed to update task status:', err);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !selectedProject) return;

    const newMessage: ChatMessage = { role: 'user', content: chatInput };
    setChatMessages([...chatMessages, newMessage]);
    setChatInput('');

    try {
      const response = await axios.post('/api/chat', {
        project_id: selectedProject.id,
        message: chatInput,
        chat_history: chatMessages,
      });
      
      setChatMessages([...chatMessages, newMessage, { role: 'assistant', content: response.data.response }]);
    } catch (err: any) {
      console.error('Failed to send chat message:', err);
      setChatMessages([
        ...chatMessages,
        newMessage,
        { role: 'system', content: 'Error: Failed to get response from assistant.' },
      ]);
    }
  };

  const renderImplementationTree = (tasks: Task[], parentId: string | null = null) => {
    const filteredTasks = parentId
      ? tasks.filter(task => task.dependencies.includes(parentId))
      : tasks.filter(task => task.dependencies.length === 0);

    return (
      <List dense>
        {filteredTasks.map(task => (
          <ListItem key={task.id} className="tree-node">
            <div className="tree-node-content">
              <Checkbox
                checked={task.status === 'completed'}
                onChange={(e) => updateTaskStatus(task.id, e.target.checked ? 'completed' : 'pending')}
                size="small"
              />
              <ListItemText primary={task.title} secondary={task.description} />
            </div>
            <div className="tree-node-children">
              {renderImplementationTree(tasks, task.id)}
            </div>
          </ListItem>
        ))}
      </List>
    );
  };

  const navigateToCodeImprovement = () => {
    const projectId = selectedProject?.id;
    router.push({
      pathname: '/code-improvement',
      query: projectId ? { projectId } : {},
    });
  };

  return (
    <>
      <Head>
        <title>Projector</title>
        <meta name="description" content="Multi-Thread Slack GitHub Tool" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            MultiThread Slack GitHub
          </Typography>
          <Button
            color="inherit"
            startIcon={<BuildIcon />}
            onClick={navigateToCodeImprovement}
            sx={{ mr: 2 }}
          >
            Code Improvement
          </Button>
          <IconButton color="inherit" onClick={toggleTheme}>
            {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4">Dashboard</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowNewProjectDialog(true)}
          >
            Add Project
          </Button>
        </Box>

        {loading && <CircularProgress />}
        {error && <Typography color="error">{error}</Typography>}

        {!loading && !error && (
          <>
            <Box sx={{ mb: 2 }}>
              <Typography variant="h6">Recent Activity</Typography>
              <Paper sx={{ p: 2 }}>
                {recentActivity.length > 0 ? (
                  <List dense>
                    {recentActivity.slice(0, 5).map((merge, index) => (
                      <ListItem key={index}>
                        <ListItemText
                          primary={`PR #${merge.number} - ${merge.title}`}
                          secondary={`Merged at ${new Date(merge.merged_at).toLocaleString()}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography>No recent activity found.</Typography>
                )}
              </Paper>
            </Box>

            <Box sx={{ width: '100%', mb: 2 }}>
              <Tabs
                value={selectedProjectIndex}
                onChange={(_, newValue) => setSelectedProjectIndex(newValue)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {projects.map(project => (
                  <Tab key={project.id} label={project.name} />
                ))}
              </Tabs>
            </Box>

            {selectedProject && (
              <>
                <div className="three-column-layout">
                  <div className="column">
                    <Typography variant="h6">Step by Step Structure</Typography>
                    {selectedProject.implementation_plan ? (
                      <List dense>
                        {selectedProject.implementation_plan.tasks.map((task, index) => (
                          <ListItem key={task.id}>
                            <ListItemText
                              primary={`${index + 1}. ${task.status === 'completed' ? '\u2713' : ' '} ${task.title}`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography>No implementation plan found.</Typography>
                    )}
                  </div>

                  <div className="column">
                    <Typography variant="h6">Project Context</Typography>
                    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                      <Tabs
                        value={documentTabIndex}
                        onChange={(_, newValue) => setDocumentTabIndex(newValue)}
                        variant="scrollable"
                        scrollButtons="auto"
                      >
                        <Tab label="Requirements" />
                        <Tab label="Architecture" />
                        <Tab label="Implementation" />
                        <Tab label="Testing" />
                      </Tabs>
                    </Box>

                    <Box sx={{ p: 2 }}>
                      <Typography>
                        {documentTabIndex === 0 && 'Requirements documents'}
                        {documentTabIndex === 1 && 'Architecture documents'}
                        {documentTabIndex === 2 && 'Implementation documents'}
                        {documentTabIndex === 3 && 'Testing documents'}
                      </Typography>
                    </Box>

                    <Box sx={{ mt: 4 }}>
                      <Typography variant="h6">Concurrency Setting</Typography>
                      <Slider
                        value={selectedProject.max_parallel_tasks}
                        min={1}
                        max={10}
                        step={1}
                        marks
                        valueLabelDisplay="auto"
                        onChange={(_, value) => {
                          setSelectedProject({
                            ...selectedProject,
                            max_parallel_tasks: value as number,
                          });
                        }}
                      />
                      <Button
                        variant="outlined"
                        onClick={updateProjectSettings}
                        sx={{ mt: 1 }}
                      >
                        Update Concurrency
                      </Button>
                    </Box>

                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        variant="outlined"
                        startIcon={<SettingsIcon />}
                        onClick={() => setShowSettingsDialog(true)}
                      >
                        Project Settings
                      </Button>
                    </Box>
                  </div>

                  <div className="column">
                    <Typography variant="h6">Implementation Tree</Typography>
                    {selectedProject.implementation_plan ? (
                      renderImplementationTree(selectedProject.implementation_plan.tasks)
                    ) : (
                      <Typography>No implementation plan found.</Typography>
                    )}
                  </div>
                </div>

                <Divider sx={{ my: 2 }} />

                <div className="chat-container">
                  <Typography variant="h6">Chat Interface</Typography>
                  <Box sx={{ mb: 2, height: '60%', overflowY: 'auto' }}>
                    {chatMessages.map((message, index) => (
                      <Box
                        key={index}
                        className={`chat-message ${message.role}-message`}
                      >
                        <Typography variant="body2">
                          <strong>{message.role === 'user' ? 'You' : message.role === 'assistant' ? 'Assistant' : 'System'}:</strong> {message.content}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TextField
                      fullWidth
                      variant="outlined"
                      placeholder="Type your message..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                      size="small"
                    />
                    <IconButton color="primary" sx={{ ml: 1 }}>
                      <AttachFileIcon />
                    </IconButton>
                    <IconButton color="primary" sx={{ ml: 1 }}>
                      <CodeIcon />
                    </IconButton>
                    <Button
                      variant="contained"
                      endIcon={<SendIcon />}
                      onClick={sendChatMessage}
                      sx={{ ml: 1 }}
                    >
                      Send
                    </Button>
                  </Box>
                </div>
              </>
            )}
          </>
        )}
      </Container>

      <Dialog open={showNewProjectDialog} onClose={() => setShowNewProjectDialog(false)}>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="GitHub Repository URL"
            fullWidth
            value={newProjectGitUrl}
            onChange={(e) => setNewProjectGitUrl(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Slack Channel (optional)"
            fullWidth
            value={newProjectSlackChannel}
            onChange={(e) => setNewProjectSlackChannel(e.target.value)}
          />
          <Typography gutterBottom>Maximum Concurrent Tasks</Typography>
          <Slider
            value={newProjectConcurrency}
            min={1}
            max={10}
            step={1}
            marks
            valueLabelDisplay="auto"
            onChange={(_, value) => setNewProjectConcurrency(value as number)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowNewProjectDialog(false)}>Cancel</Button>
          <Button onClick={createProject} variant="contained">Create Project</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={showSettingsDialog} onClose={() => setShowSettingsDialog(false)}>
        <DialogTitle>Project Settings</DialogTitle>
        <DialogContent>
          {selectedProject && (
            <>
              <TextField
                autoFocus
                margin="dense"
                label="Project Name"
                fullWidth
                value={selectedProject.name}
                onChange={(e) => setSelectedProject({ ...selectedProject, name: e.target.value })}
              />
              <TextField
                margin="dense"
                label="GitHub Repository URL"
                fullWidth
                value={selectedProject.git_url}
                onChange={(e) => setSelectedProject({ ...selectedProject, git_url: e.target.value })}
              />
              <TextField
                margin="dense"
                label="Slack Channel"
                fullWidth
                value={selectedProject.slack_channel || ''}
                onChange={(e) => setSelectedProject({ ...selectedProject, slack_channel: e.target.value })}
              />
              <Typography gutterBottom>Maximum Concurrent Tasks</Typography>
              <Slider
                value={selectedProject.max_parallel_tasks}
                min={1}
                max={10}
                step={1}
                marks
                valueLabelDisplay="auto"
                onChange={(_, value) => setSelectedProject({ ...selectedProject, max_parallel_tasks: value as number })}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettingsDialog(false)}>Cancel</Button>
          <Button onClick={updateProjectSettings} variant="contained">Save Settings</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}