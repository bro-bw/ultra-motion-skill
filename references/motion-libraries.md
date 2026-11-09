# 参考动作库与选材 · 2026-11-09 核查

本表是资源导航与候选清单，不包含任何已下载的第三方动作。候选有明确不同的状态：条目已核查、下载未验证、文件已验、已导入、已融合、已审片。只有做到对应步骤才更新状态。

## 来源路线

| 来源 | 用途与格式 | 当前核查结果 / 注意事项 |
|---|---|---|
| [奈西 MMD](https://naiximmd.com/) | 用户提供的 MMD 资源入口 | 本次首页读取超时、搜索未得到可核查条目。保留入口，但不编造具体资源、格式或使用许可。找到文章后追溯作者原配布与 readme。 |
| [VPVP 武道/运动动作](https://w.atwiki.jp/vpvpwiki/pages/236.html) | MMD 动作索引；页面收录 VMD 及 MMD/PMM 工程 | 已读取。它是索引，不是统一授权库；逐项跟进配布页。部分条目已经停止配布。 |
| [CMU](https://mocap.cs.cmu.edu/) | 实测人体动捕；原始 ASF 骨架 + AMC 动作等 | 已核查索引与说明。不要把 AMC 单独当作 BVH；ASF/AMC 本工具不直接解析。 |
| [CMU 格式资源](https://mocap.cs.cmu.edu/resources.php) | 第三方转换的 BVH 等格式路线 | 页面列出 cgspeed 的 MotionBuilder/3dsMax BVH 转换，并明确外链文件未由 CMU 自行测试；部分其他转换已不可用。检查单位、轴向及版本。 |
| [Adobe Mixamo](https://www.mixamo.com/) | 通用双足角色动作候选，通常走导出的 FBX → Blender 路线 | 网站是动态应用，本次没有登录或下载具体动作。[官方 FAQ](https://helpx.adobe.com/ie/creative-cloud/faq/mixamo-faq.html)说明需 Adobe ID，列有账号/地区限制；不要假设用户一定能访问。 |
| [mmd_tools](https://extensions.blender.org/add-ons/mmd-tools/) / [官方源码](https://github.com/MMD-Blender/blender_mmd_tools) | PMX/PMD、VMD/VPD 格式桥接 | 工具而非动作库。导入动作时先保留源骨架约束/IK，取得最终求值姿态后再采样。 |

## 已核查的候选，而非已融合资产

| 候选 | 来源 | 建议用途（制作判断） | 状态 / 要求 |
|---|---|---|---|
| MMD 格斗动作配布 1–5，サブミッションP | [VPVP](https://w.atwiki.jp/vpvpwiki/pages/236.html) → [配布目录](https://ux.getuploader.com/supe41/) | 格斗起势、攻防过渡 | 索引已核查，配布目录本次 403。索引明确要求“全ての親”和腕 IK；未下载。 |
| 八極拳 モーション詰め合わせ，hino | [BowlRoll 条目 7234](https://bowlroll.net/file/7234) | 发力、肘击、腿法的姿势参考 | 文件详情页可读取，显示 ZIP；未取得包、未审阅 readme、未核查内含格式。 |
| CMU 02_05 | [CMU 全部动作目录](https://mocap.cs.cmu.edu/search.php) | 出拳/打击片段参考 | 原描述为 punch/strike；索引核查，未下载。 |
| CMU 12_04 | 同上 | 缓慢蓄势和重心变化参考 | 原描述为 tai chi；索引核查，未下载。 |
| CMU 76_04 | 同上 | 防御站姿，作为起手式候选 | 原描述为 defensive guard pose；索引核查，未下载。 |
| CMU 77_10 | 同上 | 拳击姿势候选 | 原描述为 boxing；索引核查，未下载。 |
| CMU 86_01 | 同上 | 踢打和跳跃候选，需选段 | 原描述含跳、踢、拳；整段不直接混入起手式。 |

这些条目没有证据表明是奥特曼原版招式。要复刻某位奥特曼的起手式，视频仍是手臂角度、左右顺序、蓄力节奏和定格姿态的主依据；通用参考主要帮助姿态稳定和动作衔接。

## 检索和选择

优先级：同一目标招式的原配布动作 → 结构近似的 MMD 动作 → CMU/Mixamo 通用人体动作 → 单独视频推理。优先级不能代替预览判断。

检索词按动作拆开：`奥特曼 起手式 动作配布`、`ウルトラマン 構え モーション配布`、`格闘 構え 防御 パンチ キック`；英文可检索 `guard stance / fighting idle / punch / block / martial arts`。这些是建议搜索词，不是声称已存在的 Mixamo 动作名称。

比较：动作目的、出招侧、起终姿态、脚接触、时长、骨骼要求。先选择“起势 → 蓄力 → 出招 → 收势”的对应区间；原片和参考片的打击峰值最好落在接近的归一化位置。必要时分段处理，不能用简单整段拉伸冒充自动语义对齐。

## 来源记录

每个实际下载的文件记录以下字段到输出旁的 `references.json`：

```json
{
  "asset_id": "cmu-76-04",
  "title": "defensive guard pose",
  "author_or_provider": "CMU Graphics Lab",
  "landing_url": "https://mocap.cs.cmu.edu/search.php",
  "download_url": null,
  "local_file": null,
  "sha256": null,
  "format": null,
  "terms_url_or_readme": "https://mocap.cs.cmu.edu/",
  "terms_checked": false,
  "required_bones": [],
  "status": "catalog_verified",
  "used_range": null,
  "contribution": null
}
```

首次下载后补全真实文件信息。混合工具另记录两个输入 JSON 的 SHA256、片段范围、部位及权重；原始下载文件的来源记录仍需保留。

## 使用条件

CMU 首页允许用于作品/项目并列出不得单独转售数据（包括转换形式）的限制，且要求不要爬取整个数据库；少量按需定位，不镜像动作库。记录 CMU 来源和资助致谢信息，发布时再次核查条款。

MMD 动作以具体作者/readme 条件为准，包括署名、改造、商业用途和再配布。Mixamo 按当前 Adobe 条款及账号实际可用性使用；FAQ 的项目使用说明不能直接视为允许重新打包原始动作库。Skill ZIP 不附带第三方动作。若配布需要登录、口令或购买，保留候选并使用用户已有文件或其他公开候选，不猜口令或绕过访问限制。
