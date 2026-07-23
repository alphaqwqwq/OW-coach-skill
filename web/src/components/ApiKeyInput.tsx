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

const DEFAULT_ENDPOINT = 'https://api.deepseek.com';
const DEFAULT_MODEL = 'deepseek-v4-flash';

// 预设模型配置
interface ModelPreset {
  label: string;
  model: string;
  endpoint: string;
}

const MODEL_PRESETS: ModelPreset[] = [
  // ===== OpenAI (2026年7月最新) =====
  { label: 'GPT-5.6 Terra (OpenAI · 均衡版)', model: 'gpt-5.6-terra', endpoint: 'https://api.openai.com' },
  { label: 'GPT-5.6 Luna (OpenAI · 轻量实惠)', model: 'gpt-5.6-luna', endpoint: 'https://api.openai.com' },

  // ===== DeepSeek V4 (2026年4月发布，旧名 deepseek-chat 明日停用) =====
  { label: 'DeepSeek V4 Flash (¥0.001/M · 极致性价比)', model: 'deepseek-v4-flash', endpoint: 'https://api.deepseek.com' },
  { label: 'DeepSeek V4 Pro (旗舰推理 · 1M上下文)', model: 'deepseek-v4-pro', endpoint: 'https://api.deepseek.com' },

  // ===== Kimi K3 (2026年7月刚发布 · 2.8万亿参数开源) =====
  { label: 'Kimi K3 (月之暗面 · 2.8T开源旗舰)', model: 'kimi-k3', endpoint: 'https://api.moonshot.cn' },

  // ===== Claude (Anthropic) =====
  { label: 'Claude Fable 5 (Anthropic · 旗舰)', model: 'claude-5-fable', endpoint: 'https://api.anthropic.com' },

  // ===== 国产云平台 =====
  { label: 'Qwen 3.8 Max (阿里云 · 最新旗舰)', model: 'qwen3.8-max-preview', endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { label: 'GLM-5.2 (智谱 · 最新旗舰)', model: 'glm-5.2', endpoint: 'https://open.bigmodel.cn/api/paas/v4' },

  // ===== 自定义 =====
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
