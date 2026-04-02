import { COPY } from "../../constants/copy";
import { ROUTES, navigateTo } from "../../utils/router";

type Option = { id: string; label: string };

Page({
  data: {
    title: COPY.home.chooseSpread,
    themes: [
      { id: "theme_relationship", label: "关系" },
      { id: "theme_career", label: "事业" },
      { id: "theme_learning", label: "学习" },
      { id: "theme_growth", label: "自我成长" },
    ] as Option[],
    spreads: [
      { id: "spread_three_cards", label: "三张阵" },
      { id: "spread_celtic_cross", label: "十字阵" },
      { id: "spread_single", label: "单张指引" },
    ] as Option[],
    selectedThemeId: "theme_relationship",
    selectedSpreadId: "spread_three_cards",
  },

  onThemeChange(e: any) {
    this.setData({ selectedThemeId: e.detail.value });
  },

  onSpreadChange(e: any) {
    this.setData({ selectedSpreadId: e.detail.value });
  },

  onConfirm() {
    navigateTo(ROUTES.reading, {
      themeId: this.data.selectedThemeId,
      spreadId: this.data.selectedSpreadId,
    });
  },
});

