import { COPY } from "../../constants/copy";
import { enrichDrawItem } from "../../constants/cardFaces";
import { createReading, saveReflection } from "../../services/tarotApi";

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
    cards: [],

    reflectionText: "",
    isSavingReflection: false,
    isRevealing: false,
  },

  onLoad(options) {
    const themeId = (options && options.themeId) || "";
    const spreadId = (options && options.spreadId) || "";
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
        spreadId: spreadId,
        themeId: themeId,
        clientNonce: genNonce(),
        lang: "zh",
      });
      const raw = res && Array.isArray(res.drawResult) ? res.drawResult : [];
      if (!raw.length) {
        wx.showToast({ title: "未获取到牌面数据，请重试", icon: "none" });
        return;
      }
      const cards = raw.map((c) =>
        Object.assign({}, enrichDrawItem(c), { faceUp: false })
      );
      this.setData({
        sessionId: res.sessionId || "",
        contentVersion: res.contentVersion || "",
        cards: cards,
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
        sessionId: sessionId,
        reflectionText: reflectionText,
      });
      wx.showToast({ title: "已保存复盘", icon: "success" });
      this.setData({ reflectionText: "" });
    } finally {
      this.setData({ isSavingReflection: false });
    }
  },

  onReflectionInput(e) {
    const v = (e && e.detail && e.detail.value) || "";
    this.setData({ reflectionText: v });
  },

  onCardFlip(e) {
    const idx = Number((e.currentTarget && e.currentTarget.dataset && e.currentTarget.dataset.idx));
    if (Number.isNaN(idx) || idx < 0) return;
    const cards = this.data.cards.slice();
    const row = cards[idx];
    if (!row) return;
    const next = !row.faceUp;
    cards[idx] = Object.assign({}, row, { faceUp: next });
    this.setData({ cards: cards });
    if (next && wx.vibrateShort) {
      try {
        wx.vibrateShort({ type: "light" });
      } catch (err) {
        /* ignore */
      }
    }
  },
});

