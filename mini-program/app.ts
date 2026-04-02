/// <reference path="./src/types/wechat-globals.d.ts" />
App({
  async onLaunch() {
    // 初始化云环境（请在 app.json 设置 YOUR_WX_CLOUD_ENV_ID）
    // 若已配置云环境，可直接调用 wx.cloud.init()。
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const wxAny: any = wx;
    wxAny.cloud?.init?.();
  },
});

