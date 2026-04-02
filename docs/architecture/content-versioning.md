# 牌义/牌阵内容版本体系（manifest + 灰度 + 回滚）

## 版本清单位置

- `backend/app/content/versions/manifest.json`

## manifest.json 字段

- `active`
  - `tarotCards`: 当前激活的“牌义库版本号”
  - `spreads`: 当前激活的“牌阵模板版本号”
- `gray`
  - `enabled`: 是否开启灰度选择
  - `tarotCards`: 灰度牌义候选，数组元素形如 `{ "version": "v1", "weight": 0.1 }`
  - `spreads`: 灰度牌阵候选，数组元素形如 `{ "version": "v1", "weight": 0.1 }`

> 回滚就是把 `active` 改回旧版本即可；无需改业务接口。

## 灰度选择逻辑（开发期实现）

- 输入：`user_id + date_key`
- 对 `tarotCards` 与 `spreads` 分别做稳定 hash
- 若灰度开启：
  - 命中灰度权重区间的用户会落到灰度候选版本
  - 未命中的用户继续使用 `active` 版本
- 若灰度关闭：所有用户都使用 `active`

## 追溯（写入 session）

- `/v1/tarot/reading` 会把最终选择到的版本组合写入返回字段 `contentVersion`
- 同时也会写入历史记录存储（用于后续回溯哪个版本生成的内容）

## 管理查询

- `GET /v1/admin/content/version`
- 返回当前 `active` 的 `tarotCardsVersion / spreadsVersion` 与 `updatedAt`

