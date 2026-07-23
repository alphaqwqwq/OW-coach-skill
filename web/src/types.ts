export interface HeroSkill {
  key: string;
  name: string;
  desc: string;
}

export interface Hero {
  id: string;
  keys: string[];
  name_cn: string;
  role: string;
  subrole: string;
  summary: string;
  hp: number;
  skills: HeroSkill[];
}

export interface HeroesData {
  [id: string]: Hero;
}

export interface StrategyText {
  text: string;
  source: string;
}

export interface FandomData {
  [id: string]: StrategyText;
}

export interface StatsData {
  [id: string]: Record<string, any>;
}

export interface CnNames {
  [cnName: string]: string;
}

export interface Prompts {
  system: string;
  framework: string;
  knowledge: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  streamingContent: string;
}

export interface ApiKeyInfo {
  key: string;
  endpoint: string;
  model: string;
}
