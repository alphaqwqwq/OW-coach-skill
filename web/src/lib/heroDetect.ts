import type { Hero } from '../types';
import { ensureHeroes, ensureCnNames } from './loader';

/**
 * Detect which heroes are mentioned in user input.
 * Matches by:
 * - Chinese name (cn_names.json mapping)
 * - English hero ID
 * - Partial match in whitespace-delimited tokens
 */
export async function detectHeroes(input: string): Promise<Hero[]> {
  const lower = input.toLowerCase();
  const found = new Set<string>();
  const result: Hero[] = [];

  // 1. Match by Chinese name
  const cnMap = await ensureCnNames();
  for (const [cn, hero] of cnMap.entries()) {
    if (lower.includes(cn)) {
      if (!found.has(hero.id)) {
        found.add(hero.id);
        result.push(hero);
      }
    }
  }

  // 2. Match by English ID from heroes list
  const heroes = await ensureHeroes();
  const tokens = lower.split(/\s+/);
  for (const hero of heroes) {
    if (found.has(hero.id)) continue;
    // Match exact ID
    if (tokens.includes(hero.id)) {
      found.add(hero.id);
      result.push(hero);
      continue;
    }
    // Match by keys array
    for (const key of hero.keys) {
      if (key !== hero.id && tokens.includes(key.toLowerCase())) {
        found.add(hero.id);
        result.push(hero);
        break;
      }
    }
  }

  return result;
}
