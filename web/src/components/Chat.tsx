import React, { useState, useRef, useEffect, useCallback } from 'react';
import type { Message, Hero } from '../types';
import { buildSystemPrompt } from '../lib/buildPrompt';
import { detectHeroes } from '../lib/heroDetect';
import { streamChat, type LLMConfig } from '../lib/llm';
import type { ApiConfig } from './ApiKeyInput';

interface Props {
  apiConfig: ApiConfig;
}

export default function Chat({ apiConfig }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是 OW Coach，你的守望先锋教练。告诉我你遇到了什么问题，我来帮你分析。' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null);
  const [detectedHeroes, setDetectedHeroes] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput('');
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setStreamingContent('');

    try {
      // 1. Detect heroes from user input
      const heroes = await detectHeroes(text);

      // 2. Build system prompt with hero context
      const { systemPrompt: sp, detectedHeroes: dh } = await buildSystemPrompt(text, heroes);
      setSystemPrompt(sp);
      setDetectedHeroes(dh.map(h => h.name_cn));

      // 3. Prepare all messages for API
      const llmConfig: LLMConfig = {
        endpoint: apiConfig.endpoint,
        model: apiConfig.model,
        key: apiConfig.key,
      };

      // Build context: include existing messages but don't send system prompt (it's in the API call)
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

  const renderContent = (content: string) => {
    // Simple markdown-like rendering for now
    // react-markdown is imported but we'll use basic formatting
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
      <div className="chat-header">
        <h1>OW Coach</h1>
        <span className="subtitle">守望先锋 AI 教练</span>
        {detectedHeroes.length > 0 && (
          <span className="detected-badge">
            检测到：{detectedHeroes.join('、')}
          </span>
        )}
      </div>

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
