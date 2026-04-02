import { COPY } from "../../constants/copy";
import { enrichDrawItem } from "../../constants/cardFaces";
import { createReading, saveReflection } from "../../services/tarotApi";
import type { DrawResultItem } from "../../services/types";

function genNonce() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

Page({
  data: {
    title: COPY.reading.title,
    actionFlip: COPY.reading.actionFlip,
    optionalReflection: COPY.reading.optionalReflection,
    ctaSaveReflection: COPY.reading.ctaSaveReflection,
    disclaimer: COPY.result.disclaimer,

    themeId: "",
    spreadId: "",
    sessionId: "",
    contentVersion: "",

    revealed: false,
    cards: [] as DrawResultItem[],

    reflectionText: "",
    isSavingReflection: false,
    isRevealing: false,
  },

  async onLoad(options: any) {
    const themeId = options?.themeId ?? "";
    const spreadId = options?.spreadId ?? "";
    this.setData({ themeId, spreadId });
  },

  async onRevealAll() {
    const { themeId, spreadId } = this.data;
    if (!themeId || !spreadId) {
      wx.showToast({ title: "请选择主题与牌阵", icon: "none" });
      return;
    }
    if (this.data.isRevealing) return;
    this.setData({ isRevealing: true });
    try {
      const res = await createReading({
        spreadId,
        themeId,
        clientNonce: genNonce(),
        lang: "zh",
      });
      const raw = Array.isArray(res.drawResult) ? res.drawResult : [];
      if (!raw.length) {
        wx.showToast({ title: "未获取到牌面数据，请重试", icon: "none" });
        return;
      }
      const cards = raw.map((c) => ({
        ...enrichDrawItem(c),
        faceUp: false,
      }));
      this.setData({
        sessionId: res.sessionId,
        contentVersion: res.contentVersion,
        cards: cards as DrawResultItem[],
        revealed: true,
      });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: "呈现失败，请检查网络或稍后重试", icon: "none" });
    } finally {
      this.setData({ isRevealing: false });
    }
  },

  async onSaveReflection() {
    const { sessionId, reflectionText } = this.data;
    if (!sessionId) {
      wx.showToast({ title: "请先完成本次呈现", icon: "none" });
      return;
    }
    if (!reflectionText || !reflectionText.trim()) {
      wx.showToast({ title: "请输入复盘笔记（可选但建议）", icon: "none" });
      return;
    }
    if (this.data.isSavingReflection) return;

    this.setData({ isSavingReflection: true });
    try {
      await saveReflection({
        sessionId,
        reflectionText,
      });
      wx.showToast({ title: "已保存复盘", icon: "success" });
      this.setData({ reflectionText: "" });
    } finally {
      this.setData({ isSavingReflection: false });
    }
  },

  onReflectionInput(e: any) {
    this.setData({ reflectionText: e?.detail?.value ?? "" });
  },

  onCardFlip(e: any) {
    const idx = Number(e?.currentTarget?.dataset?.idx);
    if (Number.isNaN(idx) || idx < 0) return;
    const cards = this.data.cards.slice();
    const row = cards[idx];
    if (!row) return;
    const next = !row.faceUp;
    cards[idx] = { ...row, faceUp: next };
    this.setData({ cards: cards as DrawResultItem[] });
    if (next) {
      try {
        wx.vibrateShort?.({ type: "light" });
      } catch {
        /* ignore */
      }
    }
  },
});

