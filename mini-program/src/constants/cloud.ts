// 云托管容器调用配置（请在部署后替换为你的真实值）

export const CLOUD = {
  /**
   * 本地试玩：务必 true，否则会走 wx.cloud.callContainer（需开通云+部署容器）。
   * 上线联调云托管时改为 false，并把 resourceEnv 换成「云开发环境 ID」。
   */
  useLocalMock: true,

  resourceEnv: "YOUR_WX_CLOUD_ENV_ID",

  serviceName: "tarot-fastapi",
} as const;

