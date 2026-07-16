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

- 建议采集 15～30 组有效样本。
- 不要只做平移，需要在多个旋转轴上产生充分的姿态变化。
- 标定板必须完整可见，并避免运动模糊、反光和欠曝。
- 每张图像必须与 `poses.txt` 中同序号的位姿一一对应。

## Eye-in-Hand

### 安装方式

1. 将相机刚性固定在机械臂末端。
2. 将棋盘格固定在工作区，整个采集过程中不得移动。

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

## 使用标定结果

将旋转矩阵 `R` 和平移向量 `t` 组合成齐次变换：

```python
import numpy as np

T = np.eye(4)
T[:3, :3] = R
T[:3, 3] = np.asarray(t).reshape(3)
```

Eye-in-Hand：

```python
p_base = T_base_end @ T_end_camera @ p_camera
```

Eye-to-Hand：

```python
p_base = T_base_camera @ p_camera
```

> [!CAUTION]
> 在将标定结果用于真实机械臂运动前，必须用已知点验证变换方向、TCP/工具坐标系、长度单位和旋转约定。

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

## 贡献

欢迎提交 Issue 和 Pull Request，特别欢迎：

- 新的机械臂适配实现；
- 新的相机适配实现；
- 硬件适配器接口抽象；
- ChArUco/AprilTag 标定板支持；
- 标定结果评估和异常样本剔除；
- 模拟数据、单元测试和 CI。

提交代码前请至少运行：

```bash
python -m py_compile \
  collect_data.py compute_in_hand.py compute_to_hand.py \
  save_poses.py save_poses2.py
```

请不要提交包含内网 IP、现场图像、真实机械臂位姿或其他敏感信息的标定数据。

## 开源许可

本 Fork 的原创贡献与修改以 [MIT License](LICENSE) 发布。

> [!NOTE]
> 上游仓库 `RealManRobot/hand_eye_calibration` 当前未提供许可证文件。本 Fork 添加的 MIT 许可证仅适用于本 Fork 贡献者拥有权利的原创内容和修改，不会自动重新授权上游代码。详见 [NOTICE](NOTICE)。
