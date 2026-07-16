# Hand-Eye Calibration

一个面向不同机械臂和相机的 Python 手眼标定项目。

> 本项目 Fork 自 [RealManRobot/hand_eye_calibration](https://github.com/RealManRobot/hand_eye_calibration)，并在原项目基础上重新整理了硬件适配边界、数据采集流程和开源使用文档。

项目通过同步采集棋盘格图像与机械臂末端位姿，使用 OpenCV 求解相机坐标系和机械臂坐标系之间的刚体变换，可用于视觉定位、机器人抓取和视觉伺服。

## 硬件兼容性说明

手眼标定算法本身不依赖特定品牌的机械臂或相机。只要硬件 SDK 能够提供：

- 机械臂末端相对基座的位姿；
- 与该位姿同步的彩色图像。

就可以接入本项目。

> [!IMPORTANT]
> 当前代码中保留了 **xArm + Intel RealSense** 的参考采集实现，但它们不是标定算法的限制。使用其他机械臂或相机时，只需替换 `collect_data.py` 中已明确标记的 SDK 适配区，后续标定计算代码不需改动。

## 第一次使用：先看这里

如果你是第一次做手眼标定，可以先不研究公式，按下面的顺序操作：

1. **确认相机安装方式**：相机装在末端就选 Eye-in-Hand，相机固定在机械臂外部就选 Eye-to-Hand。
2. **安装 Python 依赖和硬件 SDK**。
3. **接入机械臂和相机**：让程序能同时获取一张图像和对应的机械臂末端位姿。
4. **配置棋盘格内角点数和方格尺寸**。
5. **采集约 50 组数据**：重点覆盖目标物体将来可能出现的工作区域。
6. **运行对应的计算脚本**，得到旋转矩阵 `R` 和平移向量 `t`。
7. **用已知点验证结果**，确认误差可接受后，再接入机械臂抓取程序。

> [!CAUTION]
> 脚本能成功打印矩阵，不等于标定结果一定正确。在验证前，不要把结果直接用于高速或大范围机械臂运动。

## 新手需要知道的坐标系

| 名称 | 含义 |
| --- | --- |
| Base | 机械臂基座坐标系，机械臂的全局参考坐标系 |
| End / Gripper | 机械臂末端或工具坐标系 |
| Camera | 相机坐标系，视觉程序计算的物体位置通常先位于这个坐标系 |
| Board / Target | 棋盘格标定板坐标系 |

本文档使用 `T_A_B` 表示“**把 B 坐标系中的点转换到 A 坐标系**”的 4×4 齐次变换矩阵。例如：

```python
p_base = T_base_camera @ p_camera
```

表示将相机坐标系中的点 `p_camera` 转换到机械臂 Base 坐标系。

## 功能

- 同步保存棋盘格图像和机械臂位姿。
- 保存机械臂关节状态，方便数据追溯。
- 支持 Eye-in-Hand（眼在手上）。
- 支持 Eye-to-Hand（眼在手外）。
- 使用 OpenCV `calibrateCamera` 计算标定板位姿。
- 使用 OpenCV `calibrateHandEye` 求解 `AX = XB`。
- Eye-to-Hand 模式可对比 Tsai、Park、Horaud、Andreff 和 Daniilidis 方法。

## 标定模式

| 模式 | 相机安装方式 | 标定板安装方式 | 标定结果 |
| --- | --- | --- | --- |
| Eye-in-Hand | 固定在机械臂末端，随末端运动 | 固定在工作区 | 相机坐标系到末端坐标系的变换 |
| Eye-to-Hand | 固定在机械臂外部 | 刚性固定在机械臂末端 | 相机坐标系到基座坐标系的变换 |

## 整体流程

```text
连接相机和机械臂
        │
        ▼
同步采集图像 + 末端位姿
        │
        ▼
检测棋盘格角点
        │
        ▼
计算标定板在相机坐标系下的位姿
        │
        ▼
将机械臂位姿转换为齐次变换矩阵
        │
        ▼
求解手眼变换
```

## 项目结构

```text
.
├── collect_data.py          # 硬件数据采集与同步
├── compute_in_hand.py       # Eye-in-Hand 标定
├── compute_to_hand.py       # Eye-to-Hand 标定
├── save_poses.py            # 位姿转齐次变换矩阵
├── save_poses2.py           # 位姿取逆，用于 Eye-to-Hand
├── config.yaml              # 棋盘格参数
├── libs/
│   ├── auxiliary.py         # 连接参数选择、数据目录等辅助函数
│   └── log_setting.py       # 日志配置
├── picture/                 # 文档图片
├── requirements.txt
└── README.md
```

## 安装

### 1. 创建虚拟环境

建议使用 Python 3.10。

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2. 安装标定依赖

```bash
pip install -r requirements.txt
```

### 3. 安装硬件 SDK

根据你使用的硬件，另行安装：

- 机械臂厂商提供的 Python SDK；
- 相机厂商提供的 Python SDK。

不同品牌、型号和操作系统的 SDK 安装方式不同，因此项目不能用一份通用依赖列表覆盖所有硬件。当前 `requirements.txt` 保留了参考相机实现所需的 `pyrealsense2`；使用其他相机时可移除该依赖并安装相应 SDK。机械臂 SDK 需按实际硬件另行安装。

## 接入机械臂

机械臂 SDK 的替换位置位于 `collect_data.py`，已用以下注释标记：

```text
机械臂 SDK 适配点 1/4
机械臂 SDK 适配点 2/4
机械臂 SDK 适配点 3/4
机械臂 SDK 适配点 4/4
```

可以直接搜索：

```bash
grep -n "机械臂 SDK 适配\|xArm SDK" collect_data.py
```

### 需要替换的能力

| 位置 | 当前参考实现 | 更换时需提供 |
| --- | --- | --- |
| `collect_data.py` 的 SDK 导入 | xArm SDK | 新机械臂 SDK 的导入 |
| `displayD435()` 内的连接区 | `XArmAPI(...)` | 创建机械臂客户端 |
| `send_cmd()` | 读取 xArm 位姿、关节角和错误码 | 读取并归一化机械臂状态 |
| `displayD435()` 内的初始化区 | 清错、使能、设置运动模式 | 新机械臂需要的初始化流程 |
| `finally` 资源释放区 | `arm.disconnect()` | 断开新机械臂连接 |

### 机械臂数据接口约定

新机械臂适配代码最终需向采集逻辑提供：

```python
success = True
pose = [x, y, z, rx, ry, rz]
joints = [j1, j2, ...]
```

| 字段 | 约定 |
| --- | --- |
| `x, y, z` | 机械臂末端在基座坐标系下的位置，单位为米 |
| `rx, ry, rz` | XYZ 欧拉角，单位为弧度 |
| `joints` | 关节角列表，只用于记录，不参与当前标定计算 |

项目使用 `Rz @ Ry @ Rx` 将欧拉角转换为旋转矩阵。如果新机械臂 SDK 使用四元数、旋转向量、其他欧拉角顺序或不同单位，必须在 `send_cmd()` 中完成转换。

如果连接方式不是 IP，可以同时替换 `libs/auxiliary.py` 中的 `get_ip()`，或将它改为读取命令行参数/配置文件。

## 接入相机

相机 SDK 的替换位置也位于 `collect_data.py`，已用以下注释标记：

```text
相机 SDK 依赖
相机 SDK 适配点 1/3
相机 SDK 适配点 2/3
相机 SDK 适配点 3/3
```

可以直接搜索：

```bash
grep -n "相机 SDK" collect_data.py
```

### 需要替换的能力

| 位置 | 当前参考实现 | 更换时需提供 |
| --- | --- | --- |
| `collect_data.py` 顶部 | `pyrealsense2` | 新相机 SDK 的导入 |
| `displayD435()` 开始处 | RealSense pipeline/config | 创建相机、配置彩色流并启动 |
| `displayD435()` 循环内 | RealSense 取帧 | 获取一帧彩色图像并转换格式 |
| `finally` 资源释放区 | `pipeline.stop()` | 停止相机并释放资源 |

### 相机数据接口约定

新相机 SDK 只需最终产生 OpenCV 可用的 BGR 图像：

```python
color_image: numpy.ndarray  # shape = (height, width, 3), dtype = uint8, BGR
callback(color_image, arm=arm)
```

如果相机输出 RGB、Bayer、YUV 或厂商自定义帧对象，请在“相机 SDK 适配点 2/3”中转换为 BGR `numpy.ndarray`。

`callback()` 中包含棋盘格检测、按键处理和数据保存逻辑，更换相机时通常不需修改。

## 配置棋盘格

编辑 `config.yaml`：

```yaml
checkerboard_args:
  XX: 14     # 水平方向内角点数
  YY: 9      # 垂直方向内角点数
  L: 0.01    # 单个方格边长，单位：m
```

- `XX` 和 `YY` 是内角点数，不是方格数。
- `L` 的单位决定最终平移向量的单位，默认使用米。

> [!IMPORTANT]
> `collect_data.py` 的角点检测尺寸目前固定为 `(14, 9)`。如果更换棋盘格，除了修改 `config.yaml`，还需同步修改 `collect_data.py` 中的两处 `(14, 9)`。

## 采集标定数据

Eye-in-Hand 和 Eye-to-Hand 共用 `collect_data.py`。硬件适配完成后运行：

```bash
python collect_data.py
```

程序会：

1. 创建 `eye_hand_data/dataYYYYMMDD/` 数据目录。
2. 连接并初始化机械臂。
3. 启动彩色相机。
4. 显示棋盘格角点检测窗口。

### 采集操作

1. 移动机械臂，使棋盘格完整、清晰地出现在画面中。
2. 确认窗口中已正确绘制棋盘格角点。
3. 将键盘焦点放在 OpenCV 窗口，按 `s` 保存当前图像和机械臂状态。
4. 改变末端的位置和姿态，重复采集。
5. 结束时在终端按 `Ctrl+C`。

每次按 `s` 会保存：

```text
eye_hand_data/dataYYYYMMDD/
├── 1.jpg
├── 2.jpg
├── ...
├── poses.txt          # x,y,z,rx,ry,rz；m/rad
└── joint_states.txt   # 关节角，仅用于记录
```

### 样本建议

> [!IMPORTANT]
> **样本的覆盖范围、姿态多样性和图像质量会直接影响标定结果。请重点遵循以下建议：**
>
> - **建议采集约 50 组高质量有效样本。** 样本应具有不同的位置和姿态，避免采集大量几乎相同的重复数据。
> - **围绕实际工作区域采集。** 工作区域是指任务运行时目标物体可能出现的大致空间范围。应尽量让标定板位姿覆盖该区域，而不是刻意让标定板填满整幅图像。这样获得的标定结果通常更符合实际使用场景。
> - **不要只做平移。** 需要在多个旋转轴上产生充分的姿态变化，同时覆盖工作区域内不同的深度、高度和方向。
> - **保证每组数据的图像质量。** 标定板必须完整可见，但不必填满画面；同时应避免运动模糊、反光、欠曝和角点遮挡。
> - **保持图像与机械臂位姿严格同步。** 每张图像必须与 `poses.txt` 中同序号的位姿一一对应。

## Eye-in-Hand

### 安装方式

1. 将相机刚性固定在机械臂末端。
2. 将棋盘格固定在工作区，整个采集过程中不得移动。

![Eye-in-Hand 安装示意图](picture/f6c716fb-c8d2-4adc-b3da-a86c6b1e78d0.png)

*Eye-in-Hand：相机安装在机械臂末端并随末端运动，标定板固定在工作区中。*

### 计算

```bash
python compute_in_hand.py
```

脚本会自动选择 `eye_hand_data/` 中名称最新的数据目录，并输出：

- 相机坐标系到机械臂末端坐标系的旋转矩阵；
- 平移向量；
- 四元数 `[x, y, z, w]`。

当前默认使用 Tsai 方法。

## Eye-to-Hand

### 安装方式

1. 将相机刚性固定在机械臂外部。
2. 将棋盘格刚性固定在机械臂末端，采集期间不得产生相对移动。

![Eye-to-Hand 安装示意图](picture/44776e79-47f7-4de2-9ef2-172b654169d5-17291349013411.png)

*Eye-to-Hand：相机固定在机械臂外部，标定板固定在机械臂末端并随末端运动。*

### 计算

```bash
python compute_to_hand.py
```

脚本会输出相机坐标系到机械臂基座坐标系的：

- 旋转矩阵；
- 平移向量；
- 四元数 `[x, y, z, w]`；
- XYZ 欧拉角，单位为度；
- 五种 OpenCV 手眼标定方法的对比结果。

## 中间文件

计算脚本会在项目根目录生成 `RobotToolPose.csv`。它是从 `poses.txt` 生成的齐次变换矩阵集合，属于可重新生成的中间数据。

标定数据和生成文件不应作为源码提交：

```text
eye_hand_data/
RobotToolPose.csv
calibration_result.txt
matrix.txt
```

## 最终会得到什么结果

运行计算脚本后，终端会打印类似下面的内容：

```text
旋转矩阵是:
[[r11 r12 r13]
 [r21 r22 r23]
 [r31 r32 r33]]

平移向量是:
[[tx]
 [ty]
 [tz]]

四元数是:
[qx qy qz qw]

欧拉角是:          # Eye-to-Hand 脚本会打印
[rx ry rz]
```

### 这些数值分别是什么

| 结果 | 含义 | 单位/顺序 | 是否推荐直接使用 |
| --- | --- | --- | --- |
| 旋转矩阵 `R` | 两个坐标系之间的旋转关系 | 3×3 矩阵 | **推荐** |
| 平移向量 `t` | 两个坐标系原点之间的平移关系 | 默认为米 | **推荐** |
| 四元数 | `R` 的另一种旋转表示 | `[x, y, z, w]` | 只在下游系统需要四元数时使用 |
| 欧拉角 | `R` 的另一种旋转表示 | XYZ，度 | 主要用于人工查看，不建议作为主要存储格式 |

> [!IMPORTANT]
> `R`、四元数和欧拉角是**同一个旋转结果的三种表示方式**，不是三个不同的标定结果。对初学者来说，最简单、最不容混淆的做法是始终保存并使用 **旋转矩阵 `R` + 平移向量 `t`**。

### Eye-in-Hand 的结果方向

`compute_in_hand.py` 当前使用 Tsai 方法，输出：

```text
T_end_camera
```

它的含义是：将相机 Camera 坐标系中的点，转换到机械臂末端 End 坐标系。

### Eye-to-Hand 的结果方向

`compute_to_hand.py` 会分别打印五种方法的：

```text
T_base_camera
```

它的含义是：将相机 Camera 坐标系中的点，直接转换到机械臂 Base 坐标系。

## 如何选择标定结果

### Eye-in-Hand

当前脚本只计算 Tsai 方法，因此没有多组算法结果需要选择。但是，**仍然必须验证 Tsai 结果的实际误差**。

### Eye-to-Hand

当前脚本会依次计算：

1. Tsai
2. Park
3. Horaud
4. Andreff
5. Daniilidis

这五组数值是五种求解方法对同一批数据的计算结果。
不存在一个对所有机械臂、相机、安装方式和采样数据都一定最好的方法，因此必须使用实际验证误差选择。

> [!WARNING]
> 脚本目前会在循环结束后返回最后一组 Daniilidis 结果，但这**不代表 Daniilidis 一定最好**。不要因为它是最后打印或最后返回的结果就直接选择它。

推荐使用以下方法选择：

1. **先排除明显异常的结果**：包含 `NaN`、无穷大、平移量级明显不可能，或与其他方法完全不一致的结果不应直接使用。
2. **查看五种方法是否大致一致**：如果多种方法的平移和旋转非常接近，说明这批数据的求解通常更稳定。如果差异很大，应优先重新检查样本质量、单位、坐标系方向和图像/位姿同步，而不是随便挑一组。
3. **在实际工作区域放置多个验证点**：建议选择至少 5～10 个不同位置和深度的点。
4. **分别使用每种方法转换验证点**，比较转换后的机械臂 Base 坐标与已知真值。
5. **选择平均误差小、最大误差也可接受的方法**。不要只看某一个点的误差。
6. **重新采集或抽取部分样本再计算一次**。如果某种方法多次结果都比较接近，说明它在当前设备和数据上更稳定。

如果完全没有真值或已知点，只能根据多种方法的一致性做初步判断，不能证明结果已经准确。

### 一个最简单的位置误差计算

```python
import numpy as np

# 标定结果转换得到的 Base 坐标，单位：m
estimated_point = np.array([x_est, y_est, z_est])

# 验证点在 Base 坐标系中的已知坐标，单位：m
reference_point = np.array([x_ref, y_ref, z_ref])

error_m = np.linalg.norm(estimated_point - reference_point)
error_mm = error_m * 1000
print(f"位置误差: {error_mm:.2f} mm")
```

## 如何使用标定结果

### 1. 把 `R` 和 `t` 组合成 4×4 矩阵

```python
import numpy as np

def make_transform(rotation_matrix, translation_vector):
    transform = np.eye(4, dtype=float)
    transform[:3, :3] = np.asarray(rotation_matrix, dtype=float)
    transform[:3, 3] = np.asarray(translation_vector, dtype=float).reshape(3)
    return transform

T = make_transform(R, t)
```

### 2. 转换一个三维点

假设视觉程序已经得到物体在相机坐标系中的三维坐标：

```python
def transform_point(transform, point_xyz):
    point_h = np.append(np.asarray(point_xyz, dtype=float), 1.0)
    transformed = transform @ point_h
    return transformed[:3]

# 例如：物体在相机前方某处，单位必须与标定结果一致
p_camera = np.array([x_camera, y_camera, z_camera])
```

#### Eye-in-Hand

Eye-in-Hand 的相机会随机械臂末端运动，因此每次使用都需读取机械臂当前的 `T_base_end`：

```python
T_end_camera = make_transform(R, t)  # compute_in_hand.py 的结果
T_base_camera = T_base_end @ T_end_camera
p_base = transform_point(T_base_camera, p_camera)
```

#### Eye-to-Hand

Eye-to-Hand 的相机固定在机械臂外部，因此 `T_base_camera` 在相机没有移动时是固定的：

```python
T_base_camera = make_transform(R, t)  # 选定的 compute_to_hand.py 结果
p_base = transform_point(T_base_camera, p_camera)
```

`p_base` 就是物体在机械臂 Base 坐标系下的位置。后续还需结合夹爪长度、TCP 偏移、抓取姿态和安全路径，才能真正生成机械臂运动命令。

### 3. 转换一个完整的物体位姿

如果视觉程序输出的不只是一个点，而是物体在相机坐标系中的完整位姿 `T_camera_object`，则：

```python
T_base_object = T_base_camera @ T_camera_object
```

`T_base_object[:3, 3]` 是物体在 Base 坐标系下的位置，`T_base_object[:3, :3]` 是物体在 Base 坐标系下的旋转。

### 4. 建议如何保存最终结果

当前脚本只会把最终结果打印到终端，不会自动生成最终标定文件。`RobotToolPose.csv` 是计算过程中的中间文件，**不是最终手眼标定结果**。

建议将通过验证的结果保存为 YAML，并明确记录方向、方法和单位：

```yaml
mode: eye_to_hand
method: Park  # 仅为格式示例，请填写验证后选定的方法
transform: T_base_camera
translation_unit: meter
quaternion_order: xyzw
rotation_matrix:
  - [r11, r12, r13]
  - [r21, r22, r23]
  - [r31, r32, r33]
translation:
  - tx
  - ty
  - tz
validation:
  mean_position_error_mm: 0.0
  max_position_error_mm: 0.0
```

> [!CAUTION]
> 在将标定结果用于真实机械臂运动前，必须检查：变换方向、位移单位、四元数顺序、欧拉角顺序、TCP/工具坐标系，以及验证点误差。

## 常见问题

### 棋盘格角点检测失败

- 核对内角点数，不要将方格数当作内角点数。
- 确保标定板完整出现在画面中。
- 减少反光、运动模糊和边缘遮挡。

### `calibrateHandEye` 报旋转不足

- 增加具有明显旋转差异的样本。
- 不要只沿单一方向平移。
- 让多个旋转轴都有充分变化。

### 计算脚本选错数据目录

计算脚本默认选择名称最新的 `dataYYYYMMDD*` 目录。删除误创建的空目录，或在计算脚本中显式指定数据目录。

### 更换 SDK 后位置结果明显错误

优先检查：

1. 位移是否已统一为米。
2. 旋转是否已统一为弧度。
3. SDK 返回的是末端相对基座，还是基座相对末端。
4. 欧拉角顺序是否与 `Rz @ Ry @ Rx` 一致。
5. 采集和使用结果时的 TCP/工具坐标系是否一致。

## 已知限制

- 当前硬件适配代码仍与参考 SDK 写在同一采集脚本中，尚未抽象成独立插件。
- 采集脚本中的棋盘格角点数尚未与 `config.yaml` 共享。
- 计算脚本默认选择最新数据目录，尚无命令行参数。
- 尚未自动计算重投影误差、留一验证误差或稳定性指标。
- 尚未提供自动化硬件测试和无硬件模拟数据测试。

## 开源许可

本 Fork 中由 WangZY233 完成的原创内容与修改以 [MIT License](LICENSE) 发布。

> [!NOTE]
> 上游仓库 `RealManRobot/hand_eye_calibration` 当前未提供许可证文件。本 Fork 添加的 MIT 许可证仅适用于 WangZY233 拥有权利的原创内容和修改，不会自动重新授权上游代码。详见 [NOTICE](NOTICE)。
