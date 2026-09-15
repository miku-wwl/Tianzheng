# Day 5 — 找到天正自动化入口

## 今日目标

今天只有一个任务：

> 找到一个稳定的方法，让代码创建真正的天正对象。

不是画“像墙的线”。

而是创建：

> 真正可以被天正识别和继续编辑的墙。

这是整个 7 天路线的最高风险点。

---

## 1. 尝试路径优先级

建议按以下顺序测试：

```text
1. 天正命令行
2. AutoLISP
3. COM / ActiveX
4. AutoCAD .NET API
5. 天正公开接口 / SDK
6. UI Automation
7. 逆向 / Hook
```

越往后成本越高。

---

## 2. 为什么优先命令行

如果天正某功能可以：

```text
输入命令
↓
参数
↓
创建对象
```

那么代码就可以调用：

```lisp
(command "某天正命令" ...)
```

这是最简单的 Bridge。

---

## 3. UI 自动化为什么只做最后 fallback

不建议优先：

```text
找按钮
↓
点击
↓
输入参数
↓
点坐标
```

因为它容易受到：

- 分辨率
- 弹窗
- 焦点
- 菜单位置
- 版本
- 语言
- 加载速度

影响。

Agent 项目应该尽量走 API / Command。

---

## 4. 今天的最小 Spike

只研究一个函数：

```text
create_wall(
    start,
    end,
    thickness
)
```

输入：

```text
start = (0,0)
end = (6000,0)
thickness = 200
```

输出必须满足：

```text
AutoCAD 中出现对象
+
天正能识别
+
能修改墙厚
+
程序能再次找到它
```

---

## 5. 验证方法

创建完成后：

### 手工验证

- 用天正选择
- 查看属性
- 修改厚度
- 修改长度

### 程序验证

查询：

```text
object id
class
layer
bounding box
custom properties
```

---

## 6. 保存 / 重开验证

非常关键：

```text
创建对象
↓
保存 DWG
↓
关闭 AutoCAD
↓
重新打开
↓
检查对象
```

因为某些自动化方式可能只在当前 session 看起来成功。

---

## 7. 错误记录

把失败当研究成果。

记录：

```text
ERROR
CAUSE
WORKAROUND
RESULT
```

例如：

```text
ERROR:
unknown command

CAUSE:
天正模块未加载

WORKAROUND:
先加载模块

RESULT:
PASS
```

---

## 8. 推荐接口设计

即使底层很乱，也先定义一个干净接口：

```text
create_wall(start, end, thickness)
```

不要让 Agent 直接知道：

```text
T20_XXXX
Command Sequence
Menu Macro
Internal Object Type
```

这些全部应该被 Bridge 隐藏。

---

## 9. 第二优先级对象

如果墙成功，再按顺序：

```text
create_door()
create_window()
```

门窗比墙更能验证“语义对象”是否真的打通，因为它们通常要绑定墙。

---

## 10. 今日产物

创建：

```text
automation_spike_report.md
```

内容：

```text
Environment

Test 1
Method
Command/API
Result
Error

Test 2
...

Final Decision
```

最后必须给出一个明确判断：

```text
A. 可直接自动化
B. 可自动化但有限制
C. 只能 UI 自动化
D. 当前版本无法稳定自动化
```

---

## 11. 完成标准

最好完成：

```text
create_wall() = PASS
```

如果失败，也没关系。

但必须知道：

> 为什么失败，以及下一条路线是什么。

明天开始真正写 Tianzheng Bridge。
