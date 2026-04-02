export const ROUTES = {
  index: "/src/pages/index/index",
  spreadPicker: "/src/pages/spread-picker/spread-picker",
  reading: "/src/pages/reading/reading",
  history: "/src/pages/history/history",
  settings: "/src/pages/settings/settings",
} as const;

export function navigateTo(route: string, query?: Record<string, any>) {
  const q =
    query && Object.keys(query).length
      ? `?${Object.entries(query)
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
          .join("&")}`
      : "";

  wx.navigateTo({ url: `${route}${q}` });
}

