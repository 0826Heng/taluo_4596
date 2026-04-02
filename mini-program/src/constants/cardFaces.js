/**
 * 牌面视觉元数据：与后端 content 的 card_id 对应（非真实塔罗版权图，仅为原创占位 UI）。
 * 新增牌时在此补充即可；未知 id 会走默认样式。
 */
const DEFAULT_FACE = {
  title: "秘符",
  numeral: "☆",
  accent: "violet",
};

export const CARD_FACE_MAP = {
  card_01: { title: "启明", numeral: "I", accent: "cyan" },
  card_02: { title: "共鸣", numeral: "II", accent: "violet" },
  card_03: { title: "蹊径", numeral: "III", accent: "magenta" },
  card_04: { title: "恒序", numeral: "IV", accent: "gold" },
};

export function enrichDrawItem(item) {
  const id = (item && item.cardId) || "";
  const meta = CARD_FACE_MAP[id] || DEFAULT_FACE;
  return Object.assign({}, item, {
    faceTitle: meta.title,
    faceNumeral: meta.numeral,
    faceAccent: meta.accent,
  });
}
