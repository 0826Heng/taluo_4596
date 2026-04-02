import { COPY } from "../../constants/copy";
import { listHistory } from "../../services/tarotApi";

Page({
  data: {
    title: COPY.history.title,
    emptyHint: COPY.history.emptyHint,
    items: [],
    cursor: "",
    loading: false,
  },

  async onLoad() {
    await this.fetchPage(true);
  },

  async fetchPage(reset) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    try {
      const cursor = reset ? "" : this.data.cursor;
      const res = await listHistory({ cursor: cursor });
      const nextCursor = res.nextCursor || "";

      this.setData({
        items: reset ? res.items : [...this.data.items, ...res.items],
        cursor: nextCursor,
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  async onLoadMore() {
    await this.fetchPage(false);
  },

  async onPullDownRefresh() {
    await this.fetchPage(true);
    wx.stopPullDownRefresh();
  },
});

