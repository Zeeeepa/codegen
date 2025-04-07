import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useState, useEffect } from 'react';

// Create a theme instance
const lightTheme = createTheme({
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

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

export default function App({ Component, pageProps }: AppProps) {
  const [theme, setTheme] = useState(lightTheme);
  const [mounted, setMounted] = useState(false);

  // When mounted on client, set the theme preference
  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setTheme(darkTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === lightTheme ? darkTheme : lightTheme;
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme === darkTheme ? 'dark' : 'light');
  };

  // Avoid rendering with wrong theme
  if (!mounted) {
    return <div style={{ visibility: 'hidden' }} />;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Component {...pageProps} toggleTheme={toggleTheme} theme={theme} />
    </ThemeProvider>
  );
}