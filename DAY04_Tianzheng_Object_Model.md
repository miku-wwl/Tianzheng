# Day 4 — 天正建筑：对象模型与普通 AutoCAD 的区别

## 今日目标

今天不是学“所有天正功能”。

今天只研究：

> 天正到底给 AutoCAD 增加了什么。

重点对象：

```text
墙
门
窗
轴网
房间
尺寸
```

---

## 1. 为什么需要天正

普通 AutoCAD 可以画：

```text
LINE
POLYLINE
ARC
TEXT
```

但是建筑设计需要更高层的对象：

```text
Wall
Door
Window
Room
Grid
```

天正的价值，就是把“纯几何”提升到“建筑语义”。

---

## 2. 第一个对比实验：墙

### 实验 A

用普通 AutoCAD：

```text
画两条平行线
间距 200
```

这“看起来”像墙。

### 实验 B

用天正：

```text
绘制墙体
厚度 200
```

比较两者。

检查：

- Properties
- Grip
- 修改墙厚
- 墙连接
- 删除
- 移动

回答：

> 天正墙和普通两条 Line 的行为有何不同？

---

## 3. 第二个实验：门

普通 AutoCAD 画门：

```text
Line
+
Arc
```

天正创建门：

```text
Door Object
```

测试：

- 改门宽
- 改方向
- 移动位置
- 墙体洞口是否跟着变

如果是专业对象，门和墙之间应该存在语义关系。

---

## 4. 第三个实验：窗

测试：

- Width
- Height
- Sill Height
- Host Wall

观察修改窗宽时，墙洞口是否自动更新。

---

## 5. Proxy Object

这是后面 Agent 项目必须理解的概念。

某些自定义对象只有在对应软件存在时才能完整编辑。

如果缺少天正：

```text
DWG
↓
AutoCAD
↓
可能只看到 Proxy Object
```

可能出现：

- 能显示
- 不能完整编辑
- 属性缺失
- 显示异常

---

## 6. 核心研究问题

今天一定要开始回答：

### Q1

天正对象在 AutoCAD 数据库中是什么类型？

### Q2

它们有自己的 Class Name 吗？

### Q3

能否通过 AutoLISP 查询？

### Q4

能否通过 COM 查询？

### Q5

能否通过 .NET API 查询？

### Q6

天正命令能否通过 `(command ...)` 调用？

### Q7

对象创建后，是否可以读取属性？

---

## 7. 命令调用实验

目标：

不是点击 UI。

而是尝试：

```text
Command Line
↓
调用天正命令
```

如果某功能可以通过命令行调用，那么自动化难度会大幅下降。

---

## 8. 记录对象行为

建立表格：

| 对象 | 普通 AutoCAD | 天正 | 可命令调用 | 可程序读取 |
|---|---|---|---|---|
| 墙 | Line/Polyline | Wall | ? | ? |
| 门 | Line+Arc/Block | Door | ? | ? |
| 窗 | Line/Block | Window | ? | ? |
| 轴网 | Line+Text | Grid | ? | ? |
| 房间 | Polyline+Text | Room | ? | ? |

---

## 9. 版本兼容性

记录：

```text
AutoCAD Version
Tianzheng Version
DWG Version
```

因为以后出现：

```text
在 A 机器能打开
在 B 机器不能编辑
```

版本信息会非常关键。

---

## 10. 今日产物

创建：

```text
tianzheng_object_research.md
```

至少包含：

- 天正墙与普通线的区别
- 天正门与普通门图形的区别
- 3 个对象的属性截图 / 记录
- 可调用命令
- 发现的限制
- 版本信息

---

## 11. 完成标准

如果今天结束你能回答：

> “天正墙到底是不是普通 AutoCAD Entity，以及我能不能通过程序找到它。”

你就完成了真正关键的一步。

明天进入最重要的技术 Spike：找到自动化入口。
