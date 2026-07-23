import type { Hero } from '../types';
import { ensurePrompts, loadFandom, loadStats } from './loader';

export interface BuildPromptResult {
  systemPrompt: string;
  detectedHeroes: { id: string; name_cn: string; role: string }[];
}

/**
 * Build the full system prompt by injecting hero context for detected heroes.
 * This mirrors agent.py's _collect_hero_context logic.
 */
export async function buildSystemPrompt(
  userInput: string,
  detectedHeroes: Hero[]
): Promise<BuildPromptResult> {
  const prompts = await ensurePrompts();
  let system = prompts.system;

  // Add knowledge and framework
  system += '\n\n## 教练方法论\n' + prompts.framework;
  system += '\n\n## 知识置信度\n' + prompts.knowledge;

  // Inject hero context for each detected hero
  for (const hero of detectedHeroes) {
    const ctx = await buildHeroContext(hero);
    if (ctx) {
      system += '\n\n' + ctx;
    }
  }

  return {
    systemPrompt: system,
    detectedHeroes: detectedHeroes.map(h => ({
      id: h.id,
      name_cn: h.name_cn || h.id,
      role: h.summary || h.role
    }))
  };
}

async function buildHeroContext(hero: Hero): Promise<string | null> {
  const sections: string[] = [];
  const heroLabel = `${hero.name_cn || hero.id}（${hero.summary || hero.role}）`;

  // 1. Basic info block
  let info = `## 英雄档案：${heroLabel}\n`;
  info += `- 英雄ID：${hero.id}\n`;
  info += `- 定位：${hero.role} · ${hero.subrole || ''}\n`;
  info += `- HP：${hero.hp}\n`;
  info += `- 技能数：${hero.skills.length}\n`;

  // 2. Skills
  if (hero.skills.length > 0) {
    info += '\n### 技能列表\n';
    for (const skill of hero.skills) {
      const desc = skill.desc ? skill.desc.replace(/\|/g, '·').trim() : '（无描述）';
      // Clean up raw desc - keep first ~150 chars for context injection
      const cleanDesc = desc.length > 200 ? desc.substring(0, 200) + '…' : desc;
      info += `- **${skill.key}** ${skill.name}：${cleanDesc}\n`;
    }
  }
  sections.push(info);

  // 3. Numerical stats
  try {
    const stats = await loadStats(hero.id);
    if (stats && Object.keys(stats).length > 0) {
      let statsBlock = '\n### 数值数据\n';
      const entries = Object.entries(stats).slice(0, 30);
      for (const [key, val] of entries) {
        if (typeof val === 'object') {
          statsBlock += `- ${key}：${JSON.stringify(val)}\n`;
        } else {
          statsBlock += `- ${key}：${val}\n`;
        }
      }
      sections.push(statsBlock);
    }
  } catch {
    // silent
  }

  // 4. Strategy text from Fandom
  try {
    const strategy = await loadFandom(hero.id);
    if (strategy && strategy.length > 0) {
      // Take first ~500 chars for compactness
      const truncated = strategy.length > 500 ? strategy.substring(0, 500) + '…' : strategy;
      sections.push(`\n### 社区攻略摘要\n${truncated}`);
    }
  } catch {
    // silent
  }

  return sections.join('\n');
}
