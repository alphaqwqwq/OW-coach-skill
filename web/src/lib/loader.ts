import type { Hero, CnNames, Prompts, StrategyText } from '../types';

let _heroes: Hero[] | null = null;
let _heroesMap: Map<string, Hero> | null = null;
let _cnNames: CnNames | null = null;
let _cnToHero: Map<string, Hero> | null = null;
let _prompts: Prompts | null = null;
let _fandomCache: Map<string, string> | null = null;

async function loadJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
  return res.json();
}

export async function ensureHeroes(): Promise<Hero[]> {
  if (_heroes) return _heroes;
  _heroes = await loadJSON<Hero[]>('./data/heroes.json');
  _heroesMap = new Map(_heroes.map(h => [h.id, h]));
  return _heroes;
}

export async function ensureCnNames(): Promise<Map<string, Hero>> {
  if (_cnToHero) return _cnToHero;
  const heroes = await ensureHeroes();
  _cnNames = await loadJSON<CnNames>('./data/cn_names.json');
  _cnToHero = new Map();
  for (const [cn, en] of Object.entries(_cnNames)) {
    const h = _heroesMap?.get(en);
    if (h) _cnToHero.set(cn.toLowerCase(), h);
  }
  return _cnToHero;
}

export async function ensurePrompts(): Promise<Prompts> {
  if (_prompts) return _prompts;
  _prompts = await loadJSON<Prompts>('./data/prompts.json');
  return _prompts;
}

export async function loadFandom(id: string): Promise<string | null> {
  if (!_fandomCache) _fandomCache = new Map();
  if (_fandomCache.has(id)) return _fandomCache.get(id) || null;
  try {
    const data = await loadJSON<StrategyText>(`./data/fandom/${id}_strategy.json`);
    _fandomCache.set(id, data.text);
    return data.text;
  } catch {
    _fandomCache.set(id, '');
    return null;
  }
}

export async function loadStats(id: string): Promise<Record<string, any> | null> {
  try {
    return await loadJSON<Record<string, any>>(`./data/stats/${id}_stats.json`);
  } catch {
    return null;
  }
}
