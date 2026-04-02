# 微信云托管（云容器 / 自定义部署）部署流程

> 适用：将后端 `FastAPI` 服务部署到微信云托管（云容器），并让小程序通过 `wx.cloud.callContainer()` 调用。

## 0. 部署前前置检查（强烈建议先确认）

1. 服务端监听端口：后端需在容器内监听 `0.0.0.0:<PORT>`。当前骨架的 FastAPI 应用在 `backend/app/main.py` 中，建议容器运行命令使用 `uvicorn`。
2. 鉴权/鉴权头：当前后端鉴权使用请求头 `X-OpenId`（可由环境变量 `OPENID_HEADER` 覆盖），管理接口使用请求头 `X-Admin-Secret`（环境变量 `ADMIN_SECRET`）。
3. 文件存储风险：当前历史存储是 `backend/app/storage/history_store.py` 的文件 `data/tarot_history.jsonl` 方案。容器重启/扩缩容时文件系统可能不持久，生产环境建议尽快替换为 DB（或至少接入持久化存储/云数据库）。本节“测试策略”会包含验证点。

## 1. 容器镜像准备（Dockerfile 或云托管自动生成）

微信云托管支持“代码包内有 Dockerfile”或“无 Dockerfile 自动生成镜像”。由于本项目目前未包含 Dockerfile，建议你选择其一：

### 方案 A：新增 Dockerfile（推荐，利于可复现）

你可以在 `backend/` 目录添加类似以下内容（示意）：

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/ /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 方案 B：使用云托管“无 Dockerfile 自动生成”

按控制台要求提供 `backend/` 代码目录（需要 `requirements.txt`），并在“进程启动命令”填写 `python main.py` 或适配你目录结构的 `uvicorn` 命令。

> 关键：确保运行命令指向正确的 FastAPI app（当前为 `backend.app.main:app`）。

## 2. 新建服务版本（版本/监听端口/环境变量）

1. 创建服务（或进入已有服务详情）。
2. 进入 `版本列表` → `新建版本`。
3. 监听端口：填写与容器运行一致的端口（例如 8080）。
4. 选择环境变量（建议最小集合）：
   - `DEBUG=false`
   - `OPENID_HEADER=X-OpenId`（或你在小程序/云托管侧实际接入的 header 名称）
   - `RATE_LIMIT_PER_MINUTE`（按预期流量设置，默认 30）
   - `ADMIN_SECRET`（必填，否则管理接口会直接拒绝）
5. 日志采集：建议保证标准输出 `stdout/stderr` 可用（后续用于告警与排错）。

完成后，云托管会经历“镜像构建/部署”两阶段（创建过程一般最多约 2 分钟）。

## 3. 发布灰度（容器版本层灰度 + 业务内容层灰度）

### 3.1 容器代码层灰度（建议用于“新镜像/新代码”）

灰度方式（控制台通常提供“全量/灰度/流量比例”等形式）建议流程：

1. 新建版本完成后，不直接 100% 放量。
2. 设置新版本流量比例为低值（例如 5% 或 10%），并在 10-20 分钟观察：
   - 错误率（4xx/5xx）
   - `POST /v1/tarot/reading` 响应时延与超时率
   - `POST /v1/tarot/history` 的成功率
   - `POST /v1/tarot/today` 的成功率
3. 达标后再提升到 50% / 100%。

### 3.2 业务内容层灰度（manifest.json 的灰度）

即使容器层灰度已经放开，仍建议保持你的“牌义/牌阵内容版本”在后端 manifest 层可独立灰度：

- `backend/app/content/versions/manifest.json` 的 `gray.enabled + gray.tarotCards/spreads` 控制“同一版本库的内容小范围切换”
- 这部分与云托管容器灰度是两层灰度，建议策略：代码层灰度更短周期，内容层灰度可更细粒度。

## 4. 上线前测试策略（在灰度前做“可用性验证”）

建议你把测试分成三类：健康检查、鉴权与主链路、以及对文件存储/内容的校验。

### 4.1 健康检查

- `GET /health` 返回 `{"status":"ok"}`。
- `GET /` 返回提示信息（非 404）。

### 4.2 主链路联调（最少覆盖 3 个接口）

1. `POST /v1/tarot/reading`
   - 校验：`sessionId` 返回且 `drawResult` 数组长度等于牌阵位置数
   - 校验：返回的 `contentVersion` 格式正确（`cards_...|spreads_...`）
2. `POST /v1/tarot/history`
   - 校验：传入 `reflectionText` 后返回 `{ok:true}`
   - 校验：如果包含敏感/高风险措辞，应触发后端拦截（当前后端会 `ValueError`，你需要确认错误码/返回体是否符合预期）
3. `GET /v1/tarot/history?cursor=0`
   - 校验：能分页返回历史摘要字段（`sessionId/createdAt/themeId/spreadId/reflectionSummary`）

### 4.3 文件存储风险验证（很关键）

由于当前 `HistoryStore` 是写 `data/tarot_history.jsonl`：

1. 确认灰度期间写入历史后，在“新增/扩缩/重启”容器后历史是否依然可读
2. 如果不持久：说明必须在上线前替换为 DB 方案（对应你计划中的 `draw_sessions/reflections` 表设计）

## 5. 观测指标与性能阈值建议

在没有真实生产压测前，建议采用保守的阈值作为上线门槛（后续再调）：

- `POST /v1/tarot/reading`：P95 < 800ms（骨架实现主要是内存/文件读取）
- 错误率（非 2xx）：< 1%
- 超时率：< 0.1%
- 系统资源：CPU 持续高于 80% 或内存接近上限视为风险，需要提前扩容/降载

## 6. 回滚方案（容器版本层）

当你在灰度阶段发现错误率或时延显著异常时，按“流量回切”为主：

1. 将新版本流量比例降回 0%（或直接切回上一稳定版本 100%）
2. 等待一两个分钟确认指标恢复
3. 若确认新版本不可用：
   - 保留版本用于取证（日志/回放请求）
   - 或删除该版本（如果控制台允许且不影响在线版本）

> 内容层回滚（manifest 切换）与容器层回滚是两件事。容器回滚通常更直接影响接口可用性；内容层回滚更影响解释/抽牌结果的“文本与版本追溯”。

## 7. 建议的发布节奏（可执行）

1. 第一次：小流量 5%-10% 放量观察 10-20 分钟。
2. 第二次：提升到 50% 再观察 30-60 分钟。
3. 最后：提升到 100%，并保留上一稳定版本至少 1-2 天以便快速回滚。

