# 参考动作接入与混合 v0.2

## 路线选择

- 已有匹配目标角色的 VMD：优先 mmd_tools 原生导入、保留完整动作，再做必要修正。不要无故把手指、根移动、扭转都压成 12 个点。
- 需要视频 + 参考融合：将参考在源骨架上正确播放，保存为 `.blend`，用 `sample_action.py` 采样到统一 12 点 JSON，再用 `mix_reference.py` 混合；最后 `bake_motion.py` 生成目标动作。
- FBX/BVH：先用 Blender 对应导入器打开，检查世界坐标 Z 向上、角色朝向、场景帧率和单位；保存 `.blend`。提供显式关节点映射，不能把 Mixamo/CMU 骨名直接套成 MMD 骨名。
- ASF+AMC：先选择经过核查的 BVH 转换，或另行配置转换工具；本版没有内置 ASF/AMC 解码。PMM 工程也不是直接输入。

导入阶段是 Blender/mmd_tools 或宿主代理完成的步骤，当前没有一个命令自动覆盖所有外部格式。脚本只负责已经导入好的 `.blend` 采样、标准 JSON 混合和烘焙。

## 采样参考

命令中 `TOOLS` 为本仓库或已安装 Skill 的 `scripts/tools`。例：

```powershell
blender --background reference.blend --python-exit-code 1 --python TOOLS/sample_action.py -- --armature ReferenceRig --start 10 --end 80 --meters-per-unit 1 --yaw 0 --output reference_pose.json
```

`start/end` 是 Blender 场景帧，包含首尾。输出帧率取场景 FPS，必须先确认导入动作时间基正确。单位参数是“1 个 Blender 世界单位等于多少米”，不会擅自读取显示单位来猜测比例。`--yaw` 仅绕世界 Z 轴旋转，不能修复躺倒的坐标系；先正确导入/旋转骨架。每帧减去髋中点，因此根位移会丢失。

默认自动匹配常见 MMD 骨。其他骨架通过 `--mapping joints.json` 提供 **全部 12 个关节点**，映射格式与烘焙用的角色映射不同：

```json
{
  "left_shoulder": {"bone":"mixamorig:LeftArm","point":"head"},
  "left_elbow": {"bone":"mixamorig:LeftForeArm","point":"head"},
  "left_wrist": {"bone":"mixamorig:LeftHand","point":"head"},
  "right_shoulder": {"bone":"mixamorig:RightArm","point":"head"},
  "right_elbow": {"bone":"mixamorig:RightForeArm","point":"head"},
  "right_wrist": {"bone":"mixamorig:RightHand","point":"head"},
  "left_hip": {"bone":"mixamorig:LeftUpLeg","point":"head"},
  "left_knee": {"bone":"mixamorig:LeftLeg","point":"head"},
  "left_ankle": {"bone":"mixamorig:LeftFoot","point":"head"},
  "right_hip": {"bone":"mixamorig:RightUpLeg","point":"head"},
  "right_knee": {"bone":"mixamorig:RightLeg","point":"head"},
  "right_ankle": {"bone":"mixamorig:RightFoot","point":"head"}
}
```

上例是常见命名模板，必须对照实际骨架。关节由已求值的骨骼 head/tail 得到，因此源 IK 应先正确工作，不能先删约束再采样。脚部取踝点，不取脚趾尖。

## 可运行的混合

```powershell
python TOOLS/mix_reference.py --base video_pose.json --reference reference_pose.json --base-range 0 89 --ref-range 5 65 --weight 0.35 --mask arms --output mixed_pose.json
blender --background character.blend --python-exit-code 1 --python TOOLS/bake_motion.py -- --pose mixed_pose.json --armature Armature --output mixed_motion.blend
```

混合区间使用 **JSON 的零起始索引、包含首尾**，与采样时 Blender 的场景帧区分。两段按归一化时间线性对应，不做动作语义识别。输出保持基础视频的帧数与 FPS。

`--mask arms` 只改肘腕；`legs` 只改膝踝；`all` 是这两组四肢，不含躯干/髋/肩。默认参考权重 35%，基础动作占其余部分；这与默认 65% 平滑是独立参数。球面插值混合骨段方向，保留基础动作各帧骨段长度，避免不同体型简单坐标平均造成缩短。

默认前后各 15% 的混合区间渐入/渐出，端点保持基础动作；`--fade 0` 关闭，仅用于明确希望硬切或整段替换的场景。接近反向的骨段会报错，应检查朝向、左右和选段，不能盲目继续。混合后再做 65% 平滑和脚锁，避免重复平滑。

35% 是可调起点，不保证美观。先试手臂参考，保持基础脚步；腿部混合需要重新检查接地与膝盖方向。不会恢复遮挡缺失超过 0.5 秒的动作，也不会自动生成招式风格。

## 验收与交付

记录参考来源、具体片段、贡献部位和权重。比较基础版与混合版的起手、蓄力峰值、击打峰值、收势；查看脚滑、穿模、手臂反折、接缝速度突变。机器测试通过只能证明数据路径和几何不变量，不能替代审片。

如没有实际动作文件，只交付候选清单和可运行流程，准确说“尚未使用第三方动作融合”。要声称某库动作参与制作，需有来源记录、真实文件、采样结果和融合报告；要声称效果改善，还需对比观察。
