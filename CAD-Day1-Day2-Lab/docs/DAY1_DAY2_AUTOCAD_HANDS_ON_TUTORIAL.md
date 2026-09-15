# Day 1 + Day 2 — AutoCAD hands-on learning lab

> 本文只记录本次实验中实际生成和验证的结果。AutoCAD 2027 已安装并运行；文件转换、重新打开、ModelSpace 实体检查，以及 Properties 面板中的对象类型确认均已完成。所有自动化选择均明确记录为 AutoCAD 内部预选，而不是物理鼠标点击。

## 实验状态

本次实验已经完成：

- 在桌面创建 `CAD-Day1-Day2-Lab/`，包含 `src/`、`output/`、`screenshots/`、`docs/`、`notes/`。
- 用 Python 3.13 和 `ezdxf 1.4.4` 生成两个可读取的 DXF 文件。
- 用 `ezdxf` 重新读取两个文件，输出实体清单，并验证了 LINE 与闭合 LWPOLYLINE 的差异。
- 生成了三个基于 DXF 数据的预览图。它们是实验预览，不是 AutoCAD 截图：
  - [Experiment A 预览：四条 LINE](../screenshots/01_ezdxf_line_preview.png)
  - [Experiment B 预览：一条闭合 LWPOLYLINE](../screenshots/02_ezdxf_polyline_preview.png)
  - [LINE vs POLYLINE 对比图](../screenshots/03_line_vs_polyline_comparison.png)
- AutoCAD 2027 实例已被发现并运行，版本为 `26.0s (LMS Tech)`，程序路径为 `D:\360\autocad\AutoCAD 2027\acad.exe`，可用 COM ProgID 为 `AutoCAD.Application.26`。
- 两个 DXF 已由 AutoCAD 打开，并通过 AutoCAD ModelSpace / Layer 集合检查实体类型和图层：
  - Experiment A：`A-WALL` 为 4 个 `AcDbLine`。
  - Experiment B：`A-WALL` 为 1 个 `AcDbPolyline`，即闭合多段线。
- 两个文件均已通过 AutoCAD `SaveAs` 生成 DWG，并由 AutoCAD 重新打开：
  - [day2_line_based.dwg](../output/day2_line_based.dwg)
  - [day2_polyline_based.dwg](../output/day2_polyline_based.dwg)
- [AutoCAD 资源与执行报告](../notes/autocad_resource_inventory.txt) 及 [JSON 报告](../notes/autocad_resource_inventory.json) 已保存。
- [AutoCAD Experiment A 窗口截图](../screenshots/04_autocad_line_overview.png) 与 [Experiment B 窗口截图](../screenshots/05_autocad_polyline_overview.png) 已保存；它们是实际 AutoCAD 窗口总览，不是 Properties 或 Layers 面板截图。
- 已通过 AutoCAD 命令接口打开 Properties、Layer Properties Manager，并切换到 `Layout1` 的 Paper Space；对应截图为 [Properties A](../screenshots/06_autocad_properties_line.png)、[Properties B](../screenshots/06_autocad_properties_polyline.png)、[Layers A](../screenshots/07_autocad_layers_line.png)、[Layers B](../screenshots/07_autocad_layers_polyline.png) 和 [Paper Space A](../screenshots/08_autocad_paper_space_line.png)。
- COM 等价属性检查确认墙实体为 `Color = 256`、`Linetype = ByLayer`；图层集合确认 `A-WALL` 等图层均为打开状态，且未锁定、未冻结。
- Paper Space 命令检查确认 `TILEMODE = 0`、当前布局为 `Layout1`、`PaperSpace` 中有 1 个布局对象；检查完成后已切回 Model Space（`TILEMODE = 1`）。
- [AutoCAD UI 等价验证报告](../notes/autocad_ui_equivalent_check.txt) 及 [JSON 报告](../notes/autocad_ui_equivalent_check.json) 已保存。
- 已通过 AutoCAD 内部预选集选中实体后，在 Properties 面板确认真实类型：
  - [Line / A-WALL](../screenshots/10_properties_selected_line_focused.png)
  - [Arc / A-DOOR](../screenshots/10_properties_selected_arc_focused.png)
  - [Text / A-TEXT，内容 OFFICE](../screenshots/10_properties_selected_text_focused.png)
  - [Rotated Dimension / A-DIMS](../screenshots/10_properties_selected_dimension_focused.png)
  - [Polyline / A-WALL，Closed = Yes](../screenshots/10_properties_selected_polyline_focused.png)
- 每个 Properties 检查的 AutoCAD 预选集记录已保存，例如 [LINE](../notes/autocad_properties_line_focused.txt) 与 [Polyline](../notes/autocad_properties_polyline_focused.txt)。
- [实体清单](../notes/entity_inventory.txt) 已保存。

仍标记为 `NOT VERIFIED` 的只是原生鼠标输入本身：

- 没有将物理鼠标坐标或可访问性元素注入 AutoCAD。
- Layers、ByLayer 与 Paper Space 的功能状态已由 AutoCAD 命令接口和 COM 验证；如果要求逐项证明“鼠标点击过每一个控件”，这件事仍无法在当前会话中验证。

AutoCAD 的网页试用流程记录仍见 [installation_status.txt](../notes/installation_status.txt)。本次本地实验使用的是已经运行的 AutoCAD 2027 实例；没有代填 MFA 验证码，也没有把网页试用流程当作本地 AutoCAD GUI 证据。

---

# Day 1 — 建筑 CAD 最小背景

## 一个足够小的例子

实验房间约为 `6000 mm × 4000 mm`，墙的概念厚度为 `200 mm`，入口门宽为 `900 mm`，上侧有两个 `1200 mm` 窗口，房间名为 `OFFICE`。

这里把建筑概念压缩到软件工程师容易操作的程度：先观察数据对象，再讨论建筑语义。

## 最小建筑词汇

- **平面图（Floor Plan）**：从上方看建筑的二维表达，通常展示房间、墙、门、窗、尺寸和文字。
- **墙（Wall）**：划分空间的构件。它有位置、方向、厚度，并可能连接到房间或其他构件。
- **门（Door）**：墙上的通行开口，常用门扇线和开启弧线表达。
- **窗（Window）**：墙上的采光/通风开口，常用两条平行线和框线表达。
- **楼梯（Stair）**：连接不同标高的构件，平面图中常用踏步线和方向箭头表达。本实验没有创建楼梯实体。
- **房间（Room）**：由边界围合出的空间，通常带有名称、编号、面积等信息。本实验用 `OFFICE` 文字表达房间名称，但没有创建语义化 Room 对象。
- **尺寸（Dimension）**：带有测量意义的 CAD 对象。本实验每个 DXF 都创建了两个真实 `DIMENSION` 实体，而不是只写两个数字。
- **轴网（Grid）**：帮助定位构件的参考系统。本实验用 `A-GRID` 图层放了一个小的 `G1` 标记，作为最小示例。
- **标高（Level）**：表示垂直方向的楼层或高度基准。本实验是单层二维房间，没有建立 Level 对象。
- **图层（Layer）**：组织实体的分类、颜色、线型和显示开关。本实验使用 `A-WALL`、`A-DOOR`、`A-WINDOW`、`A-TEXT`、`A-DIMS`、`A-GRID`。
- **块（Block）**：可复用的几何定义。插入块时，多个位置可以共享同一份定义；本次 DXF 实验没有把门或窗做成 BLOCK/INSERT，这正好可以和后续实验比较。

## 三个抽象层次

### LEVEL 1 — 视觉（Visual）

“它看起来像一面墙。”

这是人眼层面的结论。两条平行线、一个矩形、一个门扇弧线都可能让人读出建筑含义。

### LEVEL 2 — CAD 几何（CAD Geometry）

文件中实际保存的是对象类型和属性，例如：

`LINE`、`POLYLINE`、`ARC`、`CIRCLE`、`TEXT`、`MTEXT`、`DIMENSION`，以及它们的坐标、图层、颜色等。

两条平行 `LINE` 能够视觉上表示墙，但 AutoCAD 仅凭这两条线并不会自动知道“这是 Wall”。

同理，`LINE + ARC` 能够视觉上表示门，但它们不因此自动成为语义化 `Door`。

### LEVEL 3 — 建筑语义对象（Architecture Semantic Object）

这里的对象是 `Wall`、`Door`、`Window`、`Room`、`Stair` 等。它们通常带有更高层的信息，例如厚度、连接关系、开口关系、编号、材料或统计属性。

因此：

```text
视觉上像墙       ≠  CAD 中一定是 Wall
LINE + ARC       ≠  CAD 中一定是 Door
```

与天正（Tianzheng）的关系也要这样理解：

```text
AutoCAD primitive geometry
        ≠
Tianzheng semantic Wall / Door / Window
```

天正可能使用自己的扩展数据、对象类型或约定来表达建筑语义。普通 AutoCAD 几何可以“画得像”，但不一定具有天正对象的可编辑语义。

软件工程类比：直接画 `LINE` 类似调用 `draw_line()`；专业建筑工具更像调用 `create_wall()`、`create_door()`、`create_window()`。前者给出几何，后者通常还会维护领域规则。这个类比用于理解边界，不是两套系统的精确技术等价。

---

# Day 2 — AutoCAD Object Model

## 常见实体

- **LINE**：两个端点之间的直线段。本实验 A 的房间外轮廓使用四个独立 LINE。
- **POLYLINE / LWPOLYLINE**：多个顶点组成的连续路径；可以闭合。本实验 B 的房间外轮廓使用一个闭合 `LWPOLYLINE`。
- **ARC**：圆弧。本实验门的开启轨迹使用一个 `ARC`。
- **CIRCLE**：完整圆。本实验在 `A-GRID` 层放置了一个小圆作为网格标记。
- **TEXT**：单行文字。本实验有 `OFFICE` 和 `G1`。
- **MTEXT**：多行文字。本实验使用它写入房间尺寸、墙概念和边界模型说明。
- **DIMENSION**：有测量意义的尺寸实体。本实验每个文件有两个真实 DIMENSION：6000 和 4000。
- **BLOCK**：块定义，保存可复用内容。可以把它类比为模板或类定义。
- **INSERT**：块引用，把某个 BLOCK 放到模型中的某个位置。可以把它类比为实例化。
- **LAYER**：图层，承载实体的组织和显示属性。
- **ByLayer**：实体从其图层继承颜色、线型等属性。这样可以通过改图层控制一组对象，而不是逐个修改。

## Model Space 与 Paper Space

- **模型空间（Model Space）**：实际模型几何，通常按真实尺寸 1:1 绘制。本实验约定 `6000 drawing units = 6000 mm = 6 m`。
- **图纸空间（Paper Space / Layout）**：打印和出图布局，可以放图框、视口、标题栏，并控制打印比例。

DXF 和 DWG 中的实体已通过 AutoCAD COM 的 `ModelSpace` 集合验证。通过 AutoCAD 命令接口切换后，`Layout1` 的 Paper Space 状态也已验证：`TILEMODE = 0`、当前布局为 `Layout1`、`PaperSpace` 中有 1 个布局对象；随后已切回 Model Space。原生鼠标点击标签本身仍为 `NOT VERIFIED`。

## DWG 与 DXF

- **DXF**：公开程度较高、便于脚本读写和检查的交换格式。本实验用 `ezdxf` 生成并重新读取。
- **DWG**：AutoCAD 主要使用的工程文件格式，通常保存更完整的 AutoCAD 数据。

重要心智模型：

```text
DWG / DXF ≈ object database
          + geometry
          + properties
          + layers
          + dimensions
          + blocks / references
```

它不是一张已经“烘焙”完成的图片。可以把文件想成一个对象数据库：

```text
Object 001 | Type: LINE      | Layer: A-WALL
Object 002 | Type: ARC       | Layer: A-DOOR
Object 003 | Type: TEXT      | Content: OFFICE
Object 004 | Type: DIMENSION | Layer: A-DIMS
```

---

# Hands-on experiment

## 生成方式

源代码位于 [generate_lab.py](../src/generate_lab.py)。运行方式：

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\weila\Desktop\CAD-Day1-Day2-Lab\src\generate_lab.py'
```

校验代码位于 [validate_lab.py](../src/validate_lab.py)，运行方式：

```powershell
& 'D:\anaconda3\python.exe' 'C:\Users\weila\Desktop\CAD-Day1-Day2-Lab\src\validate_lab.py'
```

实际验证输出为 `VALIDATION_PASS`，并确认了两个文件都能被 `ezdxf.readfile()` 读取。

## Experiment A — LINE based drawing

文件：[day2_line_based.dxf](../output/day2_line_based.dxf)

主要结果：

- 房间尺寸：6000 mm × 4000 mm。
- 主房间边界：4 个独立 `LINE`。
- 门：1 个 `ARC` 加若干门扇/门框 `LINE`。
- 窗：两组简单窗框线。
- 房间名：`TEXT`，内容为 `OFFICE`。
- 说明：1 个 `MTEXT`。
- 尺寸：2 个 `DIMENSION`。
- 图层：`A-WALL`、`A-DOOR`、`A-WINDOW`、`A-TEXT`、`A-DIMS`、`A-GRID`。

实体清单中的总数为：`LINE x 15`、`ARC x 1`、`CIRCLE x 1`、`TEXT x 2`、`MTEXT x 1`、`DIMENSION x 2`。

## Experiment B — POLYLINE based drawing

文件：[day2_polyline_based.dxf](../output/day2_polyline_based.dxf)

它保持相同房间尺寸、门窗、文字、图层和尺寸，但主边界改成：

```text
1 个闭合 LWPOLYLINE
```

实体清单中的总数为：`LWPOLYLINE x 1`、`LINE x 11`、`ARC x 1`、`CIRCLE x 1`、`TEXT x 2`、`MTEXT x 1`、`DIMENSION x 2`。

### 最重要的 LINE vs POLYLINE 结论

**视觉上：** 两个图可以几乎一样。

**数据模型：**

```text
Experiment A: 4 independent LINE objects
Experiment B: 1 closed POLYLINE object
```

这就是“图纸看起来一样”与“文件中的对象模型一样”之间的差异。软件要做编辑、选择、长度统计、偏移、连接、转换或建筑语义识别时，这个差异会变得重要。

## AutoCAD 实例执行结果

以下动作已通过正在运行的 AutoCAD 2027 实例和 COM 自动化完成：

1. 打开 `day2_line_based.dxf`，读取 AutoCAD ModelSpace 并确认 `A-WALL` 为 4 个 `AcDbLine`。
2. 读取同一文件中的 `AcDbArc`、`AcDbCircle`、`AcDbText`、`AcDbMText` 和 `AcDbRotatedDimension`。
3. 读取 AutoCAD Layer 集合并确认 `A-WALL`、`A-DOOR`、`A-WINDOW`、`A-TEXT`、`A-DIMS`、`A-GRID` 等图层存在。
4. 打开 `day2_polyline_based.dxf`，确认 `A-WALL` 为 1 个 `AcDbPolyline`。
5. 通过 AutoCAD `SaveAs` 生成两个 DWG，再由 AutoCAD 重新打开；重开时实体数量分别为 22 和 19。
6. 通过 AutoCAD 内部预选集分别选中 `Line`、`Arc`、`Text`、`Rotated Dimension` 和 `Polyline`，随后打开 Properties 面板；五种对象类型、图层和关键属性均已在面板中截图确认。
7. 通过 `_.TILEMODE 0` 切换到 `Layout1` 的 Paper Space，确认 `active_space = 0`、`TILEMODE = 0`、`PaperSpace` 对象数为 1，并保存截图；随后通过 `_.TILEMODE 1` 切回 Model Space。

以下动作仍未执行，原因是本会话没有可用的原生窗口控制接口：

1. 用物理鼠标逐个点击墙线、门弧、`OFFICE`、尺寸和闭合多段线。
2. 用物理鼠标操作 Layers、ByLayer、Paper Space / Layout 控件。

因此，本实验没有把 DXF 改名冒充 DWG，也没有把 AutoCAD 内部预选冒充物理鼠标点击。对象类型的 Properties 面板验证已完成；可复核的完整结果见 [autocad_resource_inventory.txt](../notes/autocad_resource_inventory.txt)、[autocad_ui_equivalent_check.txt](../notes/autocad_ui_equivalent_check.txt) 和各对象的 `autocad_properties_*_focused.txt` 记录。

---

# Software engineering analogy

以下是帮助记忆的类比，不是 AutoCAD 内部实现的严格等价：

| CAD 概念 | 软件工程类比 | 边界 |
| --- | --- | --- |
| Entity | object / record | CAD 对象还有坐标、图层和图形属性 |
| Block Definition | class / template | 这是可复用定义的类比 |
| INSERT | instance | 引用一个块定义并放置到位置 |
| Layer | 分类或 namespace-like organization | 图层不是编程语言 namespace |
| Model Space | 正式模型数据 | 不是内存中的普通对象堆 |
| Paper Space | presentation / print view | 不是模型本体 |
| DWG / DXF | object database + serialized geometry | 不是图片文件 |
| `create_wall()` | domain-specific API | 普通 `LINE` 不会自动获得 Wall 语义 |

---

# Day 1 completion checklist

- [x] 我能解释 Floor Plan 是从上方表达建筑空间的二维图。
- [x] 我能区分 Wall、Door、Window、Stair、Room、Dimension、Grid、Level。
- [x] 我能解释 Layer 用来组织实体并控制显示属性。
- [x] 我能解释 Block Definition 与 INSERT 的复用关系。
- [x] 我能区分 Visual、CAD Geometry、Architecture Semantic Object 三个层次。
- [x] 我知道“两条平行 LINE”看起来像墙，但不自动等于语义化 Wall。
- [x] 我知道普通 AutoCAD 几何不自动等于天正 Wall / Door / Window。

# Day 2 completion checklist

- [x] 我在 DXF 文件中观察到了 `LINE`。
- [x] 我在 DXF 文件中观察到了闭合 `LWPOLYLINE`。
- [x] 我在 DXF 文件中观察到了 `ARC`。
- [x] 我在 DXF 文件中观察到了 `CIRCLE`。
- [x] 我在 DXF 文件中观察到了 `TEXT` 与 `MTEXT`。
- [x] 我在 DXF 文件中观察到了 `DIMENSION`。
- [x] 我知道 BLOCK 与 INSERT 的概念，但本次实验没有创建 BLOCK/INSERT。
- [x] 我在 DXF 文件中观察到了多个 LAYER。
- [x] 我理解 Model Space 与 Paper Space 的职责差异；命令接口状态已验证，原生鼠标点击标签仍为 `NOT VERIFIED`。
- [x] 我理解 DWG / DXF 更接近对象数据库，而不是图片。
- [x] 我能明确说出 Experiment A 与 B 的 LINE / POLYLINE 数据模型差异。
- [x] 我通过 AutoCAD 命令接口打开过 Properties 和 Layer Properties Manager。
- [x] 我通过 AutoCAD COM 确认过对象的 `Color = 256` 和 `Linetype = ByLayer`。
- [x] 我通过 AutoCAD 命令接口切换并确认过 `Layout1` 的 Paper Space，然后切回 Model Space。
- [x] 我在 AutoCAD Properties 面板中确认过 `Line`、`Arc`、`Text`、`Rotated Dimension` 和 `Polyline`；选择采用 AutoCAD 内部预选集，而非物理鼠标。
- [x] 我用 AutoCAD Save As 生成并重新打开过 DWG。已由 AutoCAD COM 验证；GUI 菜单点击本身未执行。

---

# Mini quiz

## Questions

1. 四个 `LINE` 和一个闭合 `POLYLINE` 可以看起来一样。它们是同一种数据结构吗？
2. 两条平行 `LINE` 是否自动意味着 AutoCAD 知道它们是一面 Wall？
3. Layer 的主要用途是什么？
4. 为什么语义化的天正 Wall 不等于普通 AutoCAD LINE 几何？
5. 为什么 CAD Agent 的工具 API 应明确指定单位？
6. `ARC` 和 `CIRCLE` 的区别是什么？
7. `TEXT` 和 `MTEXT` 的主要差别是什么？
8. `DIMENSION` 与只写着“6000”的普通文字有什么区别？
9. Block Definition 与 INSERT 如何类比为 class/template 与 instance？
10. Model Space 和 Paper Space 分别服务什么目的？

## Answers

1. 不是。前者是四个独立对象，后者是一个连续且闭合的多段线对象。
2. 不是。它们只提供几何；是否是 Wall 还取决于更高层的语义对象或应用约定。
3. 组织对象，并集中控制可见性、颜色、线型等属性。
4. 语义化 Wall 可能拥有厚度、连接、开口、材料等领域信息；普通 LINE 通常只有端点和图层等基础属性。
5. 因为 `6000` 可能表示 mm、cm、m 或英寸。单位不明确会使几何和自动化结果产生数量级错误。
6. `ARC` 是圆的一部分，`CIRCLE` 是完整圆。
7. `TEXT` 通常是单行文字；`MTEXT` 支持多行和更丰富的文字排版。
8. DIMENSION 保留测量对象和关联几何的意义；普通文字只是标签，数值不会随几何自动更新。
9. Block Definition 类似可复用的类/模板；INSERT 类似该定义的一个实例引用。
10. Model Space 放真实模型几何；Paper Space 放出图、视口、图框和打印布局。

---

# 最终结论

Day 1 + Day 2 最重要的一句话是：

> **CAD 图纸的视觉结果、底层几何实体、建筑语义对象是三个不同层次；一个图形“看起来正确”，不代表文件中的对象模型或建筑语义也正确。**

当 CAD Agent 后续生成墙、门、窗时，不能只追求“画出来像”，还必须明确单位、实体类型、图层、块/引用关系，以及目标软件是否需要真正的语义对象。
