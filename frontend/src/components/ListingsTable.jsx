import React, { useState, useEffect } from 'react';
import { fetchModelListings } from '../api';

const styles = {
  container: {
    overflowX: 'auto'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px'
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    backgroundColor: '#f9fafb',
    borderBottom: '2px solid #eee',
    fontWeight: '600',
    color: '#333',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap'
  },
  thSortable: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px'
  },
  td: {
    padding: '12px 16px',
    borderBottom: '1px solid #eee',
    color: '#333'
  },
  priceCell: {
    fontWeight: '600',
    color: '#059669'
  },
  linkCell: {
    maxWidth: '200px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap'
  },
  link: {
    color: '#4f46e5',
    textDecoration: 'none'
  },
  loading: {
    padding: '40px',
    textAlign: 'center',
    color: '#888'
  },
  noData: {
    padding: '40px',
    textAlign: 'center',
    color: '#888'
  },
  error: {
    padding: '20px',
    backgroundColor: '#fee2e2',
    color: '#dc2626',
    borderRadius: '8px',
    textAlign: 'center'
  },
  pagination: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 0',
    borderTop: '1px solid #eee',
    marginTop: '8px'
  },
  pageInfo: {
    color: '#666',
    fontSize: '14px'
  },
  pageButtons: {
    display: 'flex',
    gap: '8px'
  },
  pageButton: {
    padding: '8px 16px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  pageButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed'
  },
  sourceTag: {
    display: 'inline-block',
    padding: '2px 8px',
    fontSize: '12px',
    borderRadius: '4px',
    backgroundColor: '#e5e7eb',
    color: '#374151'
  }
};

const sourceColors = {
  'cargurus': { bg: '#dbeafe', color: '#1d4ed8' },
  'autotrader': { bg: '#fef3c7', color: '#b45309' },
  'cars.com': { bg: '#d1fae5', color: '#047857' }
};

function formatCurrency(value) {
  if (!value) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value);
}

function formatMileage(value) {
  if (!value) return '-';
  return `${value.toLocaleString()} mi`;
}

function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function ListingsTable({ modelId }) {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('price');
  const [sortOrder, setSortOrder] = useState('asc');
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const limit = 20;

  useEffect(() => {
    loadListings();
  }, [modelId, sortBy, sortOrder, offset]);

  async function loadListings() {
    try {
      setLoading(true);
      setError(null);
      const result = await fetchModelListings(modelId, {
        limit: limit + 1, // Fetch one extra to check if there are more
        offset,
        sortBy,
        sortOrder
      });
      const fetchedListings = result.listings || [];
      setHasMore(fetchedListings.length > limit);
      setListings(fetchedListings.slice(0, limit));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSort(column) {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
    setOffset(0);
  }

  function getSortIndicator(column) {
    if (sortBy !== column) return '';
    return sortOrder === 'asc' ? ' ▲' : ' ▼';
  }

  if (loading && listings.length === 0) {
    return <div style={styles.loading}>Loading listings...</div>;
  }

  if (error) {
    return <div style={styles.error}>{error}</div>;
  }

  if (listings.length === 0) {
    return (
      <div style={styles.noData}>
        No listings found. Click "Scrape Prices" to fetch listings.
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th} onClick={() => handleSort('year')}>
              <div style={styles.thSortable}>
                Year{getSortIndicator('year')}
              </div>
            </th>
            <th style={styles.th} onClick={() => handleSort('price')}>
              <div style={styles.thSortable}>
                Price{getSortIndicator('price')}
              </div>
            </th>
            <th style={styles.th} onClick={() => handleSort('mileage')}>
              <div style={styles.thSortable}>
                Mileage{getSortIndicator('mileage')}
              </div>
            </th>
            <th style={styles.th}>Location</th>
            <th style={styles.th}>Source</th>
            <th style={styles.th} onClick={() => handleSort('scraped_at')}>
              <div style={styles.thSortable}>
                Scraped{getSortIndicator('scraped_at')}
              </div>
            </th>
            <th style={styles.th}>Link</th>
          </tr>
        </thead>
        <tbody>
          {listings.map((listing, index) => {
            const sourceStyle = sourceColors[listing.source] || {};
            return (
              <tr key={listing.id || index}>
                <td style={styles.td}>{listing.year || '-'}</td>
                <td style={{ ...styles.td, ...styles.priceCell }}>
                  {formatCurrency(listing.price)}
                </td>
                <td style={styles.td}>{formatMileage(listing.mileage)}</td>
                <td style={styles.td}>{listing.location || '-'}</td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.sourceTag,
                      backgroundColor: sourceStyle.bg,
                      color: sourceStyle.color
                    }}
                  >
                    {listing.source}
                  </span>
                </td>
                <td style={styles.td}>{formatDate(listing.scraped_at)}</td>
                <td style={{ ...styles.td, ...styles.linkCell }}>
                  {listing.url ? (
                    <a
                      href={listing.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={styles.link}
                    >
                      View Listing
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div style={styles.pagination}>
        <div style={styles.pageInfo}>
          Showing {offset + 1} - {offset + listings.length}
        </div>
        <div style={styles.pageButtons}>
          <button
            style={{
              ...styles.pageButton,
              ...(offset === 0 ? styles.pageButtonDisabled : {})
            }}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            Previous
          </button>
          <button
            style={{
              ...styles.pageButton,
              ...(!hasMore ? styles.pageButtonDisabled : {})
            }}
            onClick={() => setOffset(offset + limit)}
            disabled={!hasMore}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default ListingsTable;
