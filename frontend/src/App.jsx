import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  MessageSquare, 
  FileText, 
  AlertTriangle, 
  TrendingUp, 
  ShoppingCart, 
  DollarSign, 
  Send, 
  Database, 
  Sparkles, 
  RefreshCw,
  Upload
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

// Harmonious chart colors
const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];

// Local mock data fallbacks for standalone/offline running
const MOCK_REGIONS = [
  { region: 'West', revenue: 14250 },
  { region: 'East', revenue: 11840 },
  { region: 'North', revenue: 9500 },
  { region: 'Central', revenue: 8700 },
  { region: 'South', revenue: 6200 }
];

const MOCK_PRODUCTS = [
  { name: 'Standing Desk (Dual Motor)', category: 'Furniture', quantity_sold: 45, revenue: 20250 },
  { name: 'UltraView 27-inch Monitor', category: 'Electronics', quantity_sold: 58, revenue: 16819 },
  { name: 'Pro Wireless Headset', category: 'Electronics', quantity_sold: 90, revenue: 13499 },
  { name: 'Waterproof Windbreaker Jacket', category: 'Clothing', quantity_sold: 75, revenue: 9000 },
  { name: 'Ergonomic Office Chair', category: 'Furniture', quantity_sold: 40, revenue: 7999 }
];

const MOCK_TRENDS = [
  { month: '2026-01', revenue: 8500, order_count: 48 },
  { month: '2026-02', revenue: 9800, order_count: 52 },
  { month: '2026-03', revenue: 12100, order_count: 65 },
  { month: '2026-04', revenue: 11500, order_count: 61 },
  { month: '2026-05', revenue: 14000, order_count: 78 },
  { month: '2026-06', revenue: 16500, order_count: 92 },
  { month: '2026-07', revenue: 17200, order_count: 95 }
];

const MOCK_ANOMALIES = [
  { date: '2026-07-19', total_revenue: 1250.0, z_score: 0.1, is_anomaly: false },
  { date: '2026-07-15', total_revenue: 1420.5, z_score: 0.35, is_anomaly: false },
  { date: '2026-07-10', total_revenue: 11200.0, z_score: 3.84, is_anomaly: true },
  { date: '2026-07-05', total_revenue: 950.0, z_score: -0.12, is_anomaly: false },
  { date: '2026-06-20', total_revenue: 9800.0, z_score: 3.12, is_anomaly: true },
  { date: '2026-06-15', total_revenue: 1100.0, z_score: 0.05, is_anomaly: false }
];

const MOCK_INSIGHT = {
  date: '2026-07-19',
  total_revenue: 1250.00,
  order_count: 5,
  anomaly_detected: false,
  anomaly_score: 0.1,
  summary_report: `Daily Sales Report: Yesterday saw steady performance with stable transaction volumes. Average Order Value remains healthy. No significant statistical revenue anomalies were detected in the recent period. We recommend focusing marketing outreach on products with higher profit margins to boost total overall yield.`
};

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isOnline, setIsOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Dashboard states
  const [regionsData, setRegionsData] = useState([]);
  const [productsData, setProductsData] = useState([]);
  const [trendsData, setTrendsData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [latestInsight, setLatestInsight] = useState(null);

  // Chat states
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'system',
      content: 'Hello! I am your AI Business Insights Assistant. Ask me any question about the sales database. For example: \n• "What were our top 3 products by revenue?"\n• "Which regions had the highest orders?"\n• "Show me monthly sales trends."'
    }
  ]);

  // CSV upload states
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Check health and load data
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Test server connection
      const healthRes = await fetch(`${API_BASE_URL}/`);
      if (healthRes.ok) {
        setIsOnline(true);
        
        // Fetch metrics in parallel
        const [regionsRes, productsRes, trendsRes, anomaliesRes, insightRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/analytics/revenue-by-region`),
          fetch(`${API_BASE_URL}/api/analytics/top-products?limit=5`),
          fetch(`${API_BASE_URL}/api/analytics/monthly-trends`),
          fetch(`${API_BASE_URL}/api/analytics/anomalies`),
          fetch(`${API_BASE_URL}/api/analytics/daily-insights/latest`)
        ]);

        if (regionsRes.ok) setRegionsData(await regionsRes.json());
        if (productsRes.ok) setProductsData(await productsRes.json());
        if (trendsRes.ok) setTrendsData(await trendsRes.json());
        if (anomaliesRes.ok) setAnomalies(await anomaliesRes.json());
        if (insightRes.ok) setLatestInsight(await insightRes.json());
      } else {
        throw new Error('Server returned unhealthy status');
      }
    } catch (err) {
      console.warn('API backend unreachable. Operating in Demo Mode with mock data fallbacks.', err);
      setIsOnline(false);
      
      // Load fallback data
      setRegionsData(MOCK_REGIONS);
      setProductsData(MOCK_PRODUCTS);
      setTrendsData(MOCK_TRENDS);
      setAnomalies(MOCK_ANOMALIES);
      setLatestInsight(MOCK_INSIGHT);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Compute standard KPIs
  const totalRevenue = trendsData.reduce((sum, item) => sum + (item.revenue || 0), 0);
  const totalOrders = trendsData.reduce((sum, item) => sum + (item.order_count || 0), 0);
  const averageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;
  const activeAnomaliesCount = anomalies.filter(item => item.is_anomaly).length;

  // Ask AI handler
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userQuestion = chatInput;
    setChatInput('');
    setChatLoading(true);

    // Append user message
    setChatMessages(prev => [...prev, { role: 'user', content: userQuestion }]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/text-to-sql`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process natural language query.');
      }

      const data = await response.json();
      
      // Append AI response
      setChatMessages(prev => [...prev, {
        role: 'system',
        content: data.insight || 'Query completed successfully.',
        sql: data.sql,
        results: data.results,
        columns: data.column_names
      }]);
    } catch (err) {
      console.error(err);
      
      // Demo mock responses if backend is offline
      if (!isOnline) {
        setTimeout(() => {
          let demoResponse = {
            role: 'system',
            content: 'Demo Mode: Configure API Key to generate business narrative reports.',
            sql: 'SELECT * FROM products LIMIT 5;',
            results: MOCK_PRODUCTS.slice(0, 3),
            columns: ['name', 'category', 'revenue']
          };

          const qLower = userQuestion.toLowerCase();
          if (qLower.includes('product')) {
            demoResponse = {
              role: 'system',
              content: 'Our top performing product is the Standing Desk (Dual Motor) yielding $20,250.00 in revenue. Other high performers are screens and audio sets.',
              sql: 'SELECT name, category, revenue FROM products ORDER BY revenue DESC LIMIT 5;',
              results: MOCK_PRODUCTS,
              columns: ['name', 'category', 'revenue']
            };
          } else if (qLower.includes('region')) {
            demoResponse = {
              role: 'system',
              content: 'The West region dominates regional revenue share, followed closely by the East region, together driving over 50% of aggregate sales.',
              sql: 'SELECT r.name, SUM(oi.total_price) as revenue FROM regions r GROUP BY r.name;',
              results: MOCK_REGIONS,
              columns: ['region', 'revenue']
            };
          } else if (qLower.includes('trend') || qLower.includes('monthly')) {
            demoResponse = {
              role: 'system',
              content: 'Sales show steady growth month over month, hitting a peak in the most recent month at $17,200.00.',
              sql: 'SELECT month, revenue FROM orders GROUP BY month;',
              results: MOCK_TRENDS,
              columns: ['month', 'revenue']
            };
          }

          setChatMessages(prev => [...prev, demoResponse]);
          setChatLoading(false);
        }, 1000);
        return;
      }

      setChatMessages(prev => [...prev, {
        role: 'system',
        content: `Error: ${err.message}`
      }]);
    } finally {
      if (isOnline) setChatLoading(false);
    }
  };

  const handleUploadCSV = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadLoading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/upload-csv`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload CSV file.');
      }

      const data = await response.json();
      setUploadStatus({
        type: 'success',
        message: `Success! Imported ${data.rows_imported} transaction rows. Regenerating dashboard matrices...`
      });
      setSelectedFile(null);
      
      setTimeout(async () => {
        await loadDashboardData();
        setActiveTab('dashboard');
        setUploadStatus(null);
      }, 2500);

    } catch (err) {
      console.error(err);
      
      if (!isOnline) {
        setTimeout(() => {
          setUploadStatus({
            type: 'success',
            message: 'Demo Mode: Mock CSV processed successfully. Simulating dashboard update...'
          });
          setSelectedFile(null);
          setTimeout(() => {
            setActiveTab('dashboard');
            setUploadStatus(null);
          }, 2000);
        }, 1500);
        return;
      }

      setUploadStatus({
        type: 'error',
        message: `Error: ${err.message}`
      });
    } finally {
      if (isOnline) setUploadLoading(false);
    }
  };

  // Helper to dynamically render a chart if the SQL result is chartable
  const renderInlineChatChart = (results, columns) => {
    if (!results || results.length < 2) return null;
    
    // Find a string column and a number column
    const keys = Object.keys(results[0]);
    let xKey = null;
    let yKey = null;

    for (const key of keys) {
      const sample = results[0][key];
      if (typeof sample === 'number' && !yKey) {
        yKey = key;
      } else if (typeof sample === 'string' && !xKey) {
        xKey = key;
      }
    }

    if (!xKey || !yKey) return null;

    return (
      <div style={{ height: 180, width: '100%', marginTop: '1rem', background: 'rgba(255,255,255,0.01)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={results}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey={xKey} stroke="#94a3b8" fontSize={10} tickLine={false} />
            <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
            <Tooltip contentStyle={{ background: '#0f1524', border: '1px solid rgba(255,255,255,0.1)' }} />
            <Bar dataKey={yKey} fill="url(#chatGlow)" radius={[4, 4, 0, 0]}>
              {results.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
            <defs>
              <linearGradient id="chatGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--secondary)" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="var(--secondary)" stopOpacity={0.2}/>
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <Database className="logo-icon" />
          <span className="logo-text">Pulse Analytics</span>
        </div>

        <nav className="nav-links">
          <button 
            className={`nav-button ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard className="nav-icon" />
            Dashboard
          </button>
          
          <button 
            className={`nav-button ${activeTab === 'ask-ai' ? 'active' : ''}`}
            onClick={() => setActiveTab('ask-ai')}
          >
            <MessageSquare className="nav-icon" />
            Ask AI
          </button>
          
          <button 
            className={`nav-button ${activeTab === 'insight' ? 'active' : ''}`}
            onClick={() => setActiveTab('insight')}
          >
            <FileText className="nav-icon" />
            Daily Report
          </button>
          
          <button 
            className={`nav-button ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <Upload className="nav-icon" />
            Upload CSV
          </button>
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', marginBottom: '8px' }}>
            <span style={{ 
              width: '8px', 
              height: '8px', 
              borderRadius: '50%', 
              background: isOnline ? 'var(--success)' : 'var(--warning)',
              boxShadow: isOnline ? '0 0 8px var(--success)' : '0 0 8px var(--warning)'
            }}></span>
            <span>{isOnline ? 'System Online' : 'Demo Mode'}</span>
          </div>
          <button onClick={loadDashboardData} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <RefreshCw size={12} /> Sync Data
          </button>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="main-content">
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem', fontSize: '0.95rem' }}>Synchronizing business data ledger...</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <header className="header">
              <div className="header-title">
                <h1>
                  {activeTab === 'dashboard' && 'Executive Business Dashboard'}
                  {activeTab === 'ask-ai' && 'AI-Powered SQL Explorer'}
                  {activeTab === 'insight' && 'GenAI Automated Sales Narrative'}
                  {activeTab === 'upload' && 'Upload Custom Data Ledger'}
                </h1>
                <p>
                  {activeTab === 'dashboard' && 'Real-time retail revenue, performance metrics, and statistical outliers.'}
                  {activeTab === 'ask-ai' && 'Ask business questions in natural language. We will translate, secure, and run it.'}
                  {activeTab === 'insight' && 'Cached system-wide reports detailing yesterday\'s sales anomalies.'}
                  {activeTab === 'upload' && 'Upload flat sales CSV logs to normalize and rebuild all analytics.'}
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.02)', padding: '0.5rem 1rem', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <Sparkles size={16} style={{ color: 'var(--secondary-light)' }} />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>AI-Enabled</span>
              </div>
            </header>

            {/* TAB CONTENT: DASHBOARD */}
            {activeTab === 'dashboard' && (
              <>
                {/* KPI metrics row */}
                <div className="kpi-grid">
                  <div className="kpi-card" id="kpi-revenue">
                    <div className="kpi-icon-wrapper revenue">
                      <DollarSign />
                    </div>
                    <div className="kpi-info">
                      <h3>Total Sales</h3>
                      <div className="kpi-value">${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                    </div>
                  </div>

                  <div className="kpi-card" id="kpi-orders">
                    <div className="kpi-icon-wrapper orders">
                      <ShoppingCart />
                    </div>
                    <div className="kpi-info">
                      <h3>Total Orders</h3>
                      <div className="kpi-value">{totalOrders}</div>
                    </div>
                  </div>

                  <div className="kpi-card" id="kpi-aov">
                    <div className="kpi-icon-wrapper aov">
                      <TrendingUp />
                    </div>
                    <div className="kpi-info">
                      <h3>AOV</h3>
                      <div className="kpi-value">${averageOrderValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                    </div>
                  </div>

                  <div className="kpi-card" id="kpi-anomalies">
                    <div className={`kpi-icon-wrapper anomaly ${activeAnomaliesCount > 0 ? 'alert-active' : ''}`}>
                      <AlertTriangle />
                    </div>
                    <div className="kpi-info">
                      <h3>Outliers Detected</h3>
                      <div className="kpi-value" style={{ color: activeAnomaliesCount > 0 ? 'var(--accent)' : 'inherit' }}>
                        {activeAnomaliesCount}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Daily narrative insight preview */}
                {latestInsight && (
                  <div style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)', border: '1px solid rgba(99, 102, 241, 0.25)', padding: '1.5rem', borderRadius: '16px', marginBottom: '2.5rem', display: 'flex', gap: '1.25rem', alignItems: 'flex-start' }}>
                    <div style={{ background: 'var(--primary-glow)', padding: '10px', borderRadius: '10px', color: 'var(--primary-light)', flexShrink: 0 }}>
                      <Sparkles />
                    </div>
                    <div>
                      <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.35rem', color: 'var(--primary-light)' }}>
                        Latest Automated Executive Insight ({latestInsight.date})
                      </h4>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>{latestInsight.summary_report}</p>
                    </div>
                  </div>
                )}

                {/* Charts Grid */}
                <div className="charts-grid">
                  {/* Line Chart: monthly revenue trends */}
                  <div className="chart-card charts-grid-full">
                    <div className="chart-header">
                      <div className="chart-title">
                        <h2>Sales Performance & Trends</h2>
                        <p>Month-over-month sales progression and order count</p>
                      </div>
                    </div>
                    <div className="chart-body">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendsData}>
                          <defs>
                            <linearGradient id="revenueGlow" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                          <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                          <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                          <Tooltip contentStyle={{ background: '#0f1524', border: '1px solid rgba(255, 255, 255, 0.1)' }} />
                          <Legend />
                          <Line type="monotone" dataKey="revenue" name="Revenue ($)" stroke="var(--primary-light)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                          <Line type="monotone" dataKey="order_count" name="Order Count" stroke="var(--secondary-light)" strokeWidth={2} dot={{ r: 2 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Bar Chart: top products */}
                  <div className="chart-card">
                    <div className="chart-header">
                      <div className="chart-title">
                        <h2>Top Product Categories</h2>
                        <p>Best-selling inventories ranked by completed sales yield</p>
                      </div>
                    </div>
                    <div className="chart-body">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={productsData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                          <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} tickFormatter={(val) => val.length > 15 ? `${val.substring(0, 15)}...` : val} />
                          <YAxis stroke="#94a3b8" fontSize={10} tickLine={false} />
                          <Tooltip contentStyle={{ background: '#0f1524', border: '1px solid rgba(255, 255, 255, 0.1)' }} />
                          <Bar dataKey="revenue" name="Revenue ($)" fill="var(--primary)" radius={[6, 6, 0, 0]}>
                            {productsData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Pie Chart: Region distribution */}
                  <div className="chart-card">
                    <div className="chart-header">
                      <div className="chart-title">
                        <h2>Revenue Share by Region</h2>
                        <p>Total completed aggregate sales breakdown by zone</p>
                      </div>
                    </div>
                    <div className="chart-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={regionsData}
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={105}
                            paddingAngle={5}
                            dataKey="revenue"
                            nameKey="region"
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {regionsData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ background: '#0f1524', border: '1px solid rgba(255, 255, 255, 0.1)' }} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* TAB CONTENT: ASK AI */}
            {activeTab === 'ask-ai' && (
              <div className="chat-container">
                <div className="chat-history">
                  {chatMessages.map((msg, index) => (
                    <div key={index} className={`chat-message ${msg.role}`}>
                      <div className="chat-avatar">
                        {msg.role === 'user' ? 'U' : <Sparkles size={18} />}
                      </div>
                      <div className="chat-bubble">
                        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                        
                        {/* If statement contains generated SQL */}
                        {msg.sql && (
                          <details className="sql-block">
                            <summary className="sql-header">
                              <span>Generated SQL Query (SELECT only)</span>
                              <span style={{ fontSize: '0.75rem', color: 'var(--primary-light)' }}>Click to Expand</span>
                            </summary>
                            <pre className="sql-code"><code>{msg.sql}</code></pre>
                          </details>
                        )}

                        {/* If statement contains tabular SQL results */}
                        {msg.results && msg.results.length > 0 && (
                          <>
                            <div className="results-table-container">
                              <table className="results-table">
                                <thead>
                                  <tr>
                                    {msg.columns.map((col) => (
                                      <th key={col}>{col}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {msg.results.map((row, rIdx) => (
                                    <tr key={rIdx}>
                                      {msg.columns.map((col) => (
                                        <td key={col}>
                                          {typeof row[col] === 'number' && col.toLowerCase().includes('revenue') 
                                            ? `$${row[col].toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                            : row[col]?.toString()}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            
                            {/* Dynamically build mini-visualizer chart */}
                            {renderInlineChatChart(msg.results, msg.columns)}
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {chatLoading && (
                    <div className="chat-message system">
                      <div className="chat-avatar">
                        <Sparkles size={18} />
                      </div>
                      <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="spinner" style={{ margin: 0, width: '16px', height: '16px' }}></div>
                        <span>PulseAI generating SQL syntax & querying database...</span>
                      </div>
                    </div>
                  )}
                </div>

                <form className="chat-input-bar" onSubmit={handleSendMessage}>
                  <input 
                    type="text" 
                    placeholder="Ask questions (e.g. 'what is our best selling product category?', 'list orders from central region')"
                    className="chat-input"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={chatLoading}
                  />
                  <button type="submit" className="send-button" disabled={!chatInput.trim() || chatLoading}>
                    <Send size={18} />
                  </button>
                </form>
              </div>
            )}

            {/* TAB CONTENT: DAILY REPORTS */}
            {activeTab === 'insight' && (
              <div className="insight-wrapper">
                {/* Executive insight markdown panel */}
                <section className="report-panel">
                  {latestInsight ? (
                    <article className="report-markdown">
                      <h1>Daily Business Summary</h1>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem' }}>
                        Generated Date: <strong>{latestInsight.date}</strong> | Status: <strong>Archived</strong>
                      </p>
                      
                      <h2>Report Insight Summary</h2>
                      <p>{latestInsight.summary_report}</p>
                      
                      <h2>Key Metrics Captured</h2>
                      <ul>
                        <li>Total sales ledger volume: <strong>${floatToCurr(latestInsight.total_revenue)}</strong></li>
                        <li>Completed order logs: <strong>{latestInsight.order_count}</strong></li>
                        <li>Average order unit size: <strong>${floatToCurr(latestInsight.order_count > 0 ? latestInsight.total_revenue / latestInsight.order_count : 0)}</strong></li>
                        <li>Anomaly deviation factor: <strong>{latestInsight.anomaly_score.toFixed(4)}</strong></li>
                      </ul>

                      <h2>Statistical Outlier Status</h2>
                      <div style={{ 
                        background: latestInsight.anomaly_detected ? 'rgba(244,63,94,0.05)' : 'rgba(16,185,129,0.05)',
                        border: `1px solid ${latestInsight.anomaly_detected ? 'rgba(244,63,94,0.2)' : 'rgba(16,185,129,0.2)'}`,
                        borderRadius: '10px',
                        padding: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem'
                      }}>
                        <AlertTriangle style={{ color: latestInsight.anomaly_detected ? 'var(--accent)' : 'var(--success)' }} />
                        <div>
                          <strong style={{ color: latestInsight.anomaly_detected ? 'var(--accent)' : 'var(--success)' }}>
                            {latestInsight.anomaly_detected ? 'Revenue Spike Detected (Statistical Outlier)' : 'Revenue Stable (Within Standard Limits)'}
                          </strong>
                          <p style={{ fontSize: '0.85rem', margin: 0, color: 'var(--text-secondary)' }}>
                            The statistical deviation threshold (Z-score) is set to 2.0. Outlier score registers at: {latestInsight.anomaly_score.toFixed(2)}.
                          </p>
                        </div>
                      </div>
                    </article>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '3rem 0' }}>
                      <FileText size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
                      <h3>No daily report compiled.</h3>
                      <p style={{ color: 'var(--text-secondary)' }}>Launch backend script `daily_report.py` to compile daily stats.</p>
                    </div>
                  )}
                </section>

                {/* Sidebar list of historical anomalies */}
                <section className="anomalies-panel">
                  <h2>Statistical Anomalies Ledger</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1.5rem' }}>
                    Days in recent history flagged for absolute Z-scores $|z| &gt; 2.0$.
                  </p>
                  
                  <div className="anomaly-list">
                    {anomalies.map((item, index) => (
                      <div key={index} className={`anomaly-item ${item.is_anomaly ? 'alert' : ''}`}>
                        <div>
                          <div className="anomaly-date">{item.date}</div>
                          <div className="anomaly-value">${floatToCurr(item.total_revenue)}</div>
                        </div>
                        <span className={`anomaly-status ${item.is_anomaly ? 'alert' : 'normal'}`}>
                          {item.is_anomaly ? `Spike (Z: ${item.z_score.toFixed(1)})` : 'Normal'}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {/* TAB CONTENT: UPLOAD CSV */}
            {activeTab === 'upload' && (
              <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px', padding: '2rem' }}>
                  <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Upload style={{ color: 'var(--secondary)' }} />
                    Upload Business Ledger CSV
                  </h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                    You can upload a flat CSV file of your sales ledger. The backend will automatically parse, clean, and normalize the data, mapping it into our relational schema (Regions, Products, Customers, Orders, and Order Items), and regenerate the analytical insights.
                  </p>
                  
                  {/* Expected Schema Reference Table */}
                  <div style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', borderRadius: '8px', padding: '1rem', marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Expected CSV Schema Columns:</h3>
                    <div style={{ overflowX: 'auto' }}>
                      <code style={{ fontSize: '0.8rem', color: 'var(--secondary-light)', whiteSpace: 'nowrap' }}>
                        order_date, customer_first_name, customer_last_name, customer_email, region, product_name, category, price, quantity
                      </code>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      *Note: Dates should follow YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format. Status defaults to "Completed".
                    </div>
                  </div>

                  {/* Form */}
                  <form onSubmit={handleUploadCSV} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div style={{ border: '2px dashed var(--border)', borderRadius: '12px', padding: '3rem 2rem', textAlign: 'center', transition: 'var(--transition-smooth)', cursor: 'pointer' }}
                         onDragOver={(e) => e.preventDefault()}
                         onDrop={(e) => {
                           e.preventDefault();
                           if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                             setSelectedFile(e.dataTransfer.files[0]);
                           }
                         }}>
                      <Upload size={36} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
                      <input 
                        type="file" 
                        accept=".csv"
                        id="csv-file-input"
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            setSelectedFile(e.target.files[0]);
                          }
                        }}
                        style={{ display: 'none' }}
                      />
                      <label htmlFor="csv-file-input" style={{ cursor: 'pointer', display: 'block' }}>
                        <span style={{ color: 'var(--primary-light)', fontWeight: 600 }}>Click to browse</span> or drag and drop your CSV file here
                      </label>
                      {selectedFile && (
                        <div style={{ marginTop: '1rem', background: 'var(--primary-glow)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid rgba(99, 102, 241, 0.2)', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                          <span>File selected: <strong>{selectedFile.name}</strong> ({Math.round(selectedFile.size / 1024)} KB)</span>
                        </div>
                      )}
                    </div>

                    {uploadStatus && (
                      <div style={{ 
                        background: uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.05)' : 'rgba(244, 63, 94, 0.05)',
                        border: `1px solid ${uploadStatus.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)'}`,
                        color: uploadStatus.type === 'success' ? 'var(--success)' : 'var(--accent)',
                        borderRadius: '10px',
                        padding: '1rem',
                        fontSize: '0.9rem'
                      }}>
                        {uploadStatus.message}
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                      {selectedFile && (
                        <button 
                          type="button" 
                          onClick={() => setSelectedFile(null)}
                          style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-secondary)', padding: '0.75rem 1.5rem', borderRadius: '8px', cursor: 'pointer' }}
                        >
                          Clear
                        </button>
                      )}
                      <button 
                        type="submit" 
                        disabled={!selectedFile || uploadLoading}
                        style={{ 
                          background: selectedFile && !uploadLoading ? 'var(--primary)' : 'var(--border)', 
                          color: selectedFile && !uploadLoading ? 'white' : 'var(--text-muted)', 
                          padding: '0.75rem 2rem', 
                          borderRadius: '8px', 
                          fontWeight: 600,
                          border: 'none',
                          cursor: selectedFile && !uploadLoading ? 'pointer' : 'not-allowed',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}
                      >
                        {uploadLoading ? (
                          <>
                            <div className="spinner" style={{ margin: 0, width: '14px', height: '14px', borderTopColor: 'white' }}></div>
                            <span>Parsing Ledger...</span>
                          </>
                        ) : (
                          <>
                            <Upload size={16} />
                            <span>Upload and Process</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

// Utility formatting
const floatToCurr = (val) => {
  return parseFloat(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

export default App;
