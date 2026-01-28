import React, { useState, useMemo } from 'react';

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  searchInput: {
    padding: '10px 12px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    marginBottom: '8px',
    outline: 'none',
    transition: 'border-color 0.2s'
  },
  makeGroup: {
    marginBottom: '8px'
  },
  makeHeader: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    padding: '8px 0',
    borderBottom: '1px solid #eee'
  },
  modelList: {
    display: 'flex',
    flexDirection: 'column'
  },
  modelButton: {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    padding: '10px 12px',
    fontSize: '14px',
    textAlign: 'left',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  modelButtonSelected: {
    backgroundColor: '#eef2ff',
    color: '#4f46e5',
    fontWeight: '500'
  },
  noResults: {
    padding: '20px',
    textAlign: 'center',
    color: '#888',
    fontSize: '14px'
  }
};

function ModelSelector({ models, selectedModel, onSelect }) {
  const [searchTerm, setSearchTerm] = useState('');

  const groupedModels = useMemo(() => {
    const filtered = models.filter(model => {
      const searchLower = searchTerm.toLowerCase();
      return (
        model.make.toLowerCase().includes(searchLower) ||
        model.model.toLowerCase().includes(searchLower)
      );
    });

    return filtered.reduce((groups, model) => {
      const make = model.make;
      if (!groups[make]) {
        groups[make] = [];
      }
      groups[make].push(model);
      return groups;
    }, {});
  }, [models, searchTerm]);

  const makes = Object.keys(groupedModels).sort();

  return (
    <div style={styles.container}>
      <input
        type="text"
        placeholder="Search models..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        style={styles.searchInput}
      />

      {makes.length === 0 ? (
        <div style={styles.noResults}>No models found</div>
      ) : (
        makes.map(make => (
          <div key={make} style={styles.makeGroup}>
            <div style={styles.makeHeader}>{make}</div>
            <div style={styles.modelList}>
              {groupedModels[make].map(model => (
                <button
                  key={model.id}
                  style={{
                    ...styles.modelButton,
                    ...(selectedModel?.id === model.id ? styles.modelButtonSelected : {})
                  }}
                  onClick={() => onSelect(model)}
                  onMouseOver={(e) => {
                    if (selectedModel?.id !== model.id) {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (selectedModel?.id !== model.id) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  {model.model}
                </button>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default ModelSelector;
