import api
import copy
import random

# 可调常量
GEM_SET = 100  # 成套宝石得分
IS_BOX_ENERGY = 0  # 若开宝箱拿体力则为1，拿分数为0（后续用于mean_gem2的计算）
box_values = [-10, 30]
BOX_MULTIPLE = 1
BOX_VALUE_MEAN = BOX_MULTIPLE * sum(box_values) / len(box_values)
TOTAL_ENERGY = 1000  # 总体力值
MEAN_COST = 4.5  # 平均每个物品获取所需步数
# MEAN_GEM = TOTAL_ENERGY/MEAN_COST/5  # 平均每种宝石的期望获取量（常量，后续通过计算mean_gem2来实时调整）
MAZE_SIZE = 15

# 固定常量
DRC = [[-1, 0], [1, 0], [0, -1], [0, 1]]    # (row, col) 4个方向依次对应上下左右
DRC_STR = "UDLR"


# 全局变量
pre_pos = None
pre_item_count = None
last_dst = None
is_leaving = False
is_stuck = False
is_pacing = False
itemlist = []
itemlen = 0  # 存储itemlist长度
itemgragh = []
itemspan = {}  # 存储物品“寿命”
item_weight = {}  # 存储物品权重


# 定义一个函数，判断是否需要立即离场
def should_leave(context):
    global is_leaving, pre_item_count
    pathlen = len(api.check.path(
        context.me, context.exit, method="bfs", player_id=stuck_check(context))) - 1
    # 若当前体力小于等于离场最小体力加5，并且刚获取到某一物品(item_count有变化)，则见好就收，开始离场，以防被阴
    if context.me.energy <= pathlen + 1 + 5 and pre_item_count != context.me.item_count:
        is_leaving = True
    # 若当前体力小于等于离场最小体力+6，则强制离场
    if context.me.energy <= pathlen + 1 + 6:
        is_leaving = True
    return is_leaving


# 孔雀东南飞特判
pre_dst_list = []
pre_pos_list = []
head = tail = 0  
itemless_rounds = 0  # 未获取物品回合数
is_blocked_maliciously = False


def pacing_check(context):
    global is_pacing, pre_dst_list, pre_pos_list, head, tail, itemless_rounds, last_dst, is_blocked_maliciously
    if tail >= 4:
        # 第一重特判: 若连续4回合的 目标物品（ABAB） 或 我方位置（ABABABAB） 在反复横跳，则判定为孔雀东南飞
        if pre_dst_list[head] == pre_dst_list[head+2] and pre_dst_list[head+1] == pre_dst_list[head+3] and pre_dst_list[head] != pre_dst_list[head+1]:
            is_pacing = True
        if pre_pos_list[head-4] == pre_pos_list[head-2] == pre_pos_list[head] == pre_pos_list[head+2] and pre_pos_list[head+-3] == pre_pos_list[head-1] == pre_pos_list[head+1] == pre_pos_list[head+3] and pre_pos_list[head] != pre_pos_list[head+1]:
            is_pacing = True
    if context.me.item_count != pre_item_count:  # 若刚获取到物品，则重置未获取物品回合数、消除孔雀东南飞状态、重置恶意阻挡状态
        itemless_rounds = 0
        is_pacing = False
        is_blocked_maliciously = False
    else:
        itemless_rounds += 1
    '''废稿
    # 第二重特判: 若连续20回合以上没获取到物品，则判定为孔雀东南飞，且每隔20回合切换目标为目标记录队列中最近一个与当前目标不同的目标；
    if itemless_rounds >= 20 and itemless_rounds % 20 == 0:
        is_pacing = True
        # 随机选择
        item = random.choice(itemlist)
        while item == last_dst:  # 防止与当前相同
            item = random.choice(itemlist)
        last_dst = item
    '''
    # 第二重特判：若连续30回合以上没获取到物品，则判定为恶意阻挡，启动应急备案
    if itemless_rounds >= 30:
        is_pacing = True
        is_blocked_maliciously = True
        if (itemless_rounds - 30) % 20 == 0:  # 第1次触发恶意阻挡时 以及 后续每20回合 随机更换一次目标
            # 随机选择
            item = random.choice(itemlist)
            while item == last_dst:  # 防止与当前相同
                item = random.choice(itemlist)
            last_dst = item
        print("------------------")
        print("警告！遭到恶意阻挡！")
        print("含额外障碍的地图：")
        maze = context.maze
        obstacles_list = calc_extra_obstacles(context)
        for row in range(len(maze)):
            for col in range(len(maze[row])):
                if maze[row][col] == 'WALL':
                    print('#', end='')
                elif [row, col] in obstacles_list:
                    print('S', end='')
                else:
                    print(' ', end='')
            print()
        print("------------------")
    print("孔雀东南飞状态：", is_pacing)
    print("pre_dst_list(最近几个目标): ", pre_dst_list[head:tail])
    print("pre_pos_list(最近几个我方位置): ", pre_pos_list[head:tail])
    print("itemless_rounds: ", itemless_rounds)

    if is_leaving:
        is_pacing = False
    return is_pacing


def calc_extra_obstacles(context):
    global is_blocked_maliciously
    if is_leaving:
        return []
    obstacles_list = []
    me = context.me
    rival = context.players[1]
    maze = context.maze
    # 若被恶意阻挡则将对手所在行、列中能比己方先到达的格子都视为障碍
    if is_blocked_maliciously:
        # obstacles_list.append([rival.row, rival.col])

        # 向上下左右4个方向遍历，各自直到碰到墙或者当前自己的位置为止
        for i in range(4):
            new_row = rival.row + DRC[i][0]
            new_col = rival.col + DRC[i][1]
            while 0 <= new_row < MAZE_SIZE and 0 <= new_col < MAZE_SIZE and maze[new_row][new_col] != 'WALL' and not (new_row == me.row and new_col == me.col):
                # 若对手能比己方先到
                if api.check.who_is_closer(new_row, new_col, players=None) == rival:
                    obstacles_list.append([new_row, new_col])
                new_row += DRC[i][0]
                new_col += DRC[i][1]
        '''废稿
        # 遍历整个迷宫地图，将 不是墙 并且 对手能比己方先到达 的格子全部置为额外障碍
        for row in range(len(maze)):
            for col in range(len(maze[row])):
                if maze[row][col] != 'WALL' and api.check.who_is_closer(row, col, players=None) == rival:
                    obstacles_list.append([row, col])
        '''

    return obstacles_list


# 判断是否被卡住
def stuck_check(context):
    global is_stuck, pre_pos, pre_item_count
    if is_leaving:
        return -1
    if pre_pos == (context.me.row, context.me.col):
        is_stuck = True
    elif context.me.item_count != pre_item_count:  # 若刚捡到宝石，则取消卡住状态
        is_stuck = False
    if is_stuck:  # 若被卡住则将对手视为不可穿透
        return 0
    else:  # 若未被卡住，则将对手视为可穿透
        return -1

# 遍历，处理itemspan


def traverse(context, current_index, traverse_list):
    global itemspan
    rival = context.players[1]
    # print("\ntraverse函数调用------------")
    if traverse_list == []:
        # print("current_index:", current_index, "列表为空，返回")
        return
    # print("current_itemkind:", itemlist[current_index].name, "current_index:", current_index, "traverse_list:", traverse_list)
    min_pathlen = 99999

    min_pathlen = 99999
    min_cnt = 99999
    # 寻找离对手最近且对手持有最少的物品并计算距离
    for i in traverse_list:
        pathlen = itemgragh[current_index][i]
        tmp_cnt = rival.item_count[itemlist[i].name]
        if pathlen > 0 and pathlen < min_pathlen:  # 若当前物品离对手更近，则更新最短路径和最小计数
            min_pathlen = pathlen
            min_cnt = tmp_cnt
        elif pathlen == min_pathlen:  # 若当前物品离对手一样近，则视情况更新最小计数
            if tmp_cnt < min_cnt:
                min_cnt = tmp_cnt
    # print("min_pathlen:", min_pathlen)
    # 在还没遍历过的物品中，找出所有离当前物品最近的物品作为下一层遍历的起点，组成列表
    next_index_list = [
        i for i in traverse_list if itemgragh[current_index][i] == min_pathlen and rival.item_count[itemlist[i].name] == min_cnt]
    # print("itemspan:", itemspan)
    for i in next_index_list:
        # 设置itemspan（第n层遍历，置为原先的span 和 前一层的span+当前物品到下一物品的距离 当中较小的值）
        if i in itemspan:  # 若i已在itemspan中，则取较小值
            # print(i, "已在itemspan中")
            itemspan[i] = min(
                itemspan[i], itemspan[current_index] + min_pathlen)
        else:
            # print(i, "未在itemspan中")
            itemspan[i] = itemspan[current_index] + min_pathlen

        # 创建traverse_list的新副本进行递归调用
        new_traverse_list = copy.deepcopy(traverse_list)
        # print("下一个遍历对象:", i, "号 ", itemlist[i].name)
        # print("Before remove:", new_traverse_list)
        new_traverse_list.remove(i)
        # print("After remove:", new_traverse_list)
        traverse(context, i, new_traverse_list)


def permutation(context, initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight):
    global item_weight
    # print("-----------------------")
    # print("permutation函数调用")
    # print("initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight:")
    # #print(initial_index, current_index, next_index_list,
    #       item_count, tot_pathlen, tot_weight)
    # #边界处理#
    '''原稿
    leave_pathlen = len(api.check.path(
        itemlist[current_index], context.exit, method="bfs", player_id=stuck_check(context))) - 1
    '''
    leave_pathlen = len(api.check.path(
        itemlist[current_index], context.exit, method="bfs", player_id=stuck_check(context))) - 1
    actual_energy = context.me.energy - tot_pathlen - leave_pathlen
    if next_index_list == [] or actual_energy < 1:  # 若已遍历完场上所有物品 或 当前实际动态体力小于1（即无法抵达终点），则结束遍历
        return
    # 未到边界则更新itemweight
    if initial_index in item_weight:  # 若item_weight中已有值，则取较大者保留
        item_weight[initial_index] = max(
            item_weight[initial_index], tot_weight)
    else:  # 否则新增
        item_weight[initial_index] = tot_weight
    # 物品权重计算预处理
    if context.round < TOTAL_ENERGY/10:  # 若刚开局，则姑且按余下可捡为 余下体力 / 普遍平均获取物品步数 来计算 余下期望可捡物品数（将tot_pathlen和离场所需体力纳入考虑）
        expected_remaining_gems_count = (
            context.me.energy - tot_pathlen) / MEAN_COST
    else:
        tot_item_count = sum(item_count.values())  # 当前已捡物品总数
        expected_remaining_gems_count = actual_energy * \
            tot_item_count / context.round  # 动态计算当前遍历层内余下期望可捡物品数（将tot_pathlen和离场所需体力纳入考虑）
    # print("expected_remaining_gems_count: ",
    #       expected_remaining_gems_count)

    sorted_item_count = sorted(
        item_count.values(), reverse=True)  # 将各物品数目取出并降序排序
    # print("sorted_item_count: ", sorted_item_count)
    # 求解各宝石最大收益数量
    gem_optimal_quantity = 0  # 即E(Cm)
    for i in range(5):
        cnt = 0
        for j in range(i+1, 5):
            cnt += sorted_item_count[i] - sorted_item_count[j]
        if cnt <= expected_remaining_gems_count:
            gem_optimal_quantity = (
                expected_remaining_gems_count - cnt) / (5 - i) + sorted_item_count[i]
            break
    # print("gem_optimal_quantity: ",
    #       gem_optimal_quantity)
    expected_remaining_gem_set_score = GEM_SET * \
        (gem_optimal_quantity - min(sorted_item_count))   # 求余下期望成套收益总和 即E(gem_set)
    # #完成物品权重第n层遍历#
    item_value = [0]*itemlen
    for i in next_index_list:  # 枚举下一个目标物品
        # #处理item_value#
        # print("排列组合下一个 i:", i)
        item_value[i] += itemlist[i].score
        # 如果当前目标是宝箱（废判）
        if False:
            1 == 1  # 不知道写什么，先随便放个东西凑数
        # 若当前目标是宝石
        else:
            # 将物品价值加上成套额外收益
            '''期望成套收益总和姑且先不放'''
            if item_count[itemlist[i].name] < gem_optimal_quantity:
                item_value[i] += GEM_SET * ((gem_optimal_quantity -
                                            item_count[itemlist[i].name]) / expected_remaining_gems_count)**2
            # print("物品名称itemlist[i].name: ", itemlist[i].name,
            #       "物品数量item_count[itemlist[i].name]: ", item_count[itemlist[i].name],
            #       "物品期望收益item_value[i]: ", item_value[i])

        # #第n层遍历#
        new_next_index_list = copy.deepcopy(next_index_list)
        new_next_index_list.remove(i)
        new_item_count = copy.deepcopy(item_count)
        new_item_count[itemlist[i].name] += 1
        # 若该物品在自己获取之前可能已被对手获取，则不将该物品计入item_count、tot_pathlen和tot_weight（但new_next_index_list需更新）
        if itemspan[i] < tot_pathlen + itemgragh[current_index][i]:
            permutation(context, initial_index, current_index, new_next_index_list,
                        item_count, tot_pathlen, tot_weight)
        # 否则记为获取
        else:
            permutation(context, initial_index, i, new_next_index_list, new_item_count, tot_pathlen +
                        itemgragh[current_index][i], tot_weight + item_value[i] / tot_pathlen**0.5)


def update(context):
    global pre_pos, pre_item_count, is_leaving, is_stuck, itemlist, itemlen, itemgragh, itemspan, item_weight, pre_dst_list, pre_pos_list, head, tail, last_dst
    me = context.me
    rival = context.players[1]
    print("-----------------")
    print("Round ", context.round)
    print("我的位置：", me.row, me.col)
    print("对手位置：", rival.row, rival.col)
    print("场上物品：", context.items)
    print("stuck_check(context): ", stuck_check(context))
    # 全局变量
    itemlist = []
    itemlen = 0  # 存储itemlist长度
    itemgragh = []
    itemspan = {}  # 存储物品“寿命”
    item_weight = {}  # 存储物品权重

    # #将地图上所有物品存入一个一维列表itemlist#
    for itemkind in context.items.values():
        for item in itemkind:
            itemlist.append(item)
    itemlen = len(itemlist)
    print("itemlist:")
    for i in itemlist:
        print(i)
    print("itemlen: ", itemlen)

    # #使用二维列表存储距离图#
    for i in range(itemlen):
        tmp = []
        # 遍历itemlist, 计算从当前物品到每一个物品的距离（注：Path方法计算出来的长度包括起点和终点，故-1；自己到自己的距离置为0-1=-1）
        for j in range(itemlen):
            tmp.append(len(api.check.path(
                itemlist[i], itemlist[j], method="bfs", player_id=-1)) - 1)
        itemgragh.append(tmp)
    print("itemgragh:")
    print("   ", end="")
    for i in range(len(itemgragh)):
        print(i, end="   ")
    print()
    for i in range(len(itemgragh)):
        print(i, end="  ")
        for j in range(len(itemgragh)):
            print(itemgragh[i][j], end="  ")
        print()

    # #完成itemspan的处理#
    # 对手体力为零时的体力优势特判
    if rival.energy == 0:
        for i in range(itemlen):
            itemspan[i] = 99999
    else:
        next_index_list = []
        min_pathlen = 99999
        min_cnt = 99999
        # 寻找离对手最近且对手持有最少的物品并计算距离
        for i in range(itemlen):
            pathlen = len(api.check.path(
                rival, itemlist[i], method="bfs", player_id=-1)) - 1
            tmp_cnt = rival.item_count[itemlist[i].name]
            if pathlen < min_pathlen:  # 若当前物品离对手更近，则更新最短路径和最小计数
                min_pathlen = pathlen
                min_cnt = tmp_cnt
            elif pathlen == min_pathlen:  # 若当前物品离对手一样近，则视情况更新最小计数
                if tmp_cnt < min_cnt:
                    min_cnt = tmp_cnt
        for i in range(itemlen):
            pathlen = len(api.check.path(
                rival, itemlist[i], method="bfs", player_id=-1)) - 1
            if pathlen == min_pathlen and rival.item_count[itemlist[i].name] == min_cnt:
                next_index_list.append(i)
        # print("next_index_list:", next_index_list)
        # 从距离对方最近的物品开始遍历
        for i in next_index_list:
            # 初始化遍历列表
            new_traverse_list = [x for x in range(itemlen)]
            # print("Processing:", i)
            itemspan[i] = min_pathlen  # 设置itemspan（第一层遍历）
            # print("Before remove:", new_traverse_list)
            if i in new_traverse_list:
                new_traverse_list.remove(i)
            else:
                print("Warning: Element", i, "not in traverse_list")
        #     #print("After remove:", new_traverse_list)
            traverse(context, i, new_traverse_list)
        print("itemspan:", itemspan)

    # #完成物品权重第一层遍历#
    # 物品权重计算预处理
    if context.round < TOTAL_ENERGY/10:  # 若刚开局，则姑且按余下可捡为 余下体力 / 普遍平均获取物品步数 来计算 余下期望可捡物品数
        expected_remaining_gems_count = me.energy / MEAN_COST
    else:
        tot_item_count = sum(me.item_count.values())  # 当前已捡物品总数
        leave_pathlen = len(api.check.path(
            context.me, context.exit, method="bfs", player_id=stuck_check(context))) - 1
        expected_remaining_gems_count = (me.energy - leave_pathlen) * \
            tot_item_count / context.round  # 动态计算余下期望可捡物品数（将离场所需体力纳入考虑）
    print("expected_remaining_gems_count: ",
          expected_remaining_gems_count)

    sorted_item_count = sorted(
        me.item_count.values(), reverse=True)  # 将各物品数目取出并降序排序
    print("sorted_item_count: ", sorted_item_count)
    # 求解各宝石最大收益数量
    gem_optimal_quantity = 0  # 即E(Cm)
    for i in range(5):
        cnt = 0
        for j in range(i+1, 5):
            cnt += sorted_item_count[i] - sorted_item_count[j]
        if cnt <= expected_remaining_gems_count:
            gem_optimal_quantity = (
                expected_remaining_gems_count - cnt) / (5 - i) + sorted_item_count[i]
            break
    print("gem_optimal_quantity: ",
          gem_optimal_quantity)
    expected_remaining_gem_set_score = GEM_SET * \
        (gem_optimal_quantity - min(sorted_item_count))   # 求余下期望成套收益总和 即E(gem_set)
    # 开始遍历
    item_value = [0]*itemlen
    for i in range(itemlen):
        # #处理item_value#
        item_value[i] += itemlist[i].score
        # 如果当前目标是宝箱（废判）
        if False:
            1 == 1  # 不知道写什么，先随便放个东西凑数
        # 若当前目标是宝石
        else:
            # 将物品价值加上成套额外收益
            if me.item_count[itemlist[i].name] < gem_optimal_quantity:
                '''期望成套收益总和姑且先不放'''
                item_value[i] += GEM_SET * ((gem_optimal_quantity -
                                            me.item_count[itemlist[i].name]) / expected_remaining_gems_count)**2
            # print("物品名称itemlist[i].name: ", itemlist[i].name,
            #       "物品数量item_count[itemlist[i].name]: ", me.item_count[itemlist[i].name],
            #       "物品期望收益item_value[i]: ", item_value[i])
        # 计算物品离自己的距离
        pathlen = len(api.check.path(
            me, itemlist[i], method="bfs", player_id=stuck_check(context))) - 1
        # 若该物品在自己获取之前可能已被对手获取，则不予考虑
        if itemspan[i] < pathlen:
            continue
        next_index_list = [x for x in range(itemlen)]
        next_index_list.remove(i)
        new_item_count = copy.deepcopy(me.item_count)
        new_item_count[itemlist[i].name] += 1
        # 开始后续路线排列枚举
        permutation(context, i, i, next_index_list, new_item_count,
                    pathlen, item_value[i]/pathlen)
    print("各物品收益item_value: ", item_value)
    print("各物品权重item_weight: ")
    for i in item_weight:
        print(i, itemlist[i].name, item_weight[i])

    # #寻找下一步的目标物品
    if len(item_weight) == 0:
        print("item_weight为空")
        # 找最近的策略
        dst = api.check.closest_item()  # 找到离我最近的物品
        print("closest_item:", dst)
    else:
        # 找到item_weight中的最大值
        target = list(item_weight.keys())[0]
        for i in item_weight:
            if item_weight[i] > item_weight[target]:
                target = i
        dst = itemlist[target]
        print("target:", dst, dst.name)

    # 若处在孔雀东南飞状态，则强制将目标设为上一个目标
    if pacing_check(context) == True:
        dst = last_dst
    print("当前最终目标（非离场状态下）: ", dst)

    # 更新目标物品记录队列
    pre_dst_list.append(dst)
    pre_pos_list.append([me.row, me.col])
    tail += 1
    if tail-head > 4:
        head += 1

    # 离场特判
    if should_leave(context):
        dst = context.exit
        print("体力不足，离场中")

    # #各个方向期望收益计算
    drc_weight = [0]*4
    # 计算自己到目标物品的距离
    print("计算me_dis时的额外障碍：", calc_extra_obstacles(context))
    me_dis = len(api.check.path(
        me, dst, method="bfs", extra_obstacles=None if is_leaving else calc_extra_obstacles(context), player_id=stuck_check(context))) - 1
    # 若当前目标物品处在额外障碍范围内（即距离计算结果为-1），则随机选择新目标物品
    if me_dis == -1:
        item = random.choice(itemlist)
        while item == last_dst:  # 防止与当前相同
            item = random.choice(itemlist)
        last_dst = dst = item
    # 计算各个方向的泛化期望收益权重
    for i in range(4):
        new_row = me.row + DRC[i][0]
        new_col = me.col + DRC[i][1]
        print("当前考虑方向: ", DRC_STR[i])
        print("当前考虑方向坐标：", new_row, new_col)
        # 若该方向为墙，则不予考虑
        if context.maze[new_row][new_col] == 'WALL':
            print("当前方向为墙")
            continue
        # 若该方向在额外障碍范围内，则不予考虑
        if is_leaving == False and [new_row, new_col] in calc_extra_obstacles(context):
            print("当前方向为额外障碍")
            continue
        # 若当前已被卡住且该方向为对手则不予考虑
        if is_stuck == True and new_row == rival.row and new_col == rival.col:
            print("当前方向为对手")
            continue
        # 计算向某个方向移动后到目标物品的距离
        new_dis = len(api.check.path(
            (new_row, new_col), dst, method="bfs", extra_obstacles=None if is_leaving else calc_extra_obstacles(context), player_id=stuck_check(context))) - 1

        print("new_dis: ", new_dis)
        print("me_dis: ", me_dis)

        # 若离目标物品的距离没有变小，也不予考虑
        if new_dis >= me_dis:
            print("当前方向离目标物品的距离没有变小")
            continue
        # 若下一个位置是某物品（一步之遥），则直接定为该方向，结束update函数
        for item in itemlist:
            if new_row == item.row and new_col == item.col:
                return DRC_STR[i]
        for j in range(itemlen):
            # 计算物品离自己的距离
            pathlen = len(api.check.path(
                (new_row, new_col), itemlist[j], extra_obstacles=None if is_leaving else calc_extra_obstacles(context), method="bfs", player_id=stuck_check(context))) - 1
            drc_weight[i] += itemlist[j].score / pathlen**2
    print("drc_weight: ", drc_weight)

    print("is_stuck:", is_stuck)
    # 找出泛化期望收益权重最大的方向
    direction = DRC_STR[drc_weight.index(max(drc_weight))]

    pre_pos = (me.row, me.col)
    pre_item_count = me.item_count
    last_dst = dst
    return direction


'''
作者：严文岳（本人）
'''
'''
待实现：
'''
