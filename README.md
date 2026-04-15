苯人于2024年8月参加的全国青少年信息素养大赛-迷宫寻宝AI竞技赛获全国二等奖的代码，现作归档。
此为最终参加比赛时的code folder，含历史版本、测试代码、废稿等杂项，代码main文件为“v2.3(优化Exit).py”
大赛平台：https://ai-arena.qq.com/ceickpcb2024/
赛事信息：https://ceic.kpcb.org.cn/comp/enrollMatch/58

---
## 算法主要思路：（贪心算法、有限步长内的全局最优搜索）
### 1. 核心决策模型：多目标动态权重估值
算法并非简单地寻找最近物品，而是通过 **`permutation`（排列组合递归）** 函数对多种可能的抓取路径进行深度搜索和评估：
*   **收益最大化：** 算法考虑了宝石的**成套收益（Set Bonus）**。利用 `GEM_MI`（幂次参数）和 `GEM_SET`（成套得分）计算期望收益，优先补齐短板宝石。
*   **动态期望：** 引入了 `expected_remaining_gems_count`。算法会根据当前剩余体力、平均步频和比赛进度，动态预估还能获取多少宝石，从而调整当前目标的权重。
*   **效率优先：** 评价指标为 `item_value / pathlen`（单位步数价值），确保在有限体力下实现收益效率最大化。

### 2. 博弈与对手建模 (Adversarial Modeling)
算法具有强烈的“对抗意识”，通过对对手行为的预测来规避风险：
*   **物品寿命预估 (`itemspan`)：** 通过 `traverse` 递归函数计算每个物品的“安全生存时间”。如果预测对手会比我方先到达某个物品，算法会将其从目标列表中剔除或降低权重。
*   **动态障碍物 (`calc_extra_obstacles`)：** 当检测到对手可能进行恶意阻挡时，算法会将对手周边的关键路径点虚拟化为“墙（WALL）”，迫使路径规划绕开对手，防止被卡死。

### 3. 鲁棒性与行为修正 (Anti-Stuck & Robustness)
针对迷宫赛中常见的“对峙”和“死循环”问题，代码设计了专门的监控机制：
*   **“孔雀东南飞”特判 (`pacing_check`)：** 这是一个有趣的行为检测逻辑。如果算法检测到我方在两个坐标点之间反复横跳（ABAB模式），或者连续多轮没有物品入账，会判定为进入了死循环，强制切换目标以打破僵局。
*   **恶意阻挡应对：** 当 `itemless_rounds`（未获取物品回合数）过高时，启动应急预案，随机更换目标并重新计算带有额外障碍物的地图路径。

### 4. 资源规划与风险控制 (Energy Management)
*   **精准离场机制 (`should_leave`)：** 算法实时计算当前位置到出口的最短路径长度 `pathlen`。考虑到比赛末期的不确定性，设置了“安全冗余量”（pathlen + 5），确保在体力耗尽前能够稳妥回巢，避免“见好不收”导致的分数清零。
*   **泛化方向选择：** 在确定最终目标（dst）后，算法不仅看最短路径，还会计算上下左右四个方向的**泛化期望权重 (`drc_weight`)**，选择一个既能靠近目标，又能兼顾途中顺手牵羊的方向。
---
## 其他说明
- Auto_Test文件夹用于在比赛网页端自动循环测试运行代码与对手比拼，并自动统计胜率，用于确定每一次代码优化是否有效；
- Elo机制文件夹用于计算在不同情况下与不同分数玩家对战输/赢/平时的分数变化（由于大赛采取Elo机制）
- 称恶意堵塞对手道路的为“老登”，由于此战术十分恶心可以以低设计反克复杂宝石收益权重算法，故代码中为此专门设计了“防登”部分，额外写了遇到神级“老登”实在没法应对的应急版本代码，以及统计了遇到的“老登”ID用于赛前测试
---
## 实机演示
1. 自动测试：
   
https://github.com/user-attachments/assets/959ff495-809c-4e47-a6b0-75d019a3c51c


2. 正常对局获胜：

https://github.com/user-attachments/assets/db26a81a-a6fa-4a37-a29e-0c5703a30fe1


3. “老登”对局获胜：

https://github.com/user-attachments/assets/09ee775f-fd30-4595-89f9-59b92b1a8309


---
## 文件时间记录
- <img width="1062" height="1152" alt="image" src="https://github.com/user-attachments/assets/978f154d-a145-43d9-b77a-835f13f6160e" />
- <img width="1059" height="228" alt="image" src="https://github.com/user-attachments/assets/517ddcfa-b3fb-41b0-936d-b6408ea45394" />
- <img width="1056" height="237" alt="image" src="https://github.com/user-attachments/assets/0257f3b4-5562-49a6-90dc-65175f46f30d" />
- <img width="1053" height="609" alt="image" src="https://github.com/user-attachments/assets/e440ba98-9c10-40a7-8cb1-5ff7abeb38f2" />



