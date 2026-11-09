# Ultra Motion Skill

将单人参考视频、标准姿态 JSON 或已经导入 Blender 的参考动作，转换为 Blender/MMD 身体动作的本地工具与 Codex Skill。

当前 Skill 版本为 **0.2.1**。随附的可选 Blender 面板模块仍为 **0.1.0**；本次更新整理发布与维护方式，不更改动作算法。

## 能做什么

- 视频 → 本地 MediaPipe 姿态提取 → 标准 JSON → 骨架副本与动作。
- 对已导入 Blender 的动作采样，按片段和手臂/腿部混合参考方向。
- 默认平滑 65%、脚位接触锁定开启、循环关闭。
- 输出新的 `.blend` 与诊断报告；安装 mmd_tools 后可尝试导出 VMD。

适用输入是单人、全身可见、近正面、固定机位的视频，以及已导入 Blender 的可匹配骨架。当前不恢复根位移、完整躯干扭转、手指或表情；脚锁是启发式约束。VMD 和真实角色兼容性需另行验收。完整能力边界见 [SKILL.md](SKILL.md)。

## 安装为 Skill

下载本仓库源码，将文件夹命名为 `ultra-motion`，放入个人 skills 目录（通常为 `~/.codex/skills/`，设置了 `CODEX_HOME` 时为其下的 `skills/`）。确认最终路径为 `skills/ultra-motion/SKILL.md`，重新加载技能后可使用：

> 使用 $ultra-motion，把这个全身参考视频转为这个 Blender/MMD 角色的动作，平滑 65%，脚底锁定开启，不循环。

也可以直接使用仓库内的命令行工具。Skill 本身不包含 Blender、Python、MediaPipe 模型或第三方角色/动作文件。

## 快速验证

在仓库根目录执行。将 `blender` 替换为本机 Blender 可执行文件路径：

```powershell
python -m unittest discover -s scripts/tests -p "test_*.py" -v
blender --background --factory-startup --python-exit-code 1 --python scripts/tools/bake_motion.py -- --demo --output work/demo_new.blend
```

第一条运行 16 项不依赖 Blender 的数据处理测试；第二条生成合成动作示例，验证本机 Blender 流程，不代表真实视频动捕质量。输出路径必须尚不存在。

视频推理需要独立 Python 3.12 环境，安装 `scripts/tools/requirements.txt` 并下载官方模型；不要把这些依赖装入 Blender 自带 Python。安装、命令、骨骼映射和 JSON 规范见 [运行说明](references/README.md)。

## 文件导航

| 位置 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | Codex 的执行入口与能力边界 |
| [运行说明](references/README.md) | 依赖、视频转动作、骨骼映射与 JSON 规范 |
| [参考动作流程](references/reference-workflow.md) | 采样、选段与部位混合 |
| [动作来源导航](references/motion-libraries.md) | 候选库和来源记录；不是捆绑资产 |
| [验证记录](references/VALIDATION.md) | 当前与历史测试范围及未验证事项 |
| `scripts/tools/` | 提取视频、采样、混合与烘焙入口 |
| `scripts/ultra_motion_studio/` | 数据处理、骨架处理及可选面板模块 |
| `scripts/tests/` | 16 项 Python 测试、Blender 集成测试与历史日志 |

## 更新与维护

每次推送和拉取请求会触发 GitHub Actions，运行 Python 3.12/3.13 的语法检查及现有数据测试。CI 不下载模型、不处理用户素材，也不替代 Blender 和真实角色的人工验收。

修改数据算法后运行上述 Python 测试；修改 Blender 骨架逻辑时追加：

```powershell
blender --background --factory-startup --python-exit-code 1 --python scripts/tests/blender_smoke.py
blender --background --factory-startup --python-exit-code 1 --python scripts/tests/blender_reference.py
```

这两项集成测试按 Blender 4.2 编写；更高版本需要实际运行确认。发布时更新 [CHANGELOG.md](CHANGELOG.md) 和验证记录，区分数值测试、合成动作测试与真实素材审片。提交问题时提供版本、复现命令和必要日志，素材和模型只在取得许可后分享。

## 许可

沿用项目已有 [MIT License](LICENSE)。Blender、mmd_tools、MediaPipe、模型及第三方动作/角色各自适用原许可证；仓库不捆绑这些外部资产。
