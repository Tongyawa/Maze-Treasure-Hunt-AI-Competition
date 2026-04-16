<h1 align="center">全国青少年信息素养大赛 - 迷宫寻宝AI竞技赛（高中组）</h1>

<h3 align="center">National Youth Information Literacy Competition<br>Maze Treasure Hunt AI Competition</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Award-National_2nd_Prize-FFD700?style=for-the-badge&logo=ribbon" alt="National 2nd Prize">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Status-Archived-success?style=for-the-badge" alt="Archived">
</p>

<p align="center">
  <b>🏆 本项目为本人于 2024 年 5-8 月参加该项赛事并斩获“全国二等奖”的代码归档。</b>
</p>

<br>
## 📌 赛事概览
- **大赛平台：**[腾讯 AI 竞技场 (ceickpcb2024)](https://ai-arena.qq.com/ceickpcb2024/)
- **赛事信息：** [官方赛事页面](https://ceic.kpcb.org.cn/comp/enrollMatch/58)
- **核心文件：** 本仓库为最终参赛时的完整代码目录，包含历史版本、测试代码及废稿等。**最终比赛主干程序为[`v2.3(优化Exit).py`](./v2.3(优化Exit).py)**。

---

## 💡 核心算法与技术亮点 (v2.3)

本项目没有使用简单的“就近贪心算法”，而是从**全局多步预测、动态博弈规划、异常状态机处理**三个维度构建了一个高鲁棒性的决策系统。主要包含以下五大核心模块：

### 1. 基于递归与多步评估的动态权重决策 (`permutation` & 收益期望模型)
为了最大化最终得分（不仅是单颗宝石分数，还包括凑齐一套的 `GEM_SET` 100分大奖），AI 在决策时会向后看多步：
- **全局期望计算**：通过统计当前剩余体力 (`me.energy`)、平均步数消耗 (`MEAN_COST`) 以及当前回合数，动态预测出**“余下期望可捡宝石数”**。
- **最优凑套策略**：计算 `gem_optimal_quantity`，根据当前背包里最少宝石的数量、余下期望可捡宝石数，推导当前最迫切需要哪种宝石（短期视角，防被“老登”超过）以及全局情况下可以大致再凑出多少套宝石（长期视角，稳稳拿到最高分数）等。利用次幂权重公式（`GEM_MI` 常量）将“凑套额外收益”分摊到具体的候选物品上。
- **多层排列组合寻路**：放弃短视的“找最近”，利用深度递归算法对场上剩余物品进行排列组合模拟，计算出每条行动路线的综合性价比（`tot_weight + item_value[i] / tot_pathlen`），从而选定最优长期目标。

### 2. “预知未来”的物品寿命时空预测 (`traverse` & `itemspan` 系统)
在零和博弈的赛场上，经常会出现“我快跑到宝石面前了，却被对手抢先吃掉，白白浪费体力”的情况。为此设计了独创的**物品寿命预测系统**：
- 代码通过 `traverse` 函数，利用 BFS（广度优先搜索）预先模拟对手的寻路逻辑和移动轨迹。
- 动态赋予场上每一个物品一个“寿命值” (`itemspan`)。
- **智能剪枝**：如果经过距离测算，发现某个物品在我方抵达前必定会被对手（`rival`）截胡，算法会在遍历时直接剪枝（剔除该目标），彻底杜绝“无效折返跑”。

### 3. 高阶防堵策略——动态虚拟障碍生成 (`calc_extra_obstacles`)
针对赛场上恶心人的“老登”战术（凭借初期短视贪心拿宝石而获得的微弱分数优势，利用狭窄地形死堵对手使得对手无法获取宝石，直到对局结束），构建了极具侵略性的反制系统：
- 算法时刻比对双方位置与目标。一旦判定遭到恶意阻挡（`is_blocked_maliciously` 被触发），立即启动紧急防登预案。
- **封锁区计算**：向对手的上下左右4个方向进行射线遍历，将所有“对手能比己方先到达的空地”全部拉黑，动态加入 `extra_obstacles_list`（额外障碍列表）中。
- AI 在寻路时会将这些“潜在封锁区”视作实体墙壁，从而提前规划大迂回路线，让“老登”扑空。

### 4. 状态机死锁检测与“孔雀东南飞”特判 (`pacing_check` & `stuck_check`)
在与“老登”博弈的复杂情况中，有时代码会陷入逻辑死循环从而操纵角色在两格间反复左右横跳。为了避免这种情况持续过久，特此设计了多重状态监测：
- **“孔雀东南飞”检测**：利用队列 (`pre_pos_list` 和 `pre_dst_list`) 记录最近的坐标和目标。如果发现自身坐标出现 `ABABABAB` 的原地反复横跳，或目标物品疯狂切换，立即强制打破循环。
- **长时停滞检测**：引入 `itemless_rounds`（未获取物品回合数）计时器。若长达 30 回合颗粒无收，判定为被神级“老登”死死卡住，立即触发随机目标重置；若超过 300 回合，甚至会启动“被堵死”特判，自动放弃发育直接冲向出口保底。
- **物理贴脸卡死防范**：`stuck_check` 检测到原地踏步时，直接将对手当前坐标强制设为不可穿透的障碍物，促使 BFS 重新规划绕路轨迹。

### 5. 毫秒级安全边际计算的极限逃生 (`should_leave`)
- **严格的安全冗余**：每回合实时进行当前位置到出口 (`context.exit`) 的 BFS 最短路径重算。
- 触发条件极其精准：当 `当前体力 <= 回家所需步数 + 5` 且刚捡完重要道具时，或者 `当前体力 <= 回家所需步数 + 4` 达到物理极限时，立刻将目标强制锁定为出口（`is_leaving = True`），且屏蔽一切其他干扰项。确保哪怕体力仅剩最后 1 点，也能精准跃入出口结算加分。

### 6. 泛化引力场兜底机制 (`update` 最终校验)
当常规的最优目标由于地形突变或对手卡位导致突然“无路可走”时，算法不会崩溃，而是采用**距离平方反比加权**（`score / pathlen**2`）：
计算周围上下左右4个格子的“泛化期望收益权重” (`drc_weight`)。就像引力场一样，场上所有物品会对这4个方向产生引力，AI 会自动顺着总体引力最大的方向迈出安全的一步，完成完美的异常兜底。

---

## 📁 目录结构与其他说明

- 📂 **主程序及历史版本：** 根目录包含了从初期到最终成型的一系列版本（主推 `v2.3(优化Exit).py`）。
  - 📂 **`Auto_Test` 文件夹：** 自动化测试套件。用于在比赛网页端自动循环运行代码与对手比拼，并自动统计胜率。这是我在比赛期间验证每一次算法微调（如调整权重、优化寻路）是否产生正向收益的核心测试工具。
  - 📂 **`Elo机制` 文件夹：** 积分推演工具。由于大赛采用 Elo 评级机制，该文件夹内的脚本用于计算在不同分差情况下，对战输/赢/平时的隐藏分变化预期。

---

## 🎮 实机演示

以下为代码在比赛平台上的实际运行录像：

**1. 自动化循环测试运行 (Auto Test 演示)**

https://github.com/user-attachments/assets/959ff495-809c-4e47-a6b0-75d019a3c51c

**2. 正常对局获胜演示**

https://github.com/user-attachments/assets/db26a81a-a6fa-4a37-a29e-0c5703a30fe1

**3. 智斗“老登”反制获胜演示**

https://github.com/user-attachments/assets/09ee775f-fd30-4595-89f9-59b92b1a8309

---

## 📅 文件时间记录

证明本项目开发周期的历史截图存档：

- <img width="400" alt="image" src="https://github.com/user-attachments/assets/978f154d-a145-43d9-b77a-835f13f6160e"/>
- <img width="400" alt="image" src="https://github.com/user-attachments/assets/517ddcfa-b3fb-41b0-936d-b6408ea45394"/>
- <img width="400" alt="image" src="https://github.com/user-attachments/assets/0257f3b4-5562-49a6-90dc-65175f46f30d"/>
- <img width="400" alt="image" src="https://github.com/user-attachments/assets/e440ba98-9c10-40a7-8cb1-5ff7abeb38f2"/>

## 创作声明

参赛代码仅使用代码自动补全，未使用Vibe Coding；纯原创，于高中学校课余时间在草稿纸上完成初期算法建模。

<br>

---
<div align="center">
  <i>Coding with ❤️passion in Summer 2024.</i>
</div>
