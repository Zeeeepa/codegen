import { useState } from 'react';
import Head from 'next/head';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Container,
  Box,
  Paper,
} from '@mui/material';
import {
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useRouter } from 'next/router';
import CodeImprovement from '@/components/CodeImprovement';

interface CodeImprovementPageProps {
  toggleTheme: () => void;
  theme: any;
}

export default function CodeImprovementPage({ toggleTheme, theme }: CodeImprovementPageProps) {
  const router = useRouter();
  const { projectId } = router.query;

  return (
    <>
      <Head>
        <title>Code Improvement - Projector</title>
        <meta name="description" content="AI-powered code improvement suggestions" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <AppBar position="static">
        <Toolbar>
          <IconButton 
            edge="start" 
            color="inherit" 
            aria-label="back"
            onClick={() => router.push('/')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            MultiThread Slack GitHub
          </Typography>
          <IconButton color="inherit" onClick={toggleTheme}>
            {theme.palette.mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 0 }}>
          <CodeImprovement projectId={projectId as string} />
        </Paper>
      </Container>
    </>
  );
}
