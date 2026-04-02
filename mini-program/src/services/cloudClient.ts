/* eslint-disable @typescript-eslint/no-explicit-any */

import { CLOUD } from "../constants/cloud";

let clientInitPromise: Promise<any> | null = null;
let cloudClient: any | null = null;

async function getCloudClient() {
  if (cloudClient) return cloudClient;
  if (!clientInitPromise) {
    clientInitPromise = (async () => {
      // 官方示例中建议使用 Cloud 实例并指定 resourceEnv。
      // 若你已在运行时通过其它方式初始化，也可在此处按你的项目调整。
      cloudClient = new wx.cloud.Cloud({
        resourceEnv: CLOUD.resourceEnv,
      });
      await cloudClient.init();
      return cloudClient;
    })();
  }
  return clientInitPromise;
}

export type CallMethod = "GET" | "POST";

export async function callContainer<TResponse>({
  path,
  method,
  data,
}: {
  path: string;
  method?: CallMethod;
  data?: Record<string, any>;
}): Promise<TResponse> {
  const c = await getCloudClient();

  const res = await c.callContainer({
    path, // 例如：/v1/tarot/reading
    method: method ?? "POST",
    header: {
      // 用于路由到你的云托管服务名
      "X-WX-SERVICE": CLOUD.serviceName,
    },
    data: data ?? {},
    dataType: "json",
    responseType: "json",
    // 根据官方要求：启动耗时 + 请求耗时 需满足 < timeout < 1500ms
    timeout: 1200,
  });

  return res.data as TResponse;
}

