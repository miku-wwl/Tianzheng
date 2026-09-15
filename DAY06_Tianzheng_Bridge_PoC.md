# Day 6 — Tianzheng Bridge：最小可运行 PoC

## 今日目标

今天把前 5 天的研究变成一个真正的软件组件：

```text
TianzhengBridge
```

目标：

```text
普通代码
↓
统一 API
↓
AutoCAD + 天正
```

Agent 今天仍然不是重点。

---

## 1. 第一版 API

建议只实现：

```text
create_wall()
create_door()
create_window()
get_objects()
save_drawing()
```

不要扩 scope。

---

## 2. API 示例

### create_wall

```json
{
  "start": [0, 0],
  "end": [6000, 0],
  "thickness": 200,
  "unit": "mm"
}
```

返回：

```json
{
  "success": true,
  "object_id": "wall-001",
  "native_id": "...",
  "type": "wall"
}
```

---

## 3. create_door

建议参数：

```json
{
  "wall_id": "wall-001",
  "offset": 2500,
  "width": 900,
  "opening": "left"
}
```

---

## 4. create_window

建议：

```json
{
  "wall_id": "wall-002",
  "offset": 3000,
  "width": 1500,
  "sill_height": 900
}
```

---

## 5. Bridge 应负责什么

Bridge 必须负责：

- 单位转换
- 参数验证
- AutoCAD 连接
- 天正命令 / API 调用
- 错误转换
- 对象 ID 映射
- 保存
- 查询

LLM 不应该负责这些。

---

## 6. 参数验证

例如：

```text
thickness <= 0
→ reject

width <= 0
→ reject

door position > wall length
→ reject
```

这些应该用普通代码完成。

---

## 7. 最小户型 PoC

创建：

```text
6000 × 4000
```

四面墙：

```text
W1: (0,0) -> (6000,0)
W2: (6000,0) -> (6000,4000)
W3: (6000,4000) -> (0,4000)
W4: (0,4000) -> (0,0)
```

统一：

```text
thickness = 200
```

然后：

```text
1 door
2 windows
```

---

## 8. 查询闭环

执行：

```text
get_objects()
```

期望：

```json
{
  "walls": 4,
  "doors": 1,
  "windows": 2
}
```

并且每个对象有 ID。

---

## 9. 重新打开验证

完整测试：

```text
create
↓
save
↓
close
↓
open
↓
inspect
```

结果仍然应该：

```text
4 walls
1 door
2 windows
```

并保持可编辑。

---

## 10. 错误模型

统一错误格式：

```json
{
  "success": false,
  "error_code": "TZ_COMMAND_FAILED",
  "message": "...",
  "retryable": true
}
```

未来 Agent 才容易处理。

---

## 11. 日志

至少记录：

```text
timestamp
operation
arguments
native command
result
object id
error
```

后面 Debug Agent 会非常有用。

---

## 12. 今日产物

推荐结构：

```text
tianzheng-bridge/
  src/
  tests/
  examples/
  README.md
```

最少包含：

```text
create_wall
create_door
create_window
get_objects
save_drawing
```

---

## 13. 完成标准

今天最理想结果：

```text
4 Wall
+
1 Door
+
2 Window
+
Save
+
Reload
+
Inspect
=
PASS
```

如果这个闭环成立，核心技术风险已经大幅下降。

明天才真正接 Agent / MCP。
