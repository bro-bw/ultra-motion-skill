# Ultra Motion Studio · Skill v0.2.1 / 可选插件 v0.1

v0.2 新增：动作库候选导航、Blender 已导入参考动作采样、按片段和四肢部位进行方向混合。详见 [动作库候选](motion-libraries.md) 与 [参考动作流程](reference-workflow.md)。v0.2.1 整理仓库文档和自动检查，不改变算法。历史功能验证使用合成动作，未下载或融合具体第三方库动作。

默认：平滑 **65%**、脚底锁定 **开启**、循环 **关闭**。本版输出 Blender Action 与 `.blend`；不把“动作卡”定义为其他软件专有卡片格式。可选 VMD 通过另装的 mmd_tools 导出。

## 交付与规划

主要入口为 `ultra-motion` Skill：让助手调度本地工具。可选 Blender 插件仅提供面板，二者复用相同代码。没有服务器、账号或付费服务要求。

本次实现的流程：视频 → 本地 MediaPipe Pose Landmarker → 标准姿态 JSON → 置信度过滤与短缺失补帧 → 65% 平滑 → 骨骼匹配 → 身体/四肢方向重定向 → 接触脚位双骨骼求解 → 新骨架 Action → 新 `.blend` 与诊断报告。

后续迭代应以用户真实视频和角色模型为验收素材，再添加骨盆朝向/根位移、手指、自动 VMD IK 开关及人工修正面板。本次没有实现这些能力。v0.2 的参考融合只处理四肢方向，不是完整动作风格迁移。

| 能力 | 当前状态 | 条件 |
|---|---|---|
| 内置合成动作演示 | 可运行，Blender 4.2.0 实测 | Blender，无需姿态模型 |
| 姿态 JSON 到动作 | 可运行 | 匹配的骨架或内置演示骨架 |
| 65% 平滑、补帧、脚位接触锁定 | 已实现并测试 | 脚锁为启发式，不保证任意动作无滑步 |
| 参考视频转姿态 | 已实现独立命令 | Python、MediaPipe、OpenCV、官方 `.task` 模型 |
| PMX/PMD 导入与 VMD 导出 | 复用外部 mmd_tools | 另行安装；本次未用真实 PMX 验证 |
| 手指、表情、全局走位、完整扭转 | 未实现 | 后续模型/算法支持 |
| 参考动作采样与片段混合 | v0.2 已实现 | 参考需先正确导入 Blender；JSON 混合可独立运行 |
| 奥特曼专有招式数据库 | 未提供 | 已加入通用格斗候选导航，不等于原版招式 |

## Skill 使用

下载本仓库源码，将文件夹命名为 `ultra-motion`，放到 Codex 的个人 skills 目录。确认 `skills/ultra-motion/SKILL.md` 存在。重新加载后可说：

> 使用 $ultra-motion，把这个全身参考视频转为这个 Blender/MMD 角色的动作，平滑 65%，脚底锁定开启，不循环。

本仓库与安装后的 Skill 使用同一布局，工具位于 `scripts/tools/`。以下命令从仓库或 Skill 根目录执行。Skill 负责调度，仍然需要实际可执行的 Blender 与姿态模型。

## 立即试跑，无需视频或模型

在仓库根目录运行（将 `blender` 换成自己的可执行文件路径）：

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/tools/bake_motion.py -- --demo --output work/demo_new.blend
```

生成 `.blend` 与 `.report.json`，打开新生成的文件后从第 1 帧播放。仓库不捆绑预生成的 `.blend`。这是合成站立手臂动作，不是视频识别结果。默认场景 24fps，90 帧 30fps 输入按时间换算为分数关键帧，保留时长。

## 视频转动作

1. 使用固定机位、单人、全身清晰的短视频；先把可变帧率视频转换为固定帧率。建议先用 3–10 秒片段。多人物、遮挡、快速翻滚、宽松服装和特摄服装都可能降低精度。
2. 使用独立 Python 3.12 环境，勿向 Blender 自带 Python 安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/tools/requirements.txt
```

3. 从 Google 下载 [Pose Landmarker Full 模型](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task)。模型和 Python 依赖不包含在 ZIP 中；下载后在本地 CPU 推理，素材无需上传。
4. 提取姿态：

```powershell
.\.venv\Scripts\python.exe scripts/tools/extract_video.py --video reference.mp4 --model pose_landmarker_full.task --output pose.json
```

5. 用 mmd_tools 导入 PMX/PMD，保存角色为 `character.blend`。记录 Armature 对象名（不是网格名）。也可使用已有 `.blend`。
6. 生成新动作：

```powershell
blender --background character.blend --python-exit-code 1 --python scripts/tools/bake_motion.py -- --pose pose.json --armature Armature --output motion_new.blend
```

可选参数：`--smoothing 65`、`--no-foot-lock`、`--loop`、`--mapping mapping.json`。已有输出会报错，避免覆盖。原文件不会被写入。新文件中原始角色被隐藏，复制的网格绑定新骨架。副本移除约束并清除对象动画，复杂物理和形态键动画不保证保真。

VMD：在已加载 mmd_tools 的 Blender 环境中追加 `--vmd motion_new.vmd`。若导出失败，退出码非零，报告会记录原因，但成功生成的 `.blend` 仍保留。此路径尚未完成真实 MMD 模型往返验证。目标 MMD 中必须关闭腿部 IK 后使用本版 FK 腿部动作；本版不写入 VMD IK 开关。

## 可选插件

本仓库主要交付 Skill，不附带预构建的 Blender 插件 ZIP。需要面板时，只将 `scripts/ultra_motion_studio/` 文件夹打包为 ZIP，并保留该文件夹为 ZIP 顶层目录。Blender 4.2：编辑 → 偏好设置 → 插件 → 从磁盘安装该 ZIP，启用 Ultra Motion Studio。不要把完整仓库当成 Blender 插件安装。

在 3D 视图按 N，打开 Ultra Motion。可先点击“运行内置演示”。实际使用时在对象模式选择角色骨架，选取姿态 JSON，再点击“生成动作到骨架副本”。插件只复制骨架，原网格仍绑定原骨架；要自动复制并重绑网格，使用上述 Skill/命令入口。

插件面板不直接启动视频推理；参考视频提取由独立脚本完成。Blender 4.2.0 实测；4.4+ Action API 已做适配但未实测，不承诺全部版本兼容。

## 骨骼映射

识别实际骨骼名及 `mmd_bone.name_j/name_e`。默认支持 `上半身`、`左腕/右腕`、`左ひじ/右ひじ`、`左足/右足`、`左ひざ/右ひざ`，以及 `left arm`、`left elbow` 等英文别名。需要 9 个角色，缺失时拒绝生成。非标准骨架用映射文件：

```json
{
  "spine": "上半身",
  "left_upper_arm": "左腕", "right_upper_arm": "右腕",
  "left_forearm": "左ひじ", "right_forearm": "右ひじ",
  "left_thigh": "左足", "right_thigh": "右足",
  "left_shin": "左ひざ", "right_shin": "右ひざ"
}
```

映射值必须是 Blender 中的实际骨骼名。小腿须是大腿后代，前臂须是上臂后代。推荐常规 MMD 骨架；辅助扭转骨可能需要后续适配。

## 算法与限制

- 身体仅驱动上半身纵向，四肢按目标方向求四元数；保留骨骼静止轴，但没有完整轴向扭转解算。髋部位置固定，不能还原跑步位移或大幅转身。
- 平滑 65% 是对称窗口均值与原始关节位置的混合权重，窗口半径约 67ms；不是准确率或抖动降低承诺。
- 置信度低于 0.5 视为缺失；最多约 0.5 秒缺失以线性插值补齐，边缘短缺失保持最近值；更长缺失拒绝处理。
- 脚底锁定实际约束的是小腿末端/踝关节，不追踪鞋底几何和脚趾滚动。接触阈值为低位 5.5cm 范围与速度小于 0.18m/s，接触期间锚定脚位，再做双骨骼求解。超出腿长可达范围时夹紧并计入报告，可能产生滑动。没有根部补偿或接触释放融合。
- 首帧踝点对齐骨架静止脚位；尺度来自左腿长度。输入采用髋部相对坐标，不能等同真实世界场景坐标。
- 循环开启时追加 0.2 秒回到首帧的过渡及 Cycles 修饰器；不是自动生成自然无缝循环。默认关闭。
- 输出动作使用线性关键帧与四元数符号连续化；不保留原有 IK、物理和驱动器行为。始终在副本工作。

## 姿态 JSON 规范

`schema` 为 `ums.pose.v1`；`coordinates` 为 `x_right_y_back_z_up_m`；`fps` 为 1–240 的有限数；`frames` 为按时间顺序排列的 2–36000 帧。每帧有 `joints` 字典，包含左右 shoulder/elbow/wrist/hip/knee/ankle 共 12 点；每点是 `[x,y,z,confidence]`，单位米、置信度 0–1。缺失点可省略。MediaPipe 世界坐标转换为 `(x,-z,-y)`。不接受 2D 屏幕像素或任意其他坐标系。

诊断字段：`frames`、`fps`、`repaired_landmarks`（补过的关节点数）、`locked_foot_frames`（左右脚累计）、`unreachable_foot_frames`、`mapping`、默认选项及 `vmd_export`。

## 复现测试

```powershell
python -m unittest discover -s scripts/tests -p "test_*.py" -v
blender --background --factory-startup --python-exit-code 1 --python scripts/tests/blender_smoke.py
blender --background --factory-startup --python-exit-code 1 --python scripts/tests/blender_reference.py
```

实际结果见 [验证记录](VALIDATION.md) 和 `scripts/tests/*.log`。日志为原始开发阶段的历史证据；当前发布复查范围另在验证记录注明。

## 官方参考

- [MediaPipe Pose Landmarker Python 文档](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)：本地视频推理与世界坐标点。
- [Blender Python API](https://docs.blender.org/api/current/bpy.types.Bone.html)：骨骼空间转换。
- [MMD Tools 官方仓库](https://github.com/MMD-Blender/blender_mmd_tools)：PMX/PMD/VMD 导入导出。此项目为配套工具，不是官方 mmd_tools 的组成部分。
