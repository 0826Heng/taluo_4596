import type { DrawResultItem } from "../services/types";

const DEFAULT_FACE = {
  title: "秘符",
  numeral: "☆",
  accent: "violet",
} as const;

export const CARD_FACE_MAP: Record<
  string,
  { title: string; numeral: string; accent: string }
> = {
  card_01: { title: "启明", numeral: "I", accent: "cyan" },
  card_02: { title: "共鸣", numeral: "II", accent: "violet" },
  card_03: { title: "蹊径", numeral: "III", accent: "magenta" },
  card_04: { title: "恒序", numeral: "IV", accent: "gold" },
};

export type EnrichedDrawItem = DrawResultItem & {
  faceTitle: string;
  faceNumeral: string;
  faceAccent: string;
};

export function enrichDrawItem(item: DrawResultItem): EnrichedDrawItem {
  const id = item.cardId || "";
  const meta = CARD_FACE_MAP[id] || DEFAULT_FACE;
  return {
    ...item,
    faceTitle: meta.title,
    faceNumeral: meta.numeral,
    faceAccent: meta.accent,
  };
}
