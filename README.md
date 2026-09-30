# workbuddy-chat-migration

> **English** · A [WorkBuddy](https://www.workbuddy.cn) skill that packs your current conversation into a cross-machine migration bundle — byte-level faithful, emoji/links/formatting intact — so you can continue chatting on another computer.

把当前 WorkBuddy 对话打包成「跨电脑迁移包」的 Skill。适用于在工作机 / 家用机等多台电脑之间手动同步对话，到另一台机器上接着聊，并把相关记忆一并带过去。

## 解决什么问题

WorkBuddy 的对话和本地记忆（`~/.workbuddy/MEMORY.md`）按机器隔离，换一台电脑就"失忆"了。这个 Skill 定义了一套固定的打包流程，把一次会话完整带走：

- **对话全文**——给人看的，要求**字节级保真**：emoji 不省略（影响语气）、markdown 链接保持 `[文字](url)` 可点击格式、代码块/加粗/列表全留。摘要不能替代原文。
- **记忆摘录**——给 AI 看的，从本机用户记忆中摘录与会话相关的条目，目标机器读取后并入自己的记忆。
- **附件**——会话中生成的图片 / SVG / HTML 独立导出，可直接打开。

## 核心特性

| 特性 | 说明 |
|---|---|
| 实时累积（默认） | 会话开始即创建 `实时对话流.md`，此后每轮原样追加，打包时直接拷贝，零手工重建 |
| 字节级保真 | emoji、超链接、markdown 标记、代码块原样保留，和原屏一致 |
| 直接抽取会话库 | 优先解析 WorkBuddy 本机原始会话记录（JSONL），拿到带时间戳的逐轮原文，保真度最高 |
| 一天多场不重名 | 同名自动查重加后缀（`迁移包_2026-09-30_模型选型`），避免两个包互相覆盖 |
| 事后重建（降级） | 从未激活实时累积时，从会话摘要重建逐字稿，并向用户明确声明"信息完整非字节级" |
| 固定输出结构 | 目录结构固定，目标机器操作步骤固定，跨机器零歧义 |
| 自带 skill 本体 | 迁移包内自动包含本 skill 目录，目标机没装也能用 |

## 安装

把 `skills/chat-migration-pack/` **整个目录**（含 `scripts/` 下的辅助脚本）拷贝到：

```
Windows: C:\Users\<你>\.workbuddy\skills\chat-migration-pack\
macOS / Linux: ~/.workbuddy/skills/chat-migration-pack/
```

重启 WorkBuddy 会话后生效。

## 使用

在对话中说出以下任意一种意图即可触发，无需追问细节：

- "打包对话" / "导出这次聊天"
- "迁移到另一台电脑 / 家里那台 / 公司电脑"
- "拷回家接着聊" / "拷到公司接着聊"
- "以后要迁移" / "回家接着聊"（**仅表达意图也会启动实时累积**，无需等到真要打包才说）

Skill 会在当前工作区生成（`[_主题]` 为可选后缀，见下节）：

```
迁移包_YYYY-MM-DD[_主题]/
├── 对话全文_YYYY-MM-DD[_主题].md  ← 本次会话逐轮 Q&A 原文（字节级保真）
├── <附件>.png / .svg / .html    ← 会话中生成的插图或页面
├── memory/
│   ├── MEMORY.md                ← 相关长期记忆摘录 + 给目标机器助手的指令
│   └── YYYY-MM-DD.md            ← 当日工作日志（如存在）
├── skills/
│   └── chat-migration-pack/     ← 本 skill 本体（目标机可能未装）
└── 迁移说明.md                  ← 包结构说明 + 目标机器操作指引
```

## 命名规则：一天多场对话必须加后缀

一天里可能有好几场主题完全不同的对话需要打包。如果都叫 `迁移包_<日期>`，轻则互相覆盖，重则过几天分不清谁是谁。

**根本原则：一个对话 = 一个包。**

```
迁移包_YYYY-MM-DD                ← 当天第一个包（无冲突时才用）
迁移包_YYYY-MM-DD_<主题>         ← 当天第 2、3… 个包
对话全文_YYYY-MM-DD_<主题>.md     ← 内层全文，后缀必须与包目录一致
```

- **查重范围是全机**，不只是当前工作区——同一天的多场对话通常落在不同工作区目录下，只看本工作区必漏。
- **后缀优先用主题词**（2–4 字，一眼看出聊了什么，如 `_模型选型`、`_Adobe互斥`）；话题没定型时先用 `_2`、`_3` 占位，打包时再换主题词。不要用 `_p1` / `_p2` 这类事后看不懂的编号。
- 同名主题再加时会自动顺延为 `_模型选型_2`，不会撞车。

自带查重脚本，一行拿到可用包名：

```bash
# 自动判定当天有无冲突，直接给出可用名（含顺延）
python skills/chat-migration-pack/scripts/pick_package_dir.py

# 已知主题时直接指定
python skills/chat-migration-pack/scripts/pick_package_dir.py 2026-09-30 模型选型

# 只看当天已占用哪些包
python skills/chat-migration-pack/scripts/pick_package_dir.py --list
```

## 附带脚本

| 脚本 | 用途 |
|---|---|
| `scripts/pick_package_dir.py` | 全机查重 + 自动取名。支持 `--list`（列出当天已占用包）/ `--plain`（只输出一行包名，给 shell 用） |
| `scripts/extract_session.py` | 解析 WorkBuddy 本机会话库（`~/.workbuddy/projects/<slug>/<uuid>.jsonl`），抽取字节级逐轮原文，剥离系统注入块只留用户原话 |

两个脚本均为纯标准库实现，无需额外依赖。

## 在另一台电脑上恢复

1. 用 U 盘 / 网盘 / 文件传输把整个 `迁移包_日期[_主题]/` 文件夹拷到目标机器
2. 打开 WorkBuddy 新对话，发送 `memory/MEMORY.md`，说"读取这个文件并记住"
3. 发送 `对话全文_日期[_主题].md`，说"接着聊"（或开新话题）

> 注意整体拷贝文件夹，别只挑几个文件拷——`附件/` 和 `skills/` 目录会丢。

## 适用范围

为 WorkBuddy 编写。其打包约定（原文 + 记忆 + 附件 + 说明）是平台无关的，其他有类似 Skill 机制的 agent 工具稍作路径调整也能复用。

## License

[MIT](./LICENSE)
