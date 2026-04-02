# FastAPI 接口契约（开发期骨架）

## 鉴权与限流

- 鉴权方式（开发期占位）：请求头 `X-OpenId`（可通过环境变量 `OPENID_HEADER` 配置）必须存在且非空。
- 管理接口：需请求头 `X-Admin-Secret`，与环境变量 `ADMIN_SECRET` 匹配。
- 限流（开发期内存实现）：对同一 `user_id + path` 每分钟最多 `RATE_LIMIT_PER_MINUTE` 次（默认 `30`），超出返回 `429`。

## 业务接口

### 1) 抽牌与解读

- `POST /v1/tarot/reading`
- 入参（JSON）：
  - `spreadId: string`
  - `themeId: string`
  - `positions?: string[]`
  - `clientNonce: string`
  - `lang?: "zh"`
- 出参：
  - `drawResult: { positionKey, cardId, upright, interpretation }[]`
  - `sessionId: string`
  - `contentVersion: string`

### 2) 写复盘/历史

- `POST /v1/tarot/history`
- 入参（JSON）：
  - `sessionId: string`
  - `reflectionText: string`
  - `tags?: string[]`
- 出参：
  - `{ ok: true }`

### 3) 拉取历史

- `GET /v1/tarot/history?cursor=0`
- 入参：
  - `cursor: int`（偏移量，从 0 开始）
- 出参：
  - `items: { sessionId, createdAt, themeId, spreadId, reflectionSummary }[]`
  - `nextCursor?: int | null`

### 4) 每日主题/牌阵建议

- `POST /v1/tarot/today`
- 入参（JSON）：
  - `date?: string`（YYYY-MM-DD）
  - `themePreference?: string`
- 出参：
  - `dateKey: string`
  - `themeId: string`
  - `spreadId: string`

### 5) 管理：内容版本查询

- `GET /v1/admin/content/version`
- 鉴权：需 `X-Admin-Secret`
- 出参：
  - `tarotCardsVersion: string`
  - `spreadsVersion: string`
  - `updatedAt: string`

