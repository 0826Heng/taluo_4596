# 审核自查清单（上线前）

> 用途：在提交微信小程序/云托管审核前，逐项对照并留存截图/记录。本文档覆盖页面内容、诱导行为、隐私与数据删除、日志告警与性能阈值。

## A. 页面内容与结果呈现（高风险措辞必检）

1. 页面标题/按钮/文案禁止出现高风险措辞（至少包括以下集合），避免触发“算命/抽签/星座运势/预测未来/封建迷信/宣扬邪教”等拒绝情形。
   - `算命`
   - `抽签`（含“抽签式/抽签结果”同类变体也要排除）
   - `星座运势` / `运势`
   - `预测未来`
   - `包你一定` / `必然发生` / `保证` / `必然`
   - `封建迷信` / `迷信`
   - `宣扬邪教` / `邪教`
2. 你当前小程序端“可视化文案”已使用 `塔罗象征解读 / 象征解读 / 翻阅牌面 / 复盘笔记 / 历史记录 / 隐私与数据管理` 等低风险措辞；需要在以下位置再次人工确认：
   - `mini-program/src/constants/copy.ts`
   - `mini-program/src/pages/index/index.wxml`
   - `mini-program/src/pages/spread-picker/spread-picker.wxml`
   - `mini-program/src/pages/reading/reading.wxml`（结果展示）
   - `mini-program/src/pages/settings/settings.wxml`（隐私与数据管理）
3. 结果页免责声明已放置且文案合规（必须出现在结果页/翻牌呈现附近）：
   - 检查 `mini-program/src/constants/copy.ts` 的 `result.disclaimer` 是否未被改动
   - 检查 `mini-program/src/components/DisclaimerBanner/index` 是否只展示该文案，不额外拼接高风险内容
4. 后端返回的解读文本也必须安全：
   - 当前后端会对 `drawResult[].interpretation` 和 `reflectionSummary` 做敏感词拦截（命中会直接报错）
   - 仍需在内容库发布前扫描 `backend/app/content/versions/tarot_cards_*.json`，确保不含高风险词

## B. 诱导行为与“承诺/恐吓/付费解锁”禁区

1. 禁止“付费解锁更准结果/更高权威/更多内容”的机制（当前项目未内置付费逻辑，保持这一点）。
2. 禁止恐吓或强操控式 CTA，例如：
   - “不做就会怎样”
   - “保证改变命运”
   - “你一定会……”
3. 禁止诱导分享/关注/点赞/评论作为奖励条件；同时避免“只要你转发就……”式引导。
4. 小程序端分享回调不存在（建议保留现状，并在代码变更后重新检查）：
   - 搜索 `onShareAppMessage / onShareTimeline / wx.share`：上线前应保持无结果或无诱导文案。
   - 当前快速扫描未发现分享与诱导相关实现（上线前仍建议复扫一次）。

## C. 隐私、数据删除与数据最小化

1. 隐私说明：
   - `mini-program/src/pages/settings/settings.wxml` 必须能清晰向用户说明：保存了哪些数据（历史/复盘），保存用途（查看与复盘），并支持删除。
   - 检查 `mini-program/src/constants/copy.ts` 中 `settings.privacyNote` 是否与实际后端存储一致。
2. 数据删除能力（上线前必须补齐后端）：
   - 当前 `mini-program/src/pages/settings/settings.ts` 的 `onClearData` 仅做前端占位：弹窗确认后只提示“待后端接入”
   - 正式上线前需要补齐一套后端删除接口（建议风格）：
     - `POST /v1/tarot/userdata/delete`（鉴权：必须关联 user_id）
     - 删除范围：该用户的 `draw_sessions` 与对应 `reflections`（按你的 DB 设计实现级联或显式删除）
     - 返回成功后：前端清空页面缓存并重新拉取历史
3. 数据最小化策略：
   - 日志中避免输出用户输入的 `reflectionText` 原文（建议只记录 sessionId、耗时、是否命中安全拦截、错误类型等）
4. 文件存储风险提示（当前骨架实现仍在开发期）：
   - `backend/app/storage/history_store.py` 使用本地 jsonl 文件保存历史
   - 若仍使用文件存储：删除与持久性均无法满足生产要求，需要在上线前切换到 DB（对应你计划中的 `draw_sessions/reflections` 表）

## D. 日志告警与性能阈值（上线门槛）

结合你在 `docs/architecture/deployment-cloudrun.md` 里建议的阈值，建议上线前确认下列“可观测性”具备：

1. 核心指标（建议至少在控制台/日志系统中可见）：
   - `GET /health` 可用性
   - `POST /v1/tarot/reading` 成功率、错误率、P95 延迟
   - `POST /v1/tarot/history` 成功率、错误率
   - 超时率/5xx 率
2. 建议性能门槛（骨架实现保守值）：
   - `POST /v1/tarot/reading`：P95 < 800ms
   - 错误率（非 2xx）：< 1%
   - 超时率：< 0.1%
3. 安全与合规相关日志：
   - 命中高风险内容拦截时：记录“命中类型/规则编号/拦截发生位置”，但不要把命中原文回显到日志。
4. 灰度阶段回滚触发（建议写入发布记录）：
   - 新版本错误率显著高于基线，或 P95 超出阈值时：按容器版本层回切到上一稳定版本。

## E. 版本与内容追溯（便于审核与回滚）

1. 每次生成结果应具备可追溯的 `contentVersion`（当前会返回并写入历史/会话）。
2. 上线/回滚操作需能定位是“代码版本层”还是“内容版本层”造成的差异：
   - 代码版本：云托管容器版本
   - 内容版本：后端 `content/versions/manifest.json` 的 active/gray 选择

