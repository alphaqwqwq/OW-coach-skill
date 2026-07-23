import React, { useState, useEffect } from 'react';

const STORAGE_KEY = 'ow_coach_api_config';

export interface ApiConfig {
  key: string;
  endpoint: string;
  model: string;
}

interface Props {
  onSave: (config: ApiConfig) => void;
  initialConfig?: ApiConfig;
}

const DEFAULT_ENDPOINT = 'https://api.openai.com';
const DEFAULT_MODEL = 'gpt-4o-mini';

export default function ApiKeyInput({ onSave, initialConfig }: Props) {
  const [key, setKey] = useState(initialConfig?.key || '');
  const [endpoint, setEndpoint] = useState(initialConfig?.endpoint || DEFAULT_ENDPOINT);
  const [model, setModel] = useState(initialConfig?.model || DEFAULT_MODEL);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const savedConfig = localStorage.getItem(STORAGE_KEY);
    if (savedConfig && !initialConfig) {
      try {
        const parsed = JSON.parse(savedConfig) as ApiConfig;
        setKey(parsed.key);
        setEndpoint(parsed.endpoint || DEFAULT_ENDPOINT);
        setModel(parsed.model || DEFAULT_MODEL);
      } catch { /* ignore */ }
    }
  }, [initialConfig]);

  const handleSave = () => {
    const config: ApiConfig = { key: key.trim(), endpoint: endpoint.trim(), model: model.trim() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    onSave(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const hasSaved = initialConfig?.key || localStorage.getItem(STORAGE_KEY);

  return (
    <div className="api-key-input">
      <div className="api-form">
        <div className="field">
          <label>API Endpoint</label>
          <input
            type="text"
            value={endpoint}
            onChange={e => setEndpoint(e.target.value)}
            placeholder="https://api.openai.com"
          />
        </div>
        <div className="field">
          <label>Model</label>
          <input
            type="text"
            value={model}
            onChange={e => setModel(e.target.value)}
            placeholder="gpt-4o-mini"
          />
        </div>
        <div className="field">
          <label>API Key</label>
          <div className="key-row">
            <input
              type={showKey ? 'text' : 'password'}
              value={key}
              onChange={e => setKey(e.target.value)}
              placeholder="sk-..."
            />
            <button className="btn-icon" onClick={() => setShowKey(!showKey)} title={showKey ? '隐藏' : '显示'}>
              {showKey ? '🙈' : '👁️'}
            </button>
          </div>
        </div>
        <button className="btn-save" onClick={handleSave}>
          {saved ? '✓ 已保存' : '保存配置'}
        </button>
      </div>
      {hasSaved && (
        <div className="api-status">
          <span className="status-dot" /> API 已配置
        </div>
      )}
    </div>
  );
}
