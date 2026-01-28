import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';
import { fetchModelPrices } from '../api';

const styles = {
  container: {
    width: '100%',
    height: '400px'
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '300px',
    color: '#888'
  },
  noData: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '300px',
    color: '#888'
  },
  noDataText: {
    marginBottom: '8px',
    fontSize: '16px'
  },
  noDataSubtext: {
    fontSize: '14px',
    color: '#aaa'
  },
  error: {
    padding: '20px',
    backgroundColor: '#fee2e2',
    color: '#dc2626',
    borderRadius: '8px',
    textAlign: 'center'
  },
  stats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '16px',
    marginBottom: '20px'
  },
  stat: {
    textAlign: 'center',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px'
  },
  statLabel: {
    fontSize: '12px',
    color: '#666',
    marginBottom: '4px'
  },
  statValue: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1a1a2e'
  }
};

function formatCurrency(value) {
  if (!value) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value);
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function PriceChart({ modelId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPriceHistory();
  }, [modelId]);

  async function loadPriceHistory() {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchModelPrices(modelId);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div style={styles.loading}>Loading price history...</div>;
  }

  if (error) {
    return <div style={styles.error}>{error}</div>;
  }

  if (!data?.history || data.history.length === 0) {
    return (
      <div style={styles.noData}>
        <div style={styles.noDataText}>No price history available</div>
        <div style={styles.noDataSubtext}>
          Click "Scrape Prices" to fetch listings for this model
        </div>
      </div>
    );
  }

  const chartData = data.history.map(item => ({
    ...item,
    date: formatDate(item.date)
  }));

  const latestData = data.history[data.history.length - 1];

  return (
    <div>
      <div style={styles.stats}>
        <div style={styles.stat}>
          <div style={styles.statLabel}>Average Price</div>
          <div style={styles.statValue}>{formatCurrency(latestData?.avg_price)}</div>
        </div>
        <div style={styles.stat}>
          <div style={styles.statLabel}>Min Price</div>
          <div style={styles.statValue}>{formatCurrency(latestData?.min_price)}</div>
        </div>
        <div style={styles.stat}>
          <div style={styles.statLabel}>Max Price</div>
          <div style={styles.statValue}>{formatCurrency(latestData?.max_price)}</div>
        </div>
        <div style={styles.stat}>
          <div style={styles.statLabel}>Listings</div>
          <div style={styles.statValue}>{latestData?.listing_count || 0}</div>
        </div>
      </div>

      <div style={styles.container}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorRange" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value, name) => [formatCurrency(value), name]}
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #eee',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="min_price"
              name="Min Price"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#colorRange)"
            />
            <Area
              type="monotone"
              dataKey="avg_price"
              name="Avg Price"
              stroke="#4f46e5"
              strokeWidth={2}
              fill="url(#colorAvg)"
            />
            <Area
              type="monotone"
              dataKey="max_price"
              name="Max Price"
              stroke="#f59e0b"
              strokeWidth={2}
              fill="none"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default PriceChart;
