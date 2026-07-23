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

// 预设模型配置
interface ModelPreset {
  label: string;
  model: string;
  endpoint: string;
}

const MODEL_PRESETS: ModelPreset[] = [
  { label: 'GPT-4o (OpenAI)', model: 'gpt-4o', endpoint: 'https://api.openai.com' },
  { label: 'GPT-4o-mini (OpenAI)', model: 'gpt-4o-mini', endpoint: 'https://api.openai.com' },
  { label: 'DeepSeek V3 (deepseek-chat)', model: 'deepseek-chat', endpoint: 'https://api.deepseek.com' },
  { label: 'DeepSeek R1 (deepseek-reasoner)', model: 'deepseek-reasoner', endpoint: 'https://api.deepseek.com' },
  { label: 'DeepSeek V3 (SiliconFlow)', model: 'deepseek-ai/DeepSeek-V2.5', endpoint: 'https://api.siliconflow.cn' },
  { label: 'Qwen 2.5 (阿里云)', model: 'qwen2.5-72b-instruct', endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { label: 'GLM-4 (智谱)', model: 'glm-4', endpoint: 'https://open.bigmodel.cn/api/paas/v4' },
  { label: '自定义模型', model: '', endpoint: '' },
];

export default function ApiKeyInput({ onSave, initialConfig }: Props) {
  const [key, setKey] = useState(initialConfig?.key || '');
  const [endpoint, setEndpoint] = useState(initialConfig?.endpoint || DEFAULT_ENDPOINT);
  const [model, setModel] = useState(initialConfig?.model || DEFAULT_MODEL);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [isCustomModel, setIsCustomModel] = useState(false);

  // 初始化时根据已有配置自动匹配预设
  useEffect(() => {
    const currentModel = initialConfig?.model || model;
    const currentEndpoint = initialConfig?.endpoint || endpoint;
    const match = MODEL_PRESETS.find(
      p => p.model === currentModel && p.endpoint === currentEndpoint
    );
    if (match && match.label !== '自定义模型') {
      setSelectedPreset(match.label);
      setIsCustomModel(false);
    } else {
      setSelectedPreset('自定义模型');
      setIsCustomModel(true);
    }
  }, []); // 只跑一次

  // 读取 localStorage
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

  // 切换预设
  const handlePresetChange = (label: string) => {
    setSelectedPreset(label);
    if (label === '自定义模型') {
      setIsCustomModel(true);
      return;
    }
    setIsCustomModel(false);
    const preset = MODEL_PRESETS.find(p => p.label === label);
    if (preset) {
      setEndpoint(preset.endpoint);
      setModel(preset.model);
    }
  };

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
          <label>模型预设</label>
          <select
            value={selectedPreset}
            onChange={e => handlePresetChange(e.target.value)}
            className="model-select"
          >
            {MODEL_PRESETS.map(p => (
              <option key={p.label} value={p.label}>{p.label}</option>
            ))}
          </select>
        </div>

        {isCustomModel && (
          <div className="field">
            <label>Model</label>
            <input
              type="text"
              value={model}
              onChange={e => setModel(e.target.value)}
              placeholder="gpt-4o-mini"
            />
          </div>
        )}

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
