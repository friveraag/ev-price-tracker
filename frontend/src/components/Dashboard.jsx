import React from 'react';

const styles = {
  container: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px'
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  label: {
    fontSize: '12px',
    fontWeight: '500',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  value: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a1a2e',
    marginTop: '8px'
  },
  subtext: {
    fontSize: '12px',
    color: '#888',
    marginTop: '4px'
  },
  cheapestList: {
    marginTop: '12px'
  },
  cheapestItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid #eee',
    fontSize: '14px'
  },
  cheapestName: {
    color: '#333'
  },
  cheapestPrice: {
    fontWeight: '600',
    color: '#059669'
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
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function Dashboard({ stats }) {
  if (!stats) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <p style={{ color: '#666' }}>Loading statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.label}>Total Listings</div>
        <div style={styles.value}>{stats.total_listings.toLocaleString()}</div>
        <div style={styles.subtext}>across all models</div>
      </div>

      <div style={styles.card}>
        <div style={styles.label}>Models Tracked</div>
        <div style={styles.value}>{stats.models_with_data}</div>
        <div style={styles.subtext}>with active listings</div>
      </div>

      <div style={styles.card}>
        <div style={styles.label}>Average Price</div>
        <div style={styles.value}>{formatCurrency(stats.avg_price)}</div>
        <div style={styles.subtext}>across all listings</div>
      </div>

      <div style={styles.card}>
        <div style={styles.label}>Last Updated</div>
        <div style={{ ...styles.value, fontSize: '20px' }}>{formatDate(stats.last_scrape)}</div>
        <div style={styles.subtext}>most recent scrape</div>
      </div>

      <div style={{ ...styles.card, gridColumn: 'span 2' }}>
        <div style={styles.label}>Most Affordable EVs (by average price)</div>
        {stats.cheapest_models && stats.cheapest_models.length > 0 ? (
          <div style={styles.cheapestList}>
            {stats.cheapest_models.map((model, index) => (
              <div key={index} style={styles.cheapestItem}>
                <span style={styles.cheapestName}>
                  {model.make} {model.model}
                  <span style={{ color: '#888', marginLeft: '8px' }}>
                    ({model.count} listings)
                  </span>
                </span>
                <span style={styles.cheapestPrice}>{formatCurrency(model.avg_price)}</span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#888', marginTop: '12px' }}>
            No data yet. Click "Scrape Prices" to fetch listings.
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
