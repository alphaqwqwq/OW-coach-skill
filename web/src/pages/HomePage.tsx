import React from 'react';

interface ToolCardDef {
  id: string;
  icon: string;
  title: string;
  desc: string;
  tags: string[];
  status: 'ready' | 'soon';
  onClick: () => void;
}

interface Props {
  onNavigate: (page: string) => void;
}

export default function HomePage({ onNavigate }: Props) {
  const tools: ToolCardDef[] = [
    {
      id: 'ow-coach',
      icon: '🎮',
      title: 'OW Coach',
      desc: '守望先锋 AI 教练。根据英雄克制关系、数值数据和社区攻略，分析你的对局并提供战术建议。',
      tags: ['Overwatch 2', 'AI', '对战分析'],
      status: 'ready',
      onClick: () => onNavigate('ow-coach'),
    },
    {
      id: 'more-coming',
      icon: '🔧',
      title: '更多工具',
      desc: '后续集成更多小工具……',
      tags: ['开发中'],
      status: 'soon',
      onClick: () => {},
    },
  ];

  return (
    <div className="home-page">
      <header className="home-header">
        <div className="brand">
          <span className="brand-icon">⚡</span>
          <span className="brand-name">alphaqwq</span>
          <span className="brand-dot">·</span>
          <span className="brand-tag">工具集</span>
        </div>
        <p className="home-subtitle">一些可能有用的小工具</p>
      </header>

      <main className="tool-grid">
        {tools.map(tool => (
          <button
            key={tool.id}
            className={`tool-card ${tool.status === 'soon' ? 'tool-card--soon' : ''}`}
            onClick={tool.onClick}
            disabled={tool.status === 'soon'}
          >
            <div className="tool-icon">{tool.icon}</div>
            <div className="tool-body">
              <h2 className="tool-title">
                {tool.title}
                {tool.status === 'soon' && <span className="tool-badge">即将到来</span>}
              </h2>
              <p className="tool-desc">{tool.desc}</p>
              <div className="tool-tags">
                {tool.tags.map(tag => (
                  <span key={tag} className="tool-tag">{tag}</span>
                ))}
              </div>
            </div>
            <div className="tool-arrow">→</div>
          </button>
        ))}
      </main>

      <footer className="home-footer">
        <p>纯前端 · 数据本地存储 · 自带 API Key</p>
      </footer>
    </div>
  );
}
