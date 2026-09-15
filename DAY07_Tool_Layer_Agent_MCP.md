# Day 7 — Tool Layer、MCP 与 CAD Agent

## 今日目标

今天才把前 6 天的能力交给模型。

最终结构：

```text
User
↓
LLM / Codex
↓
Tools / MCP
↓
Tianzheng Bridge
↓
AutoCAD + 天正
↓
Observation
↓
LLM
```

---

## 1. Agent 不需要额外训练模型

第一版：

```text
1 个现成 LLM
+
Tools
+
Bridge
+
Validator
```

就够了。

不要一开始做：

```text
Planner Model
Vision Model
CAD Model
Validator Model
```

复杂度会爆炸。

---

## 2. Tool 设计

建议第一版：

```text
cad_create_wall
cad_create_door
cad_create_window
cad_get_objects
cad_get_object
cad_move_object
cad_delete_object
cad_save
```

---

## 3. Tool Schema 原则

必须：

- 参数明确
- 单位明确
- 返回结构化
- 错误结构化
- 不暴露底层脆弱细节

例如：

```json
{
  "name": "cad_create_wall",
  "arguments": {
    "start": [0, 0],
    "end": [6000, 0],
    "thickness": 200,
    "unit": "mm"
  }
}
```

---

## 4. 为什么推荐 MCP

MCP 的价值：

```text
模型
↓
标准化 Tool Interface
↓
你的 Tianzheng Server
```

以后可以复用给：

- Codex
- Claude
- GPT
- 其他 Agent

而不是绑定单一模型。

---

## 5. 第一个 Agent Prompt

用户：

```text
画一个 6m × 4m 的办公室。
墙厚 200mm。
南墙中间一个 900mm 门。
北墙两个 1200mm 窗。
```

Agent 应该：

```text
解析需求
↓
计算几何
↓
调用 create_wall × 4
↓
create_door × 1
↓
create_window × 2
↓
inspect
↓
save
```

---

## 6. 不要让 LLM 负责所有计算

推荐：

```text
LLM:
理解“矩形办公室”

普通代码:
计算四面墙坐标
```

这样稳定性更高。

例如：

```text
create_rectangular_room(
  width,
  depth,
  wall_thickness
)
```

内部 deterministic。

---

## 7. Observation

必须实现：

```text
cad_get_objects
```

Agent 需要知道：

```text
实际创建了什么
```

否则无法形成闭环。

---

## 8. Validator

第一版 Validator 不需要 AI。

直接检查：

```text
wall_count == 4
door_count == 1
window_count == 2
```

再检查：

```text
wall lengths
door width
window width
bounds
```

---

## 9. Agent Loop

最终：

```text
PLAN
↓
ACT
↓
OBSERVE
↓
VALIDATE
↓
CORRECT
```

例如：

```text
Agent:
创建窗

Observation:
offset 越界

Validator:
FAIL

Agent:
重新计算 offset

Tool:
create_window

Validator:
PASS
```

---

## 10. 今天的 Demo

输入：

```text
帮我画一个 6 × 4m 办公室，
墙厚 200mm，
南侧一个 900mm 门，
北侧两个 1200mm 窗。
```

输出：

```text
DWG
```

验证：

```text
4 walls
1 door
2 windows
correct dimensions
saved successfully
```

---

## 11. 下一步可以扩展什么

只有最小闭环稳定后再加：

```text
Room
Grid
Dimension
Column
Stair
Annotation
Layer management
```

之后再考虑：

```text
PDF → CAD
Image → CAD
Hand sketch → CAD
```

视觉模型属于第二阶段。

---

## 12. 不要马上做的事情

先别做：

```text
完整建筑施工图生成
建筑规范自动审核
结构计算
多 Agent
复杂 BIM
Revit 集成
```

先把：

```text
Natural Language
→
Real Tianzheng Objects
```

跑稳定。

---

## 13. 最终成功标准

7 天结束时，如果你能完成：

```text
自然语言
↓
Agent
↓
Tool Call
↓
Tianzheng Bridge
↓
4 墙 + 1 门 + 2 窗
↓
读取验证
↓
保存 DWG
```

那么这个项目最核心的技术假设已经验证成功。

---

# 7 天路线总结

```text
Day 1
建筑 CAD 背景

Day 2
AutoCAD 对象模型

Day 3
AutoCAD 自动化

Day 4
天正对象模型

Day 5
寻找天正自动化入口

Day 6
Tianzheng Bridge

Day 7
Tool Layer + MCP + Agent
```

真正的核心不是模型。

核心是：

> 稳定地把 `create_wall()` 变成一个真正可编辑、可读取、可保存的天正墙对象。
