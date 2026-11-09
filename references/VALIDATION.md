# 验证记录 · 2026-11-09

## v0.2.1 仓库发布复查

- Python 3.12.14：现有 16 项核心与参考混合测试全部通过；所有 11 个 Python 文件通过语法编译检查。
- 本次没有修改动作算法。未重新运行 Blender、MediaPipe 视频推理、真实模型/VMD 往返或视觉审片；下方集成验证来自 v0.1/v0.2 的历史记录。
- 已统一运行文档中的仓库路径，增加 GitHub Actions 自动检查配置。云端 CI 是否通过以具体提交的 Actions 结果为准。
- 保留历史日志于 `scripts/tests/`。`video_pipeline.log` 中的本机输出路径已替换为 `<local-workspace>`，其余测试内容保留。
- 历史记录中的 `tests/` 在本仓库对应 `scripts/tests/`；`examples/` 下生成的模型和动作未随仓库发布，可使用文档命令自行生成。第三方动作、模型、视频和依赖二进制均未打包。

## v0.2 增量

新增 `test_reference.py` 的 7 项测试全部通过：零权重保持基础动作、手臂掩码保留腿和锚点、骨段长度保留、选段与端点渐变、不同帧数的时间相位对应、反向骨段拒绝、非法范围/参数拒绝。证据：`tests/reference_tests.log`。

新增 Blender 参考链路验证见 `tests/blender_reference.log`；测试涵盖已求值骨架采样、单位缩放、髋中点去位移、朝向旋转、约束结果采样，以及采样 → 混合 → 再烘焙。这里使用合成动作，不是 CMU/VMD/Mixamo 文件。

Blender 4.2.0 实测通过：采样 72 帧（24fps）、混合输出 90 帧（30fps）、重新烘焙生成 36 条四元数动画曲线。另实际执行了三个命令入口并保存 `examples/sampled_reference.json`、`examples/mixed_pose.json`、`examples/mixed_demo.blend` 和 `.report.json`。报告带有输入 JSON 的 SHA256、范围、权重与部位。该演示用于复现通路，不作为风格改善的证据。

本次更新已核查 VPVP、BowlRoll 具体条目及 CMU 动作目录；奈西读取失败，Mixamo 未登录。来源状态见 `references/motion-libraries.md`。没有捆绑、下载或实际混合第三方动作库资产，没有据此声称效果提升。

下方 v0.1 中“参考动作卡融合未实现”指原始版本；v0.2 现已支持标准姿态数据的选段四肢混合，但原始 VMD/FBX/BVH 仍需导入，自动招式语义匹配仍未实现。

## v0.1 实际执行结果

| 验证 | 结果 | 证据 |
|---|---|---|
| Python 数据处理测试 | 9/9 通过 | `tests/core_tests.log` |
| Blender 4.2.0 后台集成 | 通过 | `tests/blender_smoke.log` |
| 命令入口生成演示文件 | 成功保存 | `examples/demo_motion.blend`、`examples/demo_motion.report.json` |
| MediaPipe 模型视频接口 | 30 帧识别完成，缺失帧 0，插补点 0 | `tests/video_pipeline.log` |

Python 环境：Windows AMD64、Python 3.12。模型接口实测使用 MediaPipe 0.10.35、OpenCV 4.14.0、Google 官方 Pose Landmarker Full float16 v1 模型。

Blender 集成测试覆盖：插件注册/注销/重新注册；默认参数 65%/开/关；复制骨架与新 Action；原骨架约束保留、副本约束移除；90 帧合成站立动作；双脚累计接触帧 180、不可达脚位 0；静止脚位最大漂移 0 Blender 单位；前臂父空间旋转后方向点积 >0.9999；不可达脚位的有限夹紧；非法输入不新增场景对象；日文骨骼映射；循环 Cycles 修饰器。

数据测试覆盖：非法帧率、未知坐标系、非有限值、整关节缺失、长缺失拒绝、短缺失插值、平滑减少高频抖动、零平滑保持输入、静止接触判定。

视频验证输入为 [Google 官方测试静态图片](https://storage.googleapis.com/mediapipe-assets/pose.jpg) 重复编码成 30 帧 MJPEG AVI。实际经过 OpenCV 解码、MediaPipe VIDEO 推理、JSON 导出和核心校验。**这验证接口可运行，不验证真实运动捕捉准确率。** 测试素材与模型未打包。上游库输出了常见推理警告及一次失败的 Clearcut 连接日志，详见原始记录；程序本身没有云端素材上传步骤。

## 未验证或未实现

- 未提供用户真实参考视频、PMX 或既有动作卡，因此没有角色特定的视觉验收，也没有融合奥特曼现成动作/VMD。
- 没有声称进行渲染审片或动作自然度评测；当前验证为数值和实际 API 执行。
- mmd_tools 实际 PMX 导入、VMD 导出和回放未实测。日文命名兼容测试不等于真实模型兼容认证。
- Blender 4.4+ 的分层 Action 适配代码未实测；已验证版本为 4.2.0。
- 脚锁不等于真实鞋底接地；静态样例零漂移不代表走路、翻滚或遮挡场景零漂移。
- 原始动作文件的直接融合、自动招式风格迁移、根部移动、完整扭转、手指/表情未实现；v0.2 支持标准姿态 JSON 的选段和四肢方向混合。

## 环境说明

为本次测试临时下载了官方便携 Blender，运行完后已删除，以释放磁盘空间。早期依赖安装曾因磁盘不足失败；清理本任务的临时环境后，使用单一 OpenCV 包重新安装并成功完成视频测试。插件 ZIP、Skill ZIP 均不捆绑 Blender、姿态模型或 Python 二进制依赖。

历史 v0.1/v0.2 交付的复现命令及路径已在本仓库运行说明中更新；当时的安装包交付并不代表仓库已在读者机器上安装。

历史打包检查：官方 quick_validate.py 返回 Skill is valid；所有 Python 源文件通过语法编译检查，原交付的三个 ZIP 均通过 CRC 检查。本仓库不包含当时的 ZIP 或 SHA256SUMS.txt；这些历史结果不代表后续提交的验证结果。
