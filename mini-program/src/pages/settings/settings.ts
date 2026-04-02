import { COPY } from "../../constants/copy";

Page({
  data: {
    title: COPY.settings.title,
    disclaimerTitle: COPY.settings.disclaimerTitle,
    clearMyData: COPY.settings.clearMyData,
    privacyNote: COPY.settings.privacyNote,
  },

  async onClearData() {
    wx.showModal({
      title: COPY.settings.title,
      content: "确定要删除你的历史与复盘记录吗？",
      confirmText: "删除",
      cancelText: "取消",
      success: async (r) => {
        if (!r.confirm) return;
        // 这里先占位：后续你接入后端鉴权后，把删除请求做成标准 API。
        wx.showToast({ title: "已提交删除请求（待后端接入）", icon: "none" });
      },
    });
  },
});

