# Day 2 — AutoCAD 基础与对象模型

## 今日目标

今天不是练“画图速度”。

目标是理解：

> AutoCAD 到底把一个 DWG 图纸表示成什么。

最终你应该可以：

- 手动画一个简单房间
- 理解常见 CAD Entity
- 知道 DWG 和 DXF 的区别
- 理解坐标、单位、Model Space、Layer、Block
- 开始从“软件工程对象模型”角度看 CAD

---

## 1. 必学对象类型

### LINE

最基础对象。

概念：

```text
start_point
end_point
layer
color
linetype
```

---

### POLYLINE

一串连接的线段。

适合：

- 墙体轮廓
- 边界
- 地块
- 连续轮廓

---

### ARC

常见用途：

- 门开启弧线
- 曲线构造

---

### CIRCLE

用途：

- 节点
- 标识
- 设备
- 轴号圆圈

---

### TEXT / MTEXT

TEXT：

- 单行文字

MTEXT：

- 多行文本
- 格式更丰富

---

### DIMENSION

尺寸标注不是简单的文字。

它通常包含：

- 被测几何关系
- 尺寸文本
- 尺寸线
- 引线
- 标注样式

---

### BLOCK / INSERT

Block 是定义。

INSERT 是 Block 的一个实例。

类比：

```text
Block Definition ≈ class
Block Insert ≈ object instance
```

---

## 2. Model Space 和 Paper Space

### Model Space

真实模型空间。

建筑通常按 1:1 画。

例如：

```text
6000 = 6000 mm
```

### Paper Space

用于排版出图。

包括：

- 图框
- 比例
- Viewport
- 标题栏

你现在主要关注 Model Space。

---

## 3. 坐标系

最简单先理解：

```text
X：水平
Y：垂直
Z：高度
```

二维平面中通常：

```text
(x, y)
```

例如：

```text
(0, 0)
(6000, 0)
(6000, 4000)
(0, 4000)
```

就是一个 6m × 4m 矩形。

---

## 4. 单位

AutoCAD 本质上只知道“drawing unit”。

建筑项目会约定：

```text
1 unit = 1 mm
```

所以：

```text
6000 = 6m
200 = 200mm
900 = 900mm
```

以后写 Agent Tool 时，单位必须非常明确。

建议 API 永远显式标明：

```json
{
  "unit": "mm"
}
```

---

## 5. DWG 和 DXF

### DWG

AutoCAD 原生二进制格式。

特点：

- 信息完整
- 复杂
- 专有格式

### DXF

Drawing Exchange Format。

特点：

- 更适合交换
- 更容易程序读写
- 结构更透明

但是：

> 能生成 DXF / DWG 不等于能生成天正专业对象。

---

## 6. 手动画一个最小户型

目标：

```text
6000 × 4000 房间
墙厚 200
一个 900 门
两个 1200 窗
一个房间名称
四周尺寸
```

建议过程：

1. 创建墙图层
2. 画矩形
3. Offset 200
4. 打开门洞
5. 画门扇 + Arc
6. 画两个窗
7. 添加 Room Text
8. 添加 Dimensions

---

## 7. 观察数据模型

画完后，逐个点击：

- 墙线
- 门线
- 门弧
- 窗
- 尺寸
- 文字

观察 Properties。

回答：

```text
这是一堵墙？
还是几根 LINE？

这是一个门？
还是 Line + Arc？

尺寸是 Text？
还是 DIMENSION Entity？
```

---

## 8. 软件工程类比

你可以这样理解：

```text
DWG
≈
一个对象数据库

Entity
≈
数据库中的对象

Layer
≈
分类 / namespace

Block
≈
可复用对象模板
```

这对后面写自动化非常重要。

---

## 9. 今日实操挑战

尝试画：

```text
办公室：
6000 × 4000

墙：
200 mm

门：
900 mm

窗：
1200 mm × 2
```

然后修改：

- 门移动 500 mm
- 窗宽从 1200 改成 1500
- 房间尺寸从 6000 改到 6500

观察修改过程有多麻烦。

这会帮助你理解为什么专业建筑对象有价值。

---

## 10. 今日产物

保存：

```text
day02_room.dwg
```

另外写：

```text
day02_entity_notes.md
```

记录至少：

- 使用了哪些 Entity
- 门由什么组成
- 墙由什么组成
- Dimension 是什么
- Block 和 Line 的区别

---

## 11. 完成标准

今天结束时你应该能说：

> AutoCAD 并不知道“建筑意义”上的墙和门，它首先操作的是 Entity。

明天开始让代码操作这些 Entity。
