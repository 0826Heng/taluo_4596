export type Lang = "zh";

export type TarotPositionKey = string;

export interface DrawResultItem {
  positionKey: TarotPositionKey;
  cardId: string;
  upright: boolean;
  interpretation: string; // 服务器端渲染后的文本
  /** 前端 enrich 后填充，用于牌卡 UI */
  faceTitle?: string;
  faceNumeral?: string;
  faceAccent?: (
    | "cyan"
    | "violet"
    | "magenta"
    | "gold"
    | string
  );
  /** 是否已翻到牌面（牌背为 false） */
  faceUp?: boolean;
}

export interface TarotReadingResponse {
  drawResult: DrawResultItem[];
  sessionId: string;
  contentVersion: string;
}

export interface TarotHistoryItem {
  sessionId: string;
  createdAt: string; // ISO
  themeId: string;
  spreadId: string;
  reflectionSummary: string;
}

