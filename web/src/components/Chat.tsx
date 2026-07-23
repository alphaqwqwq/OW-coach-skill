import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { Message } from '../types';
import { buildSystemPrompt } from '../lib/buildPrompt';
import { detectHeroes } from '../lib/heroDetect';
import { streamChat, type LLMConfig } from '../lib/llm';
import type { ApiConfig } from './ApiKeyInput';

const HISTORY_KEY = 'ow_coach_history';
const WELCOME_MSG = '你好！我是 OW Coach，你的守望先锋教练。告诉我你遇到了什么问题，我来帮你分析。';

interface HistoryData {
  messages: Message[];
  updatedAt: string;
}

interface Props {
  apiConfig: ApiConfig;
}

// 读取 localStorage 中的历史记录
function loadHistory(): Message[] | null {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as HistoryData;
    if (Array.isArray(data.messages) && data.messages.length > 0) {
      return data.messages;
    }
  } catch { /* ignore */ }
  return null;
}

// 保存历史记录到 localStorage
function saveHistory(messages: Message[]) {
  try {
    const data: HistoryData = { messages, updatedAt: new Date().toISOString() };
    localStorage.setItem(HISTORY_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

// 清除历史记录
function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}

export default function Chat({ apiConfig }: Props) {
  const [messages, setMessages] = useState<Message[]>(() => {
    return loadHistory() || [{ role: 'assistant', content: WELCOME_MSG }];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [detectedHeroes, setDetectedHeroes] = useState<string[]>([]);
  const [showMenu, setShowMenu] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // 自动保存
  useEffect(() => {
    saveHistory(messages);
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput('');
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setStreamingContent('');

    try {
      const heroes = await detectHeroes(text);
      const { systemPrompt: sp, detectedHeroes: dh } = await buildSystemPrompt(text, heroes);
      setDetectedHeroes(dh.map(h => h.name_cn));

      const llmConfig: LLMConfig = {
        endpoint: apiConfig.endpoint,
        model: apiConfig.model,
        key: apiConfig.key,
      };

      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const allMsgs = [...history, userMsg];

      let fullResponse = '';
      await streamChat(llmConfig, sp, allMsgs, {
        onToken: (token) => {
          fullResponse += token;
          setStreamingContent(fullResponse);
        },
        onDone: () => {
          setMessages(prev => [...prev, { role: 'assistant', content: fullResponse }]);
          setStreamingContent('');
          setIsLoading(false);
        },
        onError: (err) => {
          const errMsg = `**API 请求出错**：${err.message}\n\n请检查：\n1. API Key 是否正确\n2. Endpoint 地址是否正确\n3. 模型名是否可用`;
          setMessages(prev => [...prev, { role: 'assistant', content: errMsg }]);
          setStreamingContent('');
          setIsLoading(false);
        },
      });
    } catch (err) {
      const errMsg = `**发生错误**：${err instanceof Error ? err.message : String(err)}`;
      setMessages(prev => [...prev, { role: 'assistant', content: errMsg }]);
      setStreamingContent('');
      setIsLoading(false);
    }
  }, [input, isLoading, messages, apiConfig]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 导出历史
  const handleExport = () => {
    const data: HistoryData = { messages, updatedAt: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const dateStr = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `ow-coach-history-${dateStr}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setShowMenu(false);
  };

  // 导入历史
  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target?.result as string) as HistoryData;
        if (Array.isArray(data.messages) && data.messages.length > 0) {
          setMessages(data.messages);
          setShowMenu(false);
        } else {
          alert('文件格式不正确：未找到有效的聊天记录');
        }
      } catch {
        alert('文件解析失败，请确认是 OW Coach 导出的 JSON 文件');
      }
    };
    reader.readAsText(file);
    // 重置 input，允许重复选同文件
    e.target.value = '';
  };

  // 清空历史
  const handleClear = () => {
    if (messages.length <= 1) return;
    if (!confirm('确定清空所有聊天记录吗？此操作不可撤销。')) return;
    clearHistory();
    setMessages([{ role: 'assistant', content: WELCOME_MSG }]);
    setDetectedHeroes([]);
    setShowMenu(false);
  };

  const renderContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('## ')) {
        return <h3 key={i}>{line.slice(3)}</h3>;
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return <strong key={i}>{line.slice(2, -2)}</strong>;
      }
      if (line.startsWith('- **')) {
        const match = line.match(/- \*\*(.+?)\*\*：?(.*)/);
        if (match) {
          return <div key={i} className="msg-line"><strong>{match[1]}</strong>{match[2] ? `：${match[2]}` : ''}</div>;
        }
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={i} className="msg-li">{line.slice(2)}</li>;
      }
      if (line.trim() === '') {
        return <div key={i} className="msg-spacer" />;
      }
      return <div key={i} className="msg-line">{line}</div>;
    });
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h1>OW Coach</h1>
        <span className="subtitle">守望先锋 AI 教练</span>

        <div className="header-menu-area">
          <button className="btn-menu" onClick={() => setShowMenu(!showMenu)} title="更多操作">
            ⋯
          </button>
          {showMenu && (
            <div className="menu-dropdown">
              <button className="menu-item" onClick={handleExport}>📥 导出聊天记录</button>
              <button className="menu-item" onClick={() => fileInputRef.current?.click()}>📤 导入聊天记录</button>
              {messages.length > 1 && (
                <button className="menu-item menu-danger" onClick={handleClear}>🗑️ 清空记录</button>
              )}
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={handleImport}
          />
        </div>

        {detectedHeroes.length > 0 && (
          <span className="detected-badge">
            {detectedHeroes.join('、')}
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="avatar">{msg.role === 'assistant' ? '🤖' : '👤'}</div>
            <div className="bubble">
              {renderContent(msg.content)}
            </div>
          </div>
        ))}
        {isLoading && streamingContent && (
          <div className="message assistant">
            <div className="avatar">🤖</div>
            <div className="bubble streaming">
              {renderContent(streamingContent)}
              <span className="cursor" />
            </div>
          </div>
        )}
        {isLoading && !streamingContent && (
          <div className="message assistant">
            <div className="avatar">🤖</div>
            <div className="bubble">
              <span className="thinking-dots">思考中<span className="dot1">.</span><span className="dot2">.</span><span className="dot3">.</span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述你的对局情况，比如：我用死神对面是双长枪加雾子安娜..."
          rows={3}
          disabled={isLoading}
        />
        <button
          className="btn-send"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '...' : '发送'}
        </button>
      </div>
    </div>
  );
}
