---
name: ultra-motion
description: 从单人视频、姿态 JSON 或已导入 Blender 的参考动作生成 MMD 身体动作；查找 MMD/CMU/Mixamo 动作参考，采样并按片段及四肢部位融合。用于视频转动作、格斗或奥特曼起手式制作；不用于角色建模或保证精确复刻。
---

# Ultra Motion · Skill v0.2.1

使用随附 `scripts/` 中的确定性工具完成视频到动作的最小流程。默认平滑 65%、脚底锁定开启、循环关闭；以用户明确设置为准。无需安装 Blender 界面插件。

## 选择工作路线

- 视频单独生成：按下方执行流程。
- 查找或利用现有动作：先读 [动作库与候选](references/motion-libraries.md)，优先匹配招式目的、出招侧与骨骼要求。六个用户指定入口已纳入导航；网页条目不是已取得的动作资产。
- 视频与参考混合：读 [参考采样和混合](references/reference-workflow.md)，使用 `sample_action.py` 与 `mix_reference.py`。默认参考权重 35%、只混合手臂，独立于平滑 65%；具体依任务调整。
- 直接应用 VMD：若原动作已适配目标，优先保留原生 mmd_tools 路线，避免不必要地丢弃手指、根位移和扭转。

## 输入与能力边界

- 视频仅支持单人、全身可见、近正面、固定机位。需要已有 Blender 和独立 Python + MediaPipe Tasks + 官方 `.task` 模型。本 Skill 本身不是姿态估计模型，不假装从视觉描述得到真实动捕数据。
- `.blend` 内的 MMD 骨架可直接使用；PMX/PMD 需先用已安装的 mmd_tools 导入 Blender 并另存为 `.blend`。不能把任意人物卡、角色图片或其他软件的卡片当成骨架。
- 只做身体方向与四肢；髋部位置固定，无相机运动恢复、全局位移、手指表情、完整骨盆/躯干扭转。脚锁是启发式接触检测加双骨骼求解；记录不可达脚位，不宣称绝对无滑步。
- 输出新 `.blend`、同名 `.report.json`；VMD 仅在 mmd_tools 可用时尝试，并独立验证。骨架副本去除约束，生成 FK 动作；MMD 播放 FK 腿部动作须关闭目标模型的腿 IK。
- 已实现标准姿态 JSON 的选段与四肢方向混合，以及已导入 Blender 的参考骨架采样。VMD/BVH/FBX 仍需先正确导入 Blender；不直接混合原始文件，也不自动完成语义匹配或招式风格迁移。当前包不含第三方动作，合成测试不能冒充动作库融合。

## 执行

1. 先检查用户提供的视频、模型文件和本机 Blender/Python。若缺少真实输入，可运行内置合成演示验证环境，明确标注合成；只询问真正缺少的文件或骨架选择。
2. 视频输入时，在独立环境安装 `scripts/tools/requirements.txt`。官方模型地址、命令和 JSON 规范见 [运行说明](references/README.md)。不向外部服务上传素材；本流程使用本地 CPU 推理。不得把依赖安装进 Blender 自带 Python。
3. 运行 `scripts/tools/extract_video.py --video VIDEO --model MODEL --output POSE_JSON`。固定帧率输入；可变帧率视频先规范化帧率。JSON 已存在时改用新文件名。超过 0.5 秒的低可信缺失在烘焙时明确报错，不能伪造补齐。
4. 执行动作生成：`BLENDER --background INPUT.blend --python-exit-code 1 --python SKILL/scripts/tools/bake_motion.py -- --pose POSE_JSON --armature ARMATURE_NAME --output NEW_OUTPUT.blend`。平滑覆盖用 `--smoothing 65`；关闭脚锁用 `--no-foot-lock`；循环用 `--loop`。骨骼匹配失败先检查骨架，按说明提供 `--mapping mapping.json`；不要悄悄跳过必要关节。
5. 如需参考融合，先记录原配布/作者、文件校验值、使用条件和骨骼要求；检查源动作正确播放，采样参考并选择对应动作阶段，再混合。查看退出码和报告，检查帧数、插补数量、不可达脚位计数、实际保存路径。比较基础与融合版本的起势、发力、收势和脚位；只有渲染或查看过才声称视觉验证。缺少真实模型/视频时说明测试范围。
6. 交付动作文件和报告，说明局限及哪些依赖已就绪。如果用户要求 VMD，追加 `--vmd NEW_OUTPUT.vmd`，检查实际文件和导出报告，失败时仍交付成功保存的 `.blend`，不要将失败描述为成功。

## 验证与故障

无需视频的端到端检查：`BLENDER --background --factory-startup --python-exit-code 1 --python SKILL/scripts/tools/bake_motion.py -- --demo --output NEW_DEMO.blend`。

已有验证记录见 [验证报告](references/VALIDATION.md)。参考测试位于 `scripts/tests/`。重复运行使用新的输出路径；不覆盖输入文件、用户现有动作或原始模型。输出文件中的原始网格被隐藏，副本网格绑定新骨架；物理、复杂约束及形态键动画不在本版保真范围。
