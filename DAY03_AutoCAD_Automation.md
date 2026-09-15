# Day 3 — AutoCAD 自动化：AutoLISP 与 .NET API

## 今日目标

今天开始把 AutoCAD 从“人操作的软件”变成：

> 可以被程序调用的图形系统。

最终你应该做到：

```text
代码
↓
创建对象
↓
修改对象
↓
查询对象
↓
保存 DWG
```

---

## 1. 为什么先学 AutoLISP

AutoLISP 的优势：

- AutoCAD 原生支持
- 迭代快
- 非常适合做 PoC
- 很容易调用 AutoCAD 命令

缺点：

- 大型项目维护性一般
- 类型系统弱
- 对复杂工程架构不够舒服

所以建议：

```text
AutoLISP = 探索 / 快速实验
C# .NET = 正式 Bridge
```

---

## 2. AutoLISP 最小概念

你不需要系统学 Lisp。

只需要理解：

```lisp
(defun c:HELLO ()
  (princ "\nHello AutoCAD")
)
```

这是一个 AutoCAD 命令：

```text
HELLO
```

---

## 3. 尝试调用命令

概念示例：

```lisp
(command "_.LINE" '(0 0) '(6000 0) "")
```

再画：

```text
(0,0)
→
(6000,0)
```

然后自己创建一个简单矩形。

---

## 4. 查询对象

你需要开始理解：

```text
Entity Handle
Object ID
Selection Set
Properties
```

一个 Agent 如果只能“创建”，但不能“读取”，就无法闭环。

后面至少要做到：

```text
get_objects()
get_object_by_id()
get_layer()
get_type()
get_geometry()
```

---

## 5. C# / AutoCAD .NET API

正式工程更推荐：

```text
C#
+
AutoCAD .NET API
```

重点概念：

```text
Document
Database
Transaction
BlockTable
BlockTableRecord
Entity
ObjectId
```

你可以把它理解成：

```text
打开数据库
↓
开启事务
↓
拿到 Model Space
↓
创建 Entity
↓
写入数据库
↓
提交事务
```

---

## 6. 最小 .NET 思维模型

概念上：

```csharp
using (Transaction tr = db.TransactionManager.StartTransaction())
{
    // get model space

    // create entity

    // add entity

    // commit
}
```

不用今天就写完整插件。

先理解架构即可。

---

## 7. 第一个自动化 PoC

目标：

程序创建：

```text
4 条边
+
1 个 Text
+
1 个 Circle
```

然后保存。

建议坐标：

```text
(0, 0)
(6000, 0)
(6000, 4000)
(0, 4000)
```

---

## 8. 第二个 PoC：自动读取

程序输出：

```text
Object Count
Object Types
Layer Names
Bounding Box
```

例如：

```text
LINE x 4
TEXT x 1
CIRCLE x 1
```

---

## 9. 为什么“读取”非常重要

未来 Agent 流程：

```text
LLM:
创建房间
↓
Tool:
create_room()
↓
CAD
↓
Tool:
inspect_drawing()
↓
LLM:
检查是否正确
```

没有 inspect：

> Agent 只能盲画。

---

## 10. 建议的抽象层

从今天开始，不要在业务逻辑里直接写：

```text
command("LINE")
```

试着抽象：

```text
create_line(start, end)
create_text(position, text)
delete_object(id)
move_object(id, delta)
get_objects()
save_drawing()
```

未来这些就是 Tool Layer 的原型。

---

## 11. 今日产物

至少完成一个：

```text
autocad_poc.lsp
```

或者：

```text
AutoCadBridge.cs
```

实现：

- [ ] 创建线
- [ ] 创建文字
- [ ] 查询对象
- [ ] 保存

---

## 12. 完成标准

今天结束时：

```text
人不用手动画
↓
代码可以控制 AutoCAD
```

即可。

明天开始研究真正的关键：天正对象。
