# 数据库表与索引设计（塔罗牌业务）

> 目的：为未来从“文件存储（开发骨架）”迁移到 MySQL/PostgreSQL 提供一套稳定的数据模型与索引策略；同时支持内容版本追溯与回滚（灰度/回滚都可以通过版本选择实现）。

## 设计假设（与当前后端代码对齐）

- `user_id`：使用小程序侧请求头 `X-OpenId`（或环境变量 `OPENID_HEADER`）中的用户标识。
- `session_id`：由 `user_id + clientNonce` 组合生成（当前实现为 `f"{user_id}-{client_nonce}"`），用于幂等与历史追溯。
- `dateKey`：YYYY-MM-DD（当前实现为当天的 UTC 日期）。
- `contentVersion`：由 `tarotCardsVersion/spreadsVersion` 组合得到（当前实现为 `cards_{tarot_cards_version}|spreads_{spreads_version}`）。

## 表：`themes`（用户提问主题/分类）

用于前端展示与后端校验（目前接口只透传 `themeId`，但上线后建议做主题表以便审查与配置管理）。

```sql
create table themes (
  theme_id          varchar(64)  primary key,
  category          varchar(64)  not null,   -- 关系/事业/学习/自我成长等
  display_name     varchar(128) not null,
  sort_order       int           not null default 0,
  is_active         boolean       not null default true,
  created_at       timestamptz   not null default now(),
  updated_at       timestamptz   not null default now()
);

create index idx_themes_category on themes(category);
create index idx_themes_active on themes(is_active);
```

## 表：`tarot_cards`（牌义库，按版本存储）

> 关键点：牌义需要支持“按内容版本”追溯，因此建议把同一张牌的不同版本并存。

```sql
create table tarot_cards (
  tarot_cards_version  varchar(64) not null,     -- 例如 v1/v2
  card_id               varchar(64) not null,     -- 例如 "card_01" 或固定编号
  meaning_upright      text         not null,
  meaning_reversed     text         not null,
  tags                  jsonb        not null default '[]'::jsonb,
  created_at           timestamptz  not null default now(),
  updated_at           timestamptz  not null default now(),

  primary key (tarot_cards_version, card_id)
);

create index idx_tarot_cards_version on tarot_cards(tarot_cards_version);
```

可选：如果需要按标签检索，可对 `tags` 建 `GIN`（上线后按实际查询再决定）。

## 表：`spreads`（牌阵模板，按版本存储）

```sql
create table spreads (
  spreads_version  varchar(64) not null,
  spread_id        varchar(64) not null,         -- 例如 "spread_three_cards"
  positions        jsonb        not null,         -- ["positionKey1","positionKey2",...]
  position_count   int          not null,         -- 冗余加速（便于校验）
  created_at       timestamptz  not null default now(),
  updated_at       timestamptz  not null default now(),

  primary key (spreads_version, spread_id)
);

create index idx_spreads_version on spreads(spreads_version);
```

## 表：`content_versions` / `versioning`（内容版本元数据 + 回滚）

计划中“versioning”核心诉求是：可以记录每次上线/回滚用到的牌义版本与牌阵版本，并可回溯到用户 session。

建议拆成两层：

1) `content_versions`：组合内容版本（与当前后端 `contentVersion` 字段同构）
2) `content_manifests`：灰度/激活策略（对应当前 `manifest.json`）

### 1. `content_versions`

```sql
create table content_versions (
  content_version        varchar(128) primary key,  -- cards_{x}|spreads_{y}
  tarot_cards_version    varchar(64) not null,
  spreads_version         varchar(64) not null,

  release_notes          text,
  released_at            timestamptz not null default now(),
  created_at             timestamptz not null default now()
);

create index idx_content_versions_tarot on content_versions(tarot_cards_version);
create index idx_content_versions_spreads on content_versions(spreads_version);
```

### 2. `content_manifests`

`content_manifests` 表用于保存“当前 active / gray 配置”，便于回滚：只要切换 active 到旧的 manifest，业务选择逻辑不变。

```sql
create table content_manifests (
  manifest_id                 uuid primary key,
  manifest_key                varchar(64) not null unique,  -- 例如 "default"
  updated_at                  timestamptz not null default now(),

  gray_enabled                boolean not null default false,
  active_tarot_cards_version varchar(64) not null,
  active_spreads_version      varchar(64) not null,

  -- 对应 manifest.json.gray.tarotCards / gray.spreads
  gray_tarot_cards jsonb not null default '[]'::jsonb,   -- [{"version":"v1","weight":0.1},...]
  gray_spreads      jsonb not null default '[]'::jsonb,

  notes text
);

create index idx_content_manifests_updated_at on content_manifests(updated_at desc);
```

## 表：`draw_sessions`（抽牌会话 / 幂等 / 追溯）

```sql
create table draw_sessions (
  session_id            varchar(128) primary key,   -- user_id-client_nonce
  user_id               varchar(64)  not null,
  client_nonce         varchar(128) not null,

  theme_id              varchar(64)  not null,
  spread_id             varchar(64)  not null,
  date_key              date          not null,       -- YYYY-MM-DD

  tarot_cards_version  varchar(64)  not null,
  spreads_version      varchar(64)  not null,
  content_version      varchar(128) not null,       -- 同 content_versions.content_version

  seed                  char(64)     not null,       -- sha256 hex
  draw_result           jsonb        not null,       -- 位置 -> 牌与象征解读（快照）

  created_at            timestamptz  not null default now(),
  updated_at            timestamptz  not null default now(),

  unique (user_id, client_nonce)
);

create index idx_draw_sessions_user_created_at on draw_sessions(user_id, created_at desc);
create index idx_draw_sessions_date_key on draw_sessions(date_key);
create index idx_draw_sessions_theme_spread on draw_sessions(theme_id, spread_id);
```

说明：

- `draw_result` 建议保留“生成快照”，这样即使内容版本回滚，历史 session 的解释仍可复现/展示一致。
- `unique (user_id, client_nonce)` 或 `session_id` 足以支撑幂等写入（按你的客户端 nonce 语义）。

## 表：`reflections`（用户复盘/复盘摘要）

```sql
create table reflections (
  session_id           varchar(128) primary key,  -- 一次会话一条复盘（若要支持多次可改成 reflection_id + FK）
  user_id              varchar(64) not null,

  reflection_text      text not null,
  reflection_summary   varchar(256) not null default '',
  tags                  jsonb not null default '[]'::jsonb,

  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),

  foreign key (session_id) references draw_sessions(session_id) on delete cascade
);

create index idx_reflections_user_created_at on reflections(user_id, created_at desc);
```

可选：

- 如果后续要按 `tags` 查询复盘列表，可对 `tags` 建 `GIN` 索引；当前 API 只需要按 `user_id + created_at` 拉列表，GIN 可能是过度。

## 查询与索引落点（对应当前 API）

- `GET /v1/tarot/history?cursor=`：按 `user_id` + `created_at`（倒序）分页。建议使用 `idx_draw_sessions_user_created_at` 与（若复盘摘要需要拼接）对 `reflections.session_id` 的主键/外键访问。
- `POST /v1/tarot/reading` 返回 `sessionId/contentVersion`：所有写入落在 `draw_sessions`，其中 `content_version` 与版本元数据对齐，便于审查与回滚追溯。
- `POST /v1/tarot/history`：按 `session_id` upsert 到 `reflections`（主键冲突即可更新）。

## 迁移/落地建议（实践要点）

- 首次上线可以先只落地 `draw_sessions/reflections + content_manifests`，`tarot_cards/spreads` 可以先从对象存储/版本 JSON 读取。
- 当你希望真正“离线化内容库”和“完全复现生成结果”时，再把 `tarot_cards/spreads` 写入对应版本表。
- 版本回滚：通过切换 `content_manifests` 的 active/gray 配置实现，业务代码不需要改变。

