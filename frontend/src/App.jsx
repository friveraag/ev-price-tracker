import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import ModelSelector from './components/ModelSelector';
import PriceChart from './components/PriceChart';
import ListingsTable from './components/ListingsTable';
import { fetchModels, fetchStats, triggerScrape, fetchScrapeStatus } from './api';

const styles = {
  container: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a1a2e'
  },
  subtitle: {
    fontSize: '14px',
    color: '#666',
    marginTop: '4px'
  },
  scrapeButton: {
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#fff',
    backgroundColor: '#4f46e5',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  scrapeButtonDisabled: {
    backgroundColor: '#9ca3af',
    cursor: 'not-allowed'
  },
  scrapeStatus: {
    marginTop: '8px',
    fontSize: '12px',
    color: '#666'
  },
  mainContent: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: '24px'
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px'
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  cardTitle: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#1a1a2e'
  },
  error: {
    padding: '12px',
    backgroundColor: '#fee2e2',
    color: '#dc2626',
    borderRadius: '8px',
    marginBottom: '16px'
  }
};

function App() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [stats, setStats] = useState(null);
  const [scrapeStatus, setScrapeStatus] = useState({ is_running: false });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (scrapeStatus.is_running) {
      const interval = setInterval(checkScrapeStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [scrapeStatus.is_running]);

  async function loadInitialData() {
    try {
      setLoading(true);
      const [modelsData, statsData, statusData] = await Promise.all([
        fetchModels(),
        fetchStats(),
        fetchScrapeStatus()
      ]);
      setModels(modelsData);
      setStats(statsData);
      setScrapeStatus(statusData);
      if (modelsData.length > 0 && !selectedModel) {
        setSelectedModel(modelsData[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function checkScrapeStatus() {
    try {
      const status = await fetchScrapeStatus();
      setScrapeStatus(status);
      if (!status.is_running) {
        // Refresh stats when scrape completes
        const statsData = await fetchStats();
        setStats(statsData);
      }
    } catch (err) {
      console.error('Failed to check scrape status:', err);
    }
  }

  async function handleScrape() {
    try {
      setError(null);
      await triggerScrape();
      setScrapeStatus({ ...scrapeStatus, is_running: true });
    } catch (err) {
      setError(err.message);
    }
  }

  function handleModelSelect(model) {
    setSelectedModel(model);
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: 'center', padding: '100px 0' }}>
          <h2>Loading EV Price Tracker...</h2>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>EV Price Tracker</h1>
          <p style={styles.subtitle}>Track used electric vehicle prices across major listing sites</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <button
            style={{
              ...styles.scrapeButton,
              ...(scrapeStatus.is_running ? styles.scrapeButtonDisabled : {})
            }}
            onClick={handleScrape}
            disabled={scrapeStatus.is_running}
          >
            {scrapeStatus.is_running ? 'Scraping...' : 'Scrape Prices'}
          </button>
          {scrapeStatus.is_running && (
            <div style={styles.scrapeStatus}>
              {scrapeStatus.current_model && `Scraping ${scrapeStatus.current_model}...`}
              {scrapeStatus.total > 0 && ` (${scrapeStatus.progress}/${scrapeStatus.total})`}
            </div>
          )}
        </div>
      </header>

      {error && <div style={styles.error}>{error}</div>}

      <Dashboard stats={stats} />

      <div style={styles.mainContent}>
        <aside style={styles.sidebar}>
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>EV Models</h2>
            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              onSelect={handleModelSelect}
            />
          </div>
        </aside>

        <main style={styles.content}>
          {selectedModel && (
            <>
              <div style={styles.card}>
                <h2 style={styles.cardTitle}>
                  Price Trends: {selectedModel.make} {selectedModel.model}
                </h2>
                <PriceChart modelId={selectedModel.id} key={selectedModel.id} />
              </div>

              <div style={styles.card}>
                <h2 style={styles.cardTitle}>
                  Current Listings: {selectedModel.make} {selectedModel.model}
                </h2>
                <ListingsTable modelId={selectedModel.id} key={`listings-${selectedModel.id}`} />
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
