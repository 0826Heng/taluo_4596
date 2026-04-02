import { callContainer } from "./cloudClient";
import { CLOUD } from "../constants/cloud";
import type {
  TarotHistoryItem,
  TarotReadingResponse,
  DrawResultItem,
  Lang,
} from "./types";

const isMockMode = () => {
  if (CLOUD.useLocalMock === true) return true;
  return (CLOUD.resourceEnv || "").startsWith("YOUR_");
};

const MOCK_SPREAD_POSITIONS: Record<string, string[]> = {
  spread_three_cards: ["位置1", "位置2", "位置3"],
  spread_celtic_cross: ["中心", "挑战", "助力", "过去", "未来", "上方", "下方", "自我", "环境", "结果"],
  spread_single: ["指引"],
};

const MOCK_MEANINGS: Record<
  string,
  { upright: string; reversed: string }
> = {
  card_01: {
    upright: "象征启示：它提醒你关注当下的选择与感受。",
    reversed: "象征启示：它也许在提醒你放慢节奏，避免把焦虑带进行动。",
  },
  card_02: {
    upright: "象征启示：你可以从细节中找到更合适的沟通方式。",
    reversed: "象征启示：它可能意味着需要重新校准边界与期待。",
  },
  card_03: {
    upright: "象征启示：给出小步尝试，往往比一次性下定论更有效。",
    reversed: "象征启示：它也可能提示你先梳理资源与优先级，再继续前进。",
  },
  card_04: {
    upright: "象征启示：当你把注意力放在过程，结果也会更稳定。",
    reversed: "象征启示：它可能提醒你别忽略内心的节奏变化。",
  },
};

function hashToUint32(input: string): number {
  // 简单稳定 hash：只用于 mock 生成“看起来不同但可复现”的结果
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

async function mockCreateReading(
  req: TarotReadingRequest
): Promise<TarotReadingResponse> {
  const positions = MOCK_SPREAD_POSITIONS[req.spreadId] ?? ["位置1", "位置2", "位置3"];
  const cards = Object.keys(MOCK_MEANINGS);
  const seed = hashToUint32(req.clientNonce + "|" + req.spreadId + "|" + req.themeId);

  const drawResult: DrawResultItem[] = positions.map((positionKey, idx) => {
    const cardId = cards[(seed + idx) % cards.length];
    const upright = ((seed + idx * 13) % 2) === 0;
    const meaning = upright ? MOCK_MEANINGS[cardId].upright : MOCK_MEANINGS[cardId].reversed;

    return {
      positionKey,
      cardId,
      upright,
      interpretation: meaning,
    };
  });

  return {
    drawResult,
    sessionId: "mock-" + req.clientNonce,
    contentVersion: "cards_v0|spreads_v0",
  };
}

const mockHistoryStore: TarotHistoryItem[] = [];
const mockSessions: Record<string, TarotHistoryItem> = {};

async function mockSaveReflection(
  req: { sessionId: string; reflectionText: string; tags?: string[] }
): Promise<{ ok: true }> {
  const summary = (req.reflectionText || "").trim().slice(0, 80);
  const createdAt = new Date().toISOString();

  // 解析 sessionId（mock sessionId: mock-xxx）
  const sessionId = req.sessionId;
  const themeId = "theme_relationship";
  const spreadId = "spread_three_cards";

  const item: TarotHistoryItem = {
    sessionId,
    createdAt,
    themeId,
    spreadId,
    reflectionSummary: summary,
  };

  mockSessions[sessionId] = item;
  // 若已存在则覆盖
  const i = mockHistoryStore.findIndex((x) => x.sessionId === sessionId);
  if (i >= 0) mockHistoryStore[i] = item;
  else mockHistoryStore.unshift(item);

  return { ok: true };
}

async function mockListHistory(opts?: { cursor?: string }): Promise<{
  items: TarotHistoryItem[];
  nextCursor: string | null;
}> {
  const cursor = Number(opts?.cursor ?? 0);
  const page = mockHistoryStore.slice(cursor, cursor + 20);
  return { items: page, nextCursor: null };
}

export interface TarotReadingRequest {
  spreadId: string;
  themeId: string;
  // 可选：用于自定义每个位置的解读引导
  positions?: string[];
  clientNonce: string;
  lang?: Lang;
}

export async function createReading(
  req: TarotReadingRequest
): Promise<TarotReadingResponse> {
  if (isMockMode()) {
    return mockCreateReading(req);
  }
  try {
    const res = await callContainer<TarotReadingResponse>({
      path: "/v1/tarot/reading",
      method: "POST",
      data: req as any,
    });
    if (res && Array.isArray(res.drawResult)) {
      return res;
    }
  } catch (e) {
    console.warn("createReading callContainer failed, fallback mock", e);
  }
  return mockCreateReading(req);
}

export interface SaveReflectionRequest {
  sessionId: string;
  reflectionText: string;
  tags?: string[];
}

export async function saveReflection(
  req: SaveReflectionRequest
): Promise<{ ok: true }> {
  if (isMockMode()) {
    return mockSaveReflection(req);
  }
  return callContainer<{ ok: true }>({
    path: "/v1/tarot/history",
    method: "POST",
    data: req as any,
  });
}

export interface ListHistoryResponse {
  items: TarotHistoryItem[];
  nextCursor: string | null;
}

export async function listHistory(opts: {
  cursor?: string;
}): Promise<ListHistoryResponse> {
  if (isMockMode()) {
    return mockListHistory(opts);
  }
  const cursor = opts.cursor ?? "";
  return callContainer<ListHistoryResponse>({
    path: `/v1/tarot/history?cursor=${encodeURIComponent(cursor)}`,
    method: "GET",
    data: {},
  });
}

export interface TodayResponse {
  dateKey: string;
  themeId: string;
  spreadId: string;
}

export async function getTodayTheme(opts?: {
  date?: string;
  themePreference?: string;
}): Promise<TodayResponse> {
  if (isMockMode()) {
    return {
      dateKey: opts?.date ?? new Date().toISOString().slice(0, 10),
      themeId: "theme_learning",
      spreadId: "spread_single",
    };
  }
  const date = opts?.date ?? "";
  const themePreference = opts?.themePreference ?? "";

  // 约定：GET 参数通过 data 传递也可；此处按你后端解析策略调整。
  return callContainer<TodayResponse>({
    path: "/v1/tarot/today",
    method: "POST",
    data: {
      date: date || undefined,
      themePreference: themePreference || undefined,
    } as any,
  });
}

export interface ContentVersionResponse {
  tarotCardsVersion: string;
  spreadsVersion: string;
  updatedAt: string;
}

export async function getAdminContentVersion(): Promise<ContentVersionResponse> {
  if (isMockMode()) {
    return {
      tarotCardsVersion: "v0",
      spreadsVersion: "v0",
      updatedAt: "2026-04-02T00:00:00Z",
    };
  }
  return callContainer<ContentVersionResponse>({
    path: "/v1/admin/content/version",
    method: "GET",
    data: {},
  });
}

