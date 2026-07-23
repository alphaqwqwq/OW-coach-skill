import React, { useState, useCallback } from 'react';
import ApiKeyInput, { type ApiConfig } from './components/ApiKeyInput';
import Chat from './components/Chat';

const STORAGE_KEY = 'ow_coach_api_config';

export default function App() {
  const [apiConfig, setApiConfig] = useState<ApiConfig | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as ApiConfig;
        if (parsed.key) return parsed;
      }
    } catch { /* ignore */ }
    return null;
  });
  const [showConfig, setShowConfig] = useState(!apiConfig);

  const handleSaveConfig = useCallback((config: ApiConfig) => {
    setApiConfig(config);
    setShowConfig(false);
  }, []);

  return (
    <div className="app">
      {showConfig || !apiConfig ? (
        <div className="config-page">
          <div className="config-card">
            <div className="config-header">
              <h1>OW Coach</h1>
              <p className="config-desc">守望先锋 AI 教练 — 纯前端应用</p>
              <div className="config-info">
                <p>首次使用需要配置 API 信息：</p>
                <ul>
                  <li>模型：选择预设（推荐 DeepSeek V3 或 GPT-4o-mini），选"自定义模型"可手动输入</li>
                  <li>Endpoint：根据预设自动填充，也可手动修改</li>
                  <li>API Key：你的 API 密钥，仅保存在本地浏览器</li>
                </ul>
              </div>
            </div>
            <ApiKeyInput onSave={handleSaveConfig} initialConfig={apiConfig || undefined} />
            {apiConfig && (
              <button className="btn-start" onClick={() => setShowConfig(false)}>
                开始使用
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          <Chat apiConfig={apiConfig} />
          <button className="btn-config-toggle" onClick={() => setShowConfig(true)} title="API 配置">
            ⚙️
          </button>
        </>
      )}
    </div>
  );
}
