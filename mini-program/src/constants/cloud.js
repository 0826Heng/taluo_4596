// 云托管容器调用配置（部署后替换为你的真实值）
export const CLOUD = {
  /**
   * 本地试玩：务必 true，否则会走 wx.cloud.callContainer（需开通云+部署容器）。
   * 上线联调云托管时改为 false，并把 resourceEnv 换成「云开发环境 ID」（不是小程序 AppID）。
   */
  useLocalMock: true,

  // 与 app.json / 云开发环境保持一致（示例占位；配合 useLocalMock: false 使用）
  resourceEnv: "YOUR_WX_CLOUD_ENV_ID",

  // 云托管服务名称（调用时通过 header: { 'X-WX-SERVICE': xxx } 指定）
  serviceName: "tarot-fastapi",
};

