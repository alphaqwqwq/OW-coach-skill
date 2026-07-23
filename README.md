# OW Coach

纯对话式守望先锋 AI 教练。没有数据 API、没有战绩查询、没有命令菜单。只有对话。

## 原理

传统 OW 教练工具靠数据面板（KDA、胜率、命中率）做量化分析——但好教练不是统计员。OW Coach
走纯对话路线：

- **你说战况，教练提问引导你发现问题**
- **教练根据你的描述做定性分析，不看面板**
- **跨对话记忆——新对话自动知道你的历史痛点和方案**

框架的核心不是爬数据，而是三组提示词（人格 + 方法论 + 知识约束）加一个跨对话玩家档案系统。

## 结构

```
ow-coach/
├── coach/
│   ├── agent.py       对话主循环（组装提示词 → 调 LLM → 存历史）
│   ├── memory.py      聊天记录 + 玩家档案持久化
│   ├── prompts/
│   │   ├── system.md      教练人格 + 核心原则
│   │   ├── framework.md   苏格拉底方法论 + 谦逊协议 + 跨对话记忆
│   │   └── knowledge.md   知识置信度三层定义
│   └── sessions/      (自动生成) 每个用户的对话记录 + 档案
├── README.md
└── .gitignore
```

**没有任何数据查询工具，没有 / 命令，没有评分系统。** 唯一的数据来源是玩家自己的描述。

## 使用方式

### 方式一：集成到你的应用

```python
from coach.agent import respond

# 你的 LLM 回调
def my_llm(system_prompt, history, user_input):
    # 调你的模型（OpenAI / 本地模型 / 飞书Bot……）
    return model.chat(system_prompt, history + [{"role": "user", "content": user_input}])

# 第一次对话
reply1 = respond("玩家ID", "我拉马刹总是打不过对面奥丽莎", my_llm)
# → 教练会提问诊断，输出诊断+方案到 [档案]

# 新对话（跨会话）——教练自动知道上次的问题
reply2 = respond("玩家ID", "我今天试了调整站位，确实好了一些", my_llm)
# → 教练能看到档案："历史诊断的痛点: [诊断] 拉马刹对线奥丽莎时站位问题"
# → 会问："上次聊的站位调整效果怎么样？"
```

### 方式二：CLI 调试

```bash
cd ow-coach
python -m coach.agent
```

CLI 支持三个命令：
- 直接输入文字 → 模拟对话，看拼好的提示词
- `prompt` → 只显示当前完整提示词（含玩家档案）
- `profile` → 查看当前玩家档案

### 方式三：Webhook / Bot

`respond()` 不依赖任何 I/O 框架，任意集成：

```python
# 飞书 Bot 回调
def on_message(user_id, text):
    return respond(user_id, text, my_llm)

# Discord Bot
@bot.event
async def on_message(msg):
    reply = respond(str(msg.author.id), msg.content, my_llm)
    await msg.channel.send(reply)
```

## 跨对话记忆

这是框架的核心特性。工作方式：

1. **教练在诊断出新问题时**，在响应末尾自动输出 `[档案]` 段（对玩家不可见）
2. **内存模块解析 `[档案]`**，提取诊断、方案、跟进状态、笔记，存到 `sessions/{用户ID}_profile.json`
3. **新对话开启时**，`build_prompt()` 自动从档案注入以下内容到提示词：
   - 历史诊断的痛点（带标签：已改善 / 未解决 / 诊断）
   - 过往给出的方案
   - 教练笔记

每次对话，教练都记得你是谁、之前有什么问题、给过什么方案。

## 需要你做的事

框架的正确性上限取决于你的知识注入。目前已有的：

- **你宗师水平的英雄池**：拉马刹、奥丽莎、骇灾、死神、探奇、雾子（等你写成知识文件）
- **LLM 兜底**：英雄技能、空间原理、战术逻辑（通过谦逊协议防止不懂装懂）
- **教练方法论**：已内置在提示词中

把你知道的写进知识文件之后，这个框架就是**有你的理解兜底的 LLM 教练**，不是网上语料乱炖。
