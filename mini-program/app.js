App({
  async onLaunch() {
    // 本地 mock/预览：未配置云环境也不会阻塞（wx.cloud 可能不存在）
    if (wx && wx.cloud && typeof wx.cloud.init === "function") {
      wx.cloud.init();
    }
  },
});

