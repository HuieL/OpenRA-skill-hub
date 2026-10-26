# OpenAR Skill Hub — Agent X 工作台（TODO 与里程碑）

本文件只在本仓库的 `todo` 分支维护，**永不合入 `main`**（`main` 是对外发布内容，必须干净）。
派工与验收由 OpenRA Review 负责；OpenRA 主仓库的 `TODO.md` 只记录 X 的一行状态与交接 SHA。

规格（以 OpenRA 主仓为准，勿复制）：`docs/skill-extension-hub-design.md`、`docs/skill-extension-hub-todo.md`（HUB-00…10）、`docs/hub-00-reuse-map.md`（C 的现状复用表）。

## 0. 角色与边界

- **X 负责本仓库的全部内容**：目录结构、条目（entries）、schema、生成的 `skills.json` 索引、校验脚本、CI、贡献说明、播种与发布。
- **不负责**：OpenRA 侧的 registry 客户端/安装/版本/回滚（C）、Hub UI（G+D）、Extension（Y 的 `OpenAR-extension-hub`）。
- **协作**：
  - X 定义 skill 条目 schema；**C 的 registry 客户端读取它**，schema 每次变更先在 OpenRA 主仓 TODO 的 M-HUB 行与 C 对齐，并在 PR 描述里写 `schemaVersion`。
  - 与 Y 共用同一份「条目公共核心字段」（id/kind/name/summary/source/version/license/review/compat）；字段名与语义两仓必须一致，改动需两边同 PR 描述互相引用。
  - 其他 agent（H/I/J/C 等）要上架自己的 skill：在本仓推 `agent-<x>/<topic>` 分支，X 先做内容审查，Review 最终合入 `main`。
- **分支与合入**：只推 `agent-x/<topic>` 分支；**不直接推 `main`**；Review（OpenRA 审查负责人）审查后合入。每个分支一个主题，小提交。
- **main 只放发布内容**：README、LICENSE、`skills.json`、`entries/`、`schemas/`、`scripts/`（校验/生成）、`.github/workflows/`。不放 TODO、回执、证据、验收记录、个人笔记（这些放 OpenRA 主仓 `docs/acceptance/`）。
- **安全**：不提交任何 token/凭据；CI 校验 job 无写权限、无 secrets，不执行 PR 中的脚本/安装命令；第三方内容逐条核许可，不整库复制上游。

## 1. 当前事实（2026-10-14）

- **main = 9 条，全部 `hub.*`**：diagram-design、hallmark、human-writing、officecli-academic-paper、officecli-data-dashboard、research-design-system、scientific-figure-making、web-design-guidelines、writing-guidelines（skills.json 钉 `2a5c93a`）。宿主客户端在该 commit 逐条解析、校验 entry sha256 与索引行一致：9/9 通过（Linux，10-14）。
- **内置 skill 不上 hub**（用户 10-12）；Craft Suite 为内置，已关闭其条目分支、历史不进 main。
- **HUB-11 社区数据已合**（`014a5f4`）：featured/collections/creators；discovery workflow 只读、产物为 artifact，不写 main。
- **officecli ×2 与宿主编译版锁步**（`cbbc1d1`），同版本同字节。
- **许可待裁决**：`hub.scientific-figure-making` 上游为 CC BY-NC 4.0，摘要/permissionsNote 已如实披露；在裁决前保持 `review.status: unreviewed`，不改其他条目、不冻结其他工作。
- **生命周期（宿主侧，公共行为）**：目录发现 → 人工批准 → 固定 revision 安装 → 会话按需加载 → 更新提示（只提示、显示差异，不自动安装或执行新版）→ 回滚。目录刷新只更新缓存，不等于启用新版。直接从 GitHub 来源选择性安装（vercel-labs/skills 源语法）与 hub 条目共用同一生命周期，标注 unreviewed / license unknown，且不进入本目录。
- **私人技能不公开**：宿主上从用户会话学到的私人 skill 不会自动出现在本仓；提交到本仓是单独的人工动作，走本仓的审查与发布门禁。

## 1b. 当前事实（2026-10-15 增补）

- main = `8bab217`：加入 `examples/standard-skill/`（HUB-09 标准样例 + 贡献步骤）；索引仍 9 条。
- `agent-x/pr-template@abe18ea`（待合）：PR 模板一页清单（钉 commit、完整清单、实际许可、作者可核对 vs registrySubmitter、requires/permissionsNote、重建索引、无私有内容、标记只改 `review.status` 并写理由）——SX-M3 PR 模板项。
- SX-02 现状：CONTRIBUTING 已含托管方式、更新与下架（`review.status` 原地改、不删历史）；**宿主侧提示**已写：OpenRA `agent-x/hub-skill-entry@879324d7` 的 `review_flag` 让 `ora changes hub-updates` 把原地标记 deprecated/high-risk 报成“registry 已标记、已装版本照常可用”，不再误报为“同版本内容被改”（触及 C 的 `hub_update.rs`，待 C 共审）。
- 宿主侧新增（OpenRA，待 Review）：`ora hub uninstall`（HUB-08，卸载与停用/单步回滚分开）、`GET /api/hub/skills/entry/{id}`（Y 详情页取 credit/categories，`designReference` 标设计资料选择器，U15-02 无需新增 kind 字段）。

- 10-15 晚：PR 模板已合 main `abe18ea`（SX-M3 一项闭）。`agent-x/trusted-validator@ccd69ed`（待合）：CI 用 **base 分支的** validate/build-index/build-community 以 `--root` 校验 PR 树，PR 代码不执行；改 scripts/schemas/.github 的 PR 被标注需人工审；首个 PR 自举一次。负例：PR 自带“永远通过”的 validate.py + 坏条目 → 可信校验 exit 1。Y 仓同样问题，owner patch 在 OpenRA `docs/acceptance/hub/x-extension-hub-trusted-validator-owner.patch`。
- OpenRA 侧全部 X 工作已合成一条 `agent-x/skill-hub-r3`（Review r3b ACCEPT，待 A+C 会签）。

## 1c. 当前事实（2026-10-19）

- main = `7b8d6c9`，**207 条**。下架（用户指示，删条目与 LICENSE、重生成全部索引）：`nature.reviewer`（疑似转载 Nature 网页，版权，`b84d5bb`）；`nature.downloader`（在用户已登录 Chrome 中自动破解 Turnstile/滑块验证码）与 `nature.image2ppt`（默认读取 ~/.codex/auth.json 并调用未公开接口），`agent-x/remove-high-risk@0760ca5` 已合。
- 可信校验已合（`66ee19c`，trusted-validator-r2）：PR 由 base 分支脚本 `--root` 校验，PR 代码不执行。旧分支 `agent-x/trusted-validator`、`agent-x/add-entry-check`（scratch，非 main）已过时，待 Review 删除。
- 宿主侧（OpenRA）：社区数据全新安装自动同步一次；Skill Hub 刷新拉最新目录；Home 有 skills.sh 排行榜（只读、6 h 缓存、上榜≠审核，安装走 install-from）；询问 agent 的会话绑定 skill、放隐藏内置项目（`agent-x/skill-hub-chat-home`，待合）；Hub 查询键入 workspace scope（`agent-x/hub-query-scope`，待合）。
- 仍待：PSL 验收走查（人工腿，脚本 `docs/acceptance/hub/x-psl-e2e.sh` 在 OpenRA）；`hub.scientific-figure-making`（CC BY-NC 4.0）许可裁决仍待用户。

## 1d. 当前事实（2026-10-26）

- main = `eea5e0a`，**226 条**（origin 已核实，无 anatomy 重名）。`hub.anatomy` 已上架（用户指派）：`agent-x/anatomy@5dbbdb6` 待 Review —— wheresryan22/anatomy 钉 `1482e846`，MIT，许可 148 文件共 2,137,030 字节；`examples/*.html`、`examples/*.pdf`（生成演示产物 ~37 MiB）按 CONTRIBUTING 演示产物规则 `--exclude` 排除并在 permissionsNote 声明（可由各示例 build.mjs 重建）；审查：kit/scripts 全读 —— 无 allowed-tools，检查脚本走本机 Chrome devtools（127.0.0.1），唯一网络路径为 publish.mjs `--submit` 显式推 wheresryan22/anatomy-community。索引/发现已重建，validate 过。
- `agent-x/gzh-design@f8fc971`（isjiamu/gzh-design-skill，AGPL）仍待 Review。
- 宿主打磨轮在 OpenRA `agent-x/skill-hub-wrap`（动效表三修、checklist.design 六清单走查、搜索命中高亮），回执在 OpenRA `docs/acceptance/skill-hub/`。

## 2. 里程碑

| 里程碑 | 内容 | 通过条件 |
| --- | --- | --- |
| **SX-M0 骨架** | 目录、schema、索引生成与校验、CI、README/LICENSE、贡献说明 | Review 合入后成为 `main`；`scripts/validate` 本地与 CI 都过；空索引合法 |
| **SX-M1 首批条目（HUB-M1 的 skill 半）** | 播种：`diagram-design`、`human-writing`、`officecli-academic-paper`、`officecli-data-dashboard`、`ora-craft-suite`；核心 ora-* 以 `delivery: bundled` 只读登记 | C 的客户端在固定 SHA 读到索引、sha256 全部吻合；OpenRA 能从本仓安装 `diagram-design` 并在会话中按需使用、升级、回滚（由 C/A 验收） |
| **SX-M2 可贡献** | 社区/私有来源说明、条目弃用/高风险标记、版本更新流程、更新检查所需的元数据 | 一个外部贡献样例从 PR 到合入走通；CI 不执行 PR 代码 |

## 3. 任务

### SX-00 骨架（✅ 已合入 main，10-12）
- [ ] 目录：
  ```
  README.md
  LICENSE                      # 仓库元数据与脚本：MIT；条目内容各按其上游许可
  skills.json                  # 由 scripts 从 entries 生成，禁止手改
  entries/skills/<id>/entry.json
  entries/skills/<id>/skill/   # 仅当 skill 正文由本仓托管时（维护者自有的小 skill）
  schemas/skill-entry.schema.json
  scripts/build-index.(py|mjs) scripts/validate.(py|mjs)
  .github/workflows/validate.yml
  CONTRIBUTING.md
  ```
- [ ] `entry.json` 字段（与 Y 共用核心 + skill 专属）：
  - 核心：`schemaVersion`(=1)、`id`（命名空间，如 `openra.diagram-design`；与显示名分离、全局唯一、不复用）、`kind`(="skill")、`name`（**一个简短英文名，所有语言相同**）、`summary`（可含 5 语言 `i18n`：en/zh-CN/ja/ko/es，只本地化描述）、`source`{`repo`,`path`,`revision`(40 位 commit SHA，禁止 main/latest/可变 tag)}、`version`（上游自报，没有则用 revision）、`license`(SPDX)+`licenseFile`、`review`{`status`: unreviewed|reviewed|deprecated|high-risk, `reviewedRevision`, `reviewer`}、`compat`{`minHost`,`harnesses`}
  - skill 专属：`delivery`: `bundled`（随 App，不可单独安装，只展示）| `hub`（可安装）；`files[]`{`path`,`sha256`,`bytes`,`executable`}（完整必要文件清单与哈希，含 scripts/references/assets；没有的目录不列）；`totalBytes`；`requires`（依赖的 extension/CLI/MCP 的 id，仅声明，不自动安装）；`permissionsNote`（SKILL.md 里 allowed-tools 等只是声明，不是本机批准）
- [ ] `skills.json`：按 id 排序的轻量投影（id/name/summary/delivery/version/revision/entryPath/entrySha256），由 build-index 生成；validate 检查与 entries 一致、无重复 id、无未知字段、sha256 对得上、路径无 `..`/绝对路径/符号链接、单条目大小上限（建议 ≤2 MiB）。
- [ ] CI：`pull_request` 只读校验（`permissions: contents: read`，无 secrets，不运行条目内脚本，不安装依赖之外的任何东西）；固定 action 版本到 SHA。
- [ ] README：Hub 是什么、如何被 OpenRA 读取（固定 revision + sha256）、`delivery` 含义、如何贡献、许可说明。
- 交付：分支 `agent-x/skeleton` → Review 合入成为 `main`。

### SX-01 首批条目（✅ 基本完成，10-13）
- [x] `diagram-design`：上游 `cathrynlavery/diagram-design@7a2e2217`，MIT；`files[]` 与 OpenRA 发布版内置副本逐文件 sha256 一致。
- [x] `human-writing`（MIT，上游 SHA 见 OpenRA curated 数据）、`officecli-academic-paper` / `officecli-data-dashboard`（核对上游许可；安装段落是 OpenRA 的"固定发布版安装"改写形式，条目需说明是改写版并给出原文来源）。
- [x] `ora-craft-suite`：从 H 的交接 接收（H 提供内容，X 建条目）；displayName 已统一为 "Craft Suite"。
- [x] ~~17 个 ora-* 核心~~：用户 10-12 裁定不上 hub，已撤销（revert `463c1fa`）。`delivery: bundled`，只登记 id/name/summary/当前 OpenRA 发布 revision，不提供安装文件（随 App 更新）。
- [x] 每条：许可文件、上游 revision、全部文件哈希；没有确认存在的 URL/版本不得上架。
- 交付：每 1–3 个条目一个分支 `agent-x/seed-<name>`。

### SX-02 可贡献与生命周期（LATER）
- [ ] CONTRIBUTING：开发者在自己仓库托管 skill，向本仓提交条目 PR；本仓只托管维护者自有的小 skill。
- [ ] 弃用/高风险/下架：保留条目与历史 revision，`review.status` 变更说明原因；OpenRA 侧据此提示（C）。
- [ ] 版本更新：新 revision = 新 `source.revision` + 新哈希；旧 revision 保留可回滚。
- [ ] 私有/本地来源说明：本仓不收私有内容，OpenRA 支持用户自加来源（C 实现）。

## 4. 验收与回报
- 每个分支：`scripts/validate` 输出、条目数、是否改 schema（改了需写 schemaVersion 与对 C/Y 的影响）。
- 回报写在 OpenRA 主仓 TODO 的 X 行（只写分支@SHA + 一句结论），不要在本仓 main 写回执。
- 规模：每分支新增手写文件 ≤5、修改 ≤10（条目数据文件除外，但每分支 ≤3 个新条目）。

## 5. OpenRA 主仓上的底座工作（用户 10-12：X/Y 在 OpenRA 分支写入底座以无缝集成）

- 在 OpenRA 只推 `agent-x/<topic>` 分支；Review 审查，Rust 改动进 Mac 门禁 train 后合入。派工以 OpenRA `TODO.md` 的 X 行为准。
- **HUB-01 registry 客户端（X 负责，两个 hub 共用一份实现）**：
  - [ ] 按 commit SHA 读取 `skills.json` 与 Y 仓的 `extensions.json`；逐条校验 entry sha256；拒绝 main/latest/可变 tag 当锁定。
  - [ ] 缓存 last-good 索引与刷新时间，断网不影响已安装能力；条件请求/ETag、限流退避、大小与条目数上限。
  - [ ] 只读：不安装、不执行；安装走 C 的安装内核 + ChangeSet（改 OpenRA 安装内核需 C 共审）。
  - [ ] fixture 测试（空索引、坏哈希、未知字段、路径穿越、超限）+ 对两真仓的只读探测。
- **HUB-04 skill 加载/编辑**：标准 SKILL.md 及必要 scripts/references/assets；按 revision 管理第三方 skill；只暴露当前 scope 已选 skill 的 metadata，正文按需读取；本地修改产生新本地 revision，升级前展示差异。
- 不碰：Hub UI（G+D）、ExtensionDefinition 契约（G）、扩展安装（Y）。

## 6. HUB-11 Community, Credits & Discovery（后续里程碑 SX-M3/M4；规格 OpenRA `docs/hub-community-discovery.md`）

**SX-00 起就预留署名字段**（避免以后迁移）：entry.json 公共核心加 `authors[]`{name,github}、`maintainers[]`、`contributors[]`、`adapters[]`（OpenRA 适配者）、`registrySubmitter`、`categories[]`；Y 仓同名同义。
- **SX-M3（HUB-M1 通过后，HUB-11 M2 部分）**
  - [ ] 署名校验（CI）：Original Author 必须能在 `source` 仓库的提交/许可/README 中核对；提交者默认只记 `registrySubmitter`，不可自填为 author；纠错走 PR + 原作者或维护者确认。
  - [ ] `community/creators.json`（作者公开资料：名称、GitHub、代表作品 `kind:id`，只放公开信息）、`community/featured.json`（条目、理由、日期、精选者）、`community/collections.json`（标题、说明、策展者、`kind:id` 列表、推荐理由）——两仓的社区数据**只在本仓**，用 `kind:id` 引用 Y 仓条目。
  - [ ] PR 模板与 CONTRIBUTING：新增条目、修正署名、提交合集。
- **SX-M4（HUB-11 M3 部分）**
  - [ ] GitHub Actions 定时生成 `community/discovery.json`：New（首次收录日期）、Recently Updated（可核查 release/commit）、Trending（公开 GitHub 信号，写明指标与窗口，标注 "Trending on GitHub"，不冒充安装量）；给新/小众项目保留曝光位；失败保留上一版；只读公开元数据，固定 action SHA，无写权限外泄。
- 不做：社区服务器、账号、评论库、点赞积分、等级、付费位；不收集私人使用历史/安装记录。


## 7. Public Release Gate（用户 10-12，硬规则）

- 本仓库**只放 OpenRA Public Contract 之上的可下载/适配资产**（条目元数据、schema、第三方或社区 skill/扩展的公开内容与发行包索引、校验脚本、CI）。**不得包含 OpenRA 核心逻辑**：不复制 OpenRA 源码、内部模块路径、内部 HTTP 路由、宿主 token 名、未公开的数据结构。
- 条目与 schema 只能引用 OpenRA `docs/public-contract.md` 中列出的稳定字段与接口（由 G+A 维护，尽量小）；需要新接口时向 OpenRA 提最小公共契约变更，不在本仓自定义宿主行为。
- 每个合入 main 的分支都要过 Review 的 Public Release Gate：路径白名单、与 OpenRA 源文件逐字节比对、内部标识/密钥扫描、无符号链接/大文件、CI 只读且 action 固定 SHA、无 `pull_request_target`。不通过不合入。
- 本 `todo` 分支同样公开可见：不要写 OpenRA 内部文件路径或实现细节，只引用公共文档名。
