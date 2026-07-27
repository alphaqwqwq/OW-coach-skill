import os, json

BASE = r'd:\workspace\alphaqwq-home'
SRC = os.path.join(BASE, 'src')
os.makedirs(SRC, exist_ok=True)

# index.html
with open(os.path.join(BASE, 'index.html'), 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>alphaqwq · 工具集</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
''')

# src/main.tsx
with open(os.path.join(SRC, 'main.tsx'), 'w', encoding='utf-8') as f:
    f.write('''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
''')

# src/vite-env.d.ts
with open(os.path.join(SRC, 'vite-env.d.ts'), 'w', encoding='utf-8') as f:
    f.write('/// <reference types="vite/client" />\n')

# App.tsx
with open(os.path.join(SRC, 'App.tsx'), 'w', encoding='utf-8') as f:
    f.write('''import React from 'react'
import './App.css'

interface ToolCard {
  id: string
  icon: string
  title: string
  desc: string
  url: string
  tags: string[]
}

const TOOLS: ToolCard[] = [
  {
    id: 'ow-coach',
    icon: '🎮',
    title: 'OW Coach',
    desc: '守望先锋 AI 教练。根据英雄克制关系、数值数据和社区攻略，分析对局并提供战术建议。',
    url: '/',
    tags: ['Overwatch 2', 'AI', '对战分析'],
  },
  {
    id: 'team-balancer',
    icon: '⚔️',
    title: '随机分队器',
    desc: '守望先锋位置感知分队工具。录入玩家段位，自动生成平衡队伍，支持 4v4 / 5v5 / 6v6。',
    url: 'https://tb.alphaqwq.xyz',
    tags: ['Overwatch 2', '分队', '平衡'],
  },
  {
    id: 'more',
    icon: '🔧',
    title: '更多工具',
    desc: '更多小工具正在开发中……',
    url: '#',
    tags: ['开发中'],
  },
]

export default function App() {
  const handleClick = (url: string) => {
    if (url !== '#') window.location.href = url
  }

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          <span className="brand-icon">⚡</span>
          <span className="brand-name">alphaqwq</span>
          <span className="brand-tagline">一些小工具</span>
        </div>
      </header>

      <main className="grid">
        {TOOLS.map(tool => (
          <button
            key={tool.id}
            className="card"
            onClick={() => handleClick(tool.url)}
            disabled={tool.url === '#'}
          >
            <div className="card-icon">{tool.icon}</div>
            <div className="card-body">
              <h2 className="card-title">{tool.title}</h2>
              <p className="card-desc">{tool.desc}</p>
              <div className="card-tags">
                {tool.tags.map(t => <span key={t} className="tag">{t}</span>)}
              </div>
            </div>
            <div className="card-arrow">{'>'}</div>
          </button>
        ))}
      </main>

      <footer className="footer">
        <a href="https://github.com/alphaqwqwq" target="_blank" rel="noopener noreferrer">GitHub</a>
        <span className="footer-sep">·</span>
        <span>纯前端工具集</span>
      </footer>
    </div>
  )
}
''')

# App.css
with open(os.path.join(SRC, 'App.css'), 'w', encoding='utf-8') as f:
    f.write(''':root {
  --bg: #0a0a0f;
  --bg-card: #12121a;
  --bg-hover: #1a1a2e;
  --text: #e8e8f0;
  --text-dim: #8888a0;
  --text-muted: #555568;
  --accent: #f0c040;
  --border: #2a2a3a;
  --radius: 12px;
  --radius-sm: 8px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #root { height: 100%; width: 100%; }
body {
  font-family: var(--font);
  background: radial-gradient(ellipse at 50% 0%, #12121a 0%, #0a0a0f 70%);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page { flex: 1; display: flex; flex-direction: column; max-width: 540px; margin: 0 auto; width: 100%; padding: 0 20px; }

.header { text-align: center; padding: 48px 0 32px; }
.brand { display: flex; align-items: center; justify-content: center; gap: 8px; }
.brand-icon { font-size: 28px; }
.brand-name { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
.brand-tagline { font-size: 14px; color: var(--text-dim); margin-top: 6px; font-weight: 400; }

.grid { flex: 1; display: flex; flex-direction: column; gap: 10px; padding-bottom: 32px; }

.card {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 18px;
  cursor: pointer; transition: all 0.2s;
  text-align: left; width: 100%;
  font-family: var(--font); color: var(--text);
}
.card:hover:not(:disabled) { border-color: var(--accent); transform: translateY(-1px); }
.card:disabled { opacity: 0.5; cursor: not-allowed; border-style: dashed; }
.card-icon {
  width: 44px; height: 44px; border-radius: var(--radius-sm);
  background: var(--bg); display: flex; align-items: center;
  justify-content: center; font-size: 22px; flex-shrink: 0;
}
.card-body { flex: 1; min-width: 0; }
.card-title { font-size: 15px; font-weight: 700; margin-bottom: 3px; display: flex; align-items: center; gap: 8px; }
.card-desc { font-size: 13px; color: var(--text-dim); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-tags { display: flex; gap: 5px; margin-top: 6px; flex-wrap: wrap; }
.tag { font-size: 11px; padding: 1px 7px; border-radius: 5px; background: var(--bg); color: var(--text-muted); }
.card-arrow { font-size: 16px; color: var(--text-muted); flex-shrink: 0; font-weight: 700; }
.card:hover:not(:disabled) .card-arrow { color: var(--accent); transform: translateX(3px); }

.footer { text-align: center; padding: 20px; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border); }
.footer a { color: var(--text-dim); text-decoration: none; }
.footer a:hover { color: var(--accent); }
.footer-sep { margin: 0 8px; }

@media (max-width: 480px) {
  .header { padding: 32px 0 24px; }
  .brand-name { font-size: 22px; }
  .page { padding: 0 16px; }
}
''')

# .gitignore
with open(os.path.join(BASE, '.gitignore'), 'w', encoding='utf-8') as f:
    f.write('node_modules/\ndist/\ntsconfig.tsbuildinfo\n')

print('ALL FILES CREATED')
print('Dir:', os.listdir(BASE))
print('Src:', os.listdir(SRC) if os.path.isdir(SRC) else 'N/A')
