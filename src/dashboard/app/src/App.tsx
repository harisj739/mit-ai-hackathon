import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardContent,
  Paper,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Security,
  BugReport,
  Speed,
  CheckCircle,
  Warning,
  Refresh,
  DarkMode,
  LightMode,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  PieChart,
  Pie,
  Cell,

} from 'recharts';
import axios from 'axios';
import './App.css';

// Dark theme configuration
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4ff',
    },
    secondary: {
      main: '#ff6b6b',
    },
    background: {
      default: '#0a0e1a',
      paper: '#1a1f3a',
    },
    success: {
      main: '#00ff88',
    },
    warning: {
      main: '#ffb800',
    },
    error: {
      main: '#ff5555',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
});

// Light theme configuration
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
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: {
    borderRadius: 12,
  },
});

interface TestStats {
  total_test_runs: number;
  total_test_cases: number;
  success_rate: number;
  average_latency: number;
  total_vulnerabilities: number;
  last_run: string | null;
}

interface TestRun {
  id: string;
  name: string;
  status: string;
  created_at: string;
  total_cases: number;
  success_rate: number;
  average_latency: number;
}



const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [stats, setStats] = useState<TestStats | null>(null);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [statsResponse, runsResponse] = await Promise.all([
        axios.get('http://localhost:8080/api/stats'),
        axios.get('http://localhost:8080/api/test-runs'),
      ]);

      setStats(statsResponse.data);
      setTestRuns(runsResponse.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to fetch data from the backend. Please ensure it is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon, color, subtitle }: any) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${color}22, ${color}11)`, border: `1px solid ${color}33` }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {title}
              </Typography>
              <Typography variant="h4" component="div" color={color} fontWeight="bold">
                {value}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {subtitle}
                </Typography>
              )}
            </Box>
            <Box sx={{ color: color }}>
              {icon}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );

  const chartData = testRuns.map((run, index) => ({
    name: `Test ${index + 1}`,
    success_rate: run.success_rate,
    latency: run.average_latency / 1000, // Convert to seconds
  }));

  const vulnerabilityData = [
    { name: 'Secure', value: stats?.total_test_cases || 0 - (stats?.total_vulnerabilities || 0), color: '#00ff88' },
    { name: 'Vulnerabilities', value: stats?.total_vulnerabilities || 0, color: '#ff6b6b' },
  ];

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', background: 'linear-gradient(135deg, #0a0e1a 0%, #1a1f3a 100%)' }}>
        <AppBar position="static" elevation={0} sx={{ background: 'rgba(26, 31, 58, 0.8)', backdropFilter: 'blur(10px)' }}>
          <Toolbar>
            <Security sx={{ mr: 2, color: '#00d4ff' }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
              FailProof LLM Dashboard
            </Typography>
            <Chip 
              icon={<CheckCircle />} 
              label="REAL DATA" 
              color="success" 
              variant="outlined" 
              sx={{ mr: 2, fontWeight: 'bold' }}
            />
            <Tooltip title="Refresh Data">
              <IconButton color="inherit" onClick={fetchData}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title={`Switch to ${isDarkMode ? 'Light' : 'Dark'} Mode`}>
              <IconButton color="inherit" onClick={() => setIsDarkMode(!isDarkMode)}>
                {isDarkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Tooltip>
          </Toolbar>
        </AppBar>

        <main>
          <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            {error && (
              <Paper sx={{ p: 2, mb: 2, backgroundColor: 'error.main', color: 'white' }}>
                <Typography>{error}</Typography>
              </Paper>
            )}
            <AnimatePresence>
              {loading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <LinearProgress sx={{ mb: 2, borderRadius: 2, height: 6 }} />
                </motion.div>
              )}
            </AnimatePresence>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
              {/* Statistics Cards */}
              <div style={{ flex: '1 1 calc(25% - 16px)'}}>
                <StatCard
                  title="Total Tests"
                  value={stats?.total_test_cases || 0}
                  icon={<BugReport sx={{ fontSize: 40 }} />}
                  color="#00d4ff"
                  subtitle="Stress test cases executed"
                />
              </div>
              <div style={{ flex: '1 1 calc(25% - 16px)'}}>
                <StatCard
                  title="Success Rate"
                  value={`${(stats?.success_rate || 0).toFixed(1)}%`}
                  icon={<CheckCircle sx={{ fontSize: 40 }} />}
                  color="#00ff88"
                  subtitle="LLM robustness score"
                />
              </div>
              <div style={{ flex: '1 1 calc(25% - 16px)'}}>
                <StatCard
                  title="Avg Latency"
                  value={`${((stats?.average_latency || 0) / 1000).toFixed(1)}s`}
                  icon={<Speed sx={{ fontSize: 40 }} />}
                  color="#ffb800"
                  subtitle="Response time performance"
                />
              </div>
              <div style={{ flex: '1 1 calc(25% - 16px)'}}>
                <StatCard
                  title="Vulnerabilities"
                  value={stats?.total_vulnerabilities || 0}
                  icon={<Warning sx={{ fontSize: 40 }} />}
                  color="#ff6b6b"
                  subtitle="Security issues detected"
                />
              </div>

              {/* Performance Chart */}
              <div style={{ flex: '1 1 calc(66.66% - 16px)'}}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6 }}
                >
                  <Card sx={{ height: 400 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Test Performance Metrics
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData}>
                          <defs>
                            <linearGradient id="successGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#00ff88" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#00ff88" stopOpacity={0.1}/>
                            </linearGradient>
                            <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#00d4ff" stopOpacity={0.1}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                          <XAxis dataKey="name" stroke="#666" />
                          <YAxis stroke="#666" />
                          <RechartsTooltip 
                            contentStyle={{ 
                              backgroundColor: '#1a1f3a', 
                              border: '1px solid #333',
                              borderRadius: '8px'
                            }} 
                          />
                          <Area 
                            type="monotone" 
                            dataKey="success_rate" 
                            stroke="#00ff88" 
                            fillOpacity={1} 
                            fill="url(#successGradient)" 
                            name="Success Rate (%)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </motion.div>
              </div>

              {/* Security Overview */}
              <div style={{ flex: '1 1 calc(33.33% - 16px)'}}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                >
                  <Card sx={{ height: 400 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Security Overview
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={vulnerabilityData}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                          >
                            {vulnerabilityData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <RechartsTooltip 
                            contentStyle={{ 
                              backgroundColor: '#1a1f3a', 
                              border: '1px solid #333',
                              borderRadius: '8px'
                            }} 
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </motion.div>
              </div>

              {/* Test Runs Table */}
              <div style={{ flex: '1 1 100%'}}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Recent Test Runs
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        {testRuns.map((run, index) => (
                          <Paper 
                            key={run.id} 
                            sx={{ 
                              p: 2, 
                              mb: 2, 
                              background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 255, 136, 0.1))',
                              border: '1px solid rgba(0, 212, 255, 0.3)'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', width: '100%' }}>
                              <div style={{ flex: 3 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {run.name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {new Date(run.created_at).toLocaleString()}
                                </Typography>
                              </div>
                              <div style={{ flex: 2 }}>
                                <Chip 
                                  label={run.status.toUpperCase()} 
                                  color={run.status === 'completed' ? 'success' : 'warning'}
                                  size="small"
                                />
                              </div>
                              <div style={{ flex: 2 }}>
                                <Typography variant="body2">
                                  {run.total_cases} test cases
                                </Typography>
                              </div>
                              <div style={{ flex: 2 }}>
                                <Typography variant="body2" color="success.main">
                                  {run.success_rate.toFixed(1)}% success
                                </Typography>
                              </div>
                              <div style={{ flex: 3 }}>
                                <Typography variant="body2">
                                  {(run.average_latency / 1000).toFixed(1)}s avg latency
                                </Typography>
                              </div>
                            </div>
                          </Paper>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </motion.div>
              </div>
            </div>

            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Last updated: {lastUpdated.toLocaleTimeString()} • Real-time FailProof LLM monitoring
              </Typography>
            </Box>
          </Container>
        </main>
      </Box>
    </ThemeProvider>
  );
};

export default App;
