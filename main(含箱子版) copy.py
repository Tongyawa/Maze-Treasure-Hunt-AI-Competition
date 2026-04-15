import api
import copy

# 可调常量
GEM_SET = 20  # 成套宝石得分
IS_BOX_ENERGY = 0  # 若开宝箱拿体力则为1，拿分数为0（后续用于mean_gem2的计算）
box_values = [-10, 30]
BOX_MULTIPLE = 1
BOX_VALUE_MEAN = BOX_MULTIPLE * sum(box_values) / len(box_values)
TOTAL_ENERGY = 1000  # 总体力值
MEAN_COST = 4.5  # 平均每个物品获取所需步数
# MEAN_GEM = TOTAL_ENERGY/MEAN_COST/5  # 平均每种宝石的期望获取量（常量，后续通过计算mean_gem2来实时调整）

# 固定常量
BOX = "box"
RG = "red_gem"
BG = "blue_gem"
PG = "pink_gem"
YG = "yellow_gem"
PG = "purple_gem"
DRC = [[-1, 0], [1, 0], [0, -1], [0, 1]]    # (row, col) 4个方向依次对应上下左右
DRC_STR = "UDLR"


# 全局变量
pre_pos = None
pre_item_count = None
is_leaving = False
is_stuck = False
itemlist = []
itemlen = 0  # 存储itemlist长度
itemgragh = []
itemspan = {}  # 存储物品“寿命”
item_weight = {}  # 存储物品权重


# 定义一个函数，判断是否需要立即离场
def should_leave(context):
    global is_leaving, pre_item_count
    my_energy = context.me.energy
    e_row = context.exit.row
    e_col = context.exit.col
    path_len = api.check.path_len(row=e_row, col=e_col)
    # 若当前体力小于等于离场最小体力加5，并且刚获取到某一物品(item_count有变化)，则见好就收，开始离场，以防被阴
    if my_energy <= path_len + 1 + 5 and pre_item_count != context.me.item_count:
        is_leaving = True
    # 若当前体力小于等于离场最小体力，则强制离场
    if my_energy <= path_len + 1:
        is_leaving = True
    return is_leaving

# 判断是否被卡住


def stuck_check():
    if is_stuck:
        return 0
    else:
        return -1

# 遍历，处理itemspan


def traverse(current_index, traverse_list):
    global itemspan
    # print("\ntraverse函数调用------------")
    if traverse_list == []:
        # print("current_index:", current_index, "列表为空，返回")
        return
    # print("current_itemkind:", itemlist[current_index].name, "current_index:", current_index, "traverse_list:", traverse_list)
    min_pathlen = 99999
    for i in traverse_list:
        pathlen = itemgragh[current_index][i]
        if pathlen > 0 and pathlen < min_pathlen:
            min_pathlen = pathlen
    # print("min_pathlen:", min_pathlen)
    # 在还没遍历过的物品中，找出所有离当前物品最近的物品作为下一层遍历的起点，组成列表
    next_index_list = [
        i for i in traverse_list if itemgragh[current_index][i] == min_pathlen]
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
        traverse(i, new_traverse_list)


def permutation(context, initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight):
    global item_weight
    # print("-----------------------")
    # print("permutation函数调用")
    # print("initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight:")
    # print(initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight)
    # #边界处理#
    if next_index_list == []:
        if initial_index in item_weight:  # 若item_weight中已有值，则取较大者保留
            item_weight[initial_index] = max(
                item_weight[initial_index], tot_weight)
        else:  # 否则新增
            item_weight[initial_index] = tot_weight

    # 物品权重计算预处理
    if context.round < TOTAL_ENERGY/10:  # 若刚开局，则姑且按余下可捡为 余下体力 / 普遍平均获取物品步数 来计算 余下期望可捡物品数
        expected_remaining_gems_count = context.me.energy / MEAN_COST
    else:
        tot_item_count = sum(item_count.values())  # 当前已捡物品总数
        expected_remaining_gems_count = context.me.energy * \
            tot_item_count / context.round  # 动态计算余下期望可捡物品数
    # print("expected_remaining_gems_count: ", expected_remaining_gems_count)

    sorted_item_count = sorted(
        item_count.values(), reverse=True)  # 将各物品数目取出并降序排序
    sorted_item_count.remove(item_count[BOX])  # 删除箱子数目
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
    # print("gem_optimal_quantity: ", gem_optimal_quantity)
    expected_remaining_gem_set_score = GEM_SET * \
        (gem_optimal_quantity - min(sorted_item_count))   # 求余下期望成套收益总和 即E(gem_set)
    # #完成物品权重第n层遍历#
    item_value = [0]*itemlen
    for i in next_index_list:  # 枚举下一个目标物品
        # #处理item_value#
        # print("排列组合下一个 i:", i)
        item_value[i] += itemlist[i].score
        # 如果当前目标是宝箱
        if itemlist[i].name == BOX:
            1 == 1  # 不知道写什么，先随便放个东西凑数
        # 若当前目标是宝石
        else:
            # 将物品价值加上成套额外收益
            '''期望成套收益总和姑且先不放'''
            if item_count[itemlist[i].name] < gem_optimal_quantity:
                item_value[i] += GEM_SET * (
                    gem_optimal_quantity - item_count[itemlist[i].name]) / expected_remaining_gems_count
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
                        itemgragh[current_index][i], tot_weight + item_value[i] / itemgragh[current_index][i])


def update(context):
    global pre_pos, pre_item_count, is_leaving, is_stuck, itemlist, itemlen, itemgragh, itemspan, item_weight
    me = context.me
    rival = context.players[1]
    print("-----------------")
    print("Round ", context.round)
    print("我的位置：", me.row, me.col)
    print("对手位置：", rival.row, rival.col)
    # 全局变量
    itemlist = []
    itemlen = 0  # 存储itemlist长度
    itemgragh = []
    itemspan = {}  # 存储物品“寿命”
    item_weight = {}  # 存储物品权重

    # #将地图上所有物品存入一个一维列表itemlist#
    for itemkind in context.items.values():
        for item in itemkind:
            # 箱子需特殊处理
            if item.name == BOX:
                item.score = BOX_VALUE_MEAN
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
                itemlist[i], itemlist[j], method="jps", player_id=stuck_check())) - 1)
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

        # 寻找离对手最近的物品并计算距离
        closest_item = api.check.closest_item(player=rival)
        min_pathlen = api.check.path_len(
            closest_item.row, closest_item.col, player=rival)
        for i in range(itemlen):
            pathlen = api.check.path_len(
                itemlist[i].row, itemlist[i].col, player=rival)
            if pathlen == min_pathlen:
                next_index_list.append(i)
        print("next_index_list:", next_index_list)
        # 从距离对方最近的物品开始遍历
        for i in next_index_list:
            # 初始化遍历列表
            new_traverse_list = [x for x in range(itemlen)]
            print("Processing:", i)
            itemspan[i] = min_pathlen  # 设置itemspan（第一层遍历）
            print("Before remove:", new_traverse_list)
            if i in new_traverse_list:
                new_traverse_list.remove(i)
            else:
                print("Warning: Element", i, "not in traverse_list")
            print("After remove:", new_traverse_list)
            traverse(i, new_traverse_list)
        print("itemspan:", itemspan)

    # #完成物品权重第一层遍历#
    # 物品权重计算预处理
    if context.round < TOTAL_ENERGY/10:  # 若刚开局，则姑且按余下可捡为 余下体力 / 普遍平均获取物品步数 来计算 余下期望可捡物品数
        expected_remaining_gems_count = me.energy / MEAN_COST
    else:
        tot_item_count = sum(me.item_count.values())  # 当前已捡物品总数
        expected_remaining_gems_count = me.energy * \
            tot_item_count / context.round  # 动态计算余下期望可捡物品数
    print("expected_remaining_gems_count: ",
          expected_remaining_gems_count)

    sorted_item_count = sorted(
        me.item_count.values(), reverse=True)  # 将各物品数目取出并降序排序
    sorted_item_count.remove(me.item_count[BOX])  # 删除箱子数目
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
        # 如果当前目标是宝箱
        if itemlist[i].name == BOX:
            1 == 1  # 不知道写什么，先随便放个东西凑数
        # 若当前目标是宝石
        else:
            # 将物品价值加上成套额外收益
            if me.item_count[itemlist[i].name] < gem_optimal_quantity:
                '''期望成套收益总和姑且先不放'''
                item_value[i] += GEM_SET * (
                    gem_optimal_quantity - me.item_count[itemlist[i].name]) / expected_remaining_gems_count
            print("物品名称itemlist[i].name: ", itemlist[i].name,
                  "物品数量item_count[itemlist[i].name]: ", me.item_count[itemlist[i].name],
                  "物品期望收益item_value[i]: ", item_value[i])
        # 计算物品离自己的距离
        pathlen = len(api.check.path(
            me, itemlist[i], method="jps", player_id=stuck_check())) - 1
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
    print("item_weight:")
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
    # 离场特判
    if should_leave(context):
        dst = context.exit
        print("体力不足，离场中")

    # #各个方向期望收益计算
    drc_weight = [0]*4
    # 计算自己到目标物品的距离
    me_dis = len(api.check.path(
        me, dst, method="jps", player_id=stuck_check())) - 1
    # 计算各个方向的泛化期望收益权重
    for i in range(4):
        new_row = me.row + DRC[i][0]
        new_col = me.col + DRC[i][1]
        # 若该方向为墙，则不予考虑
        if context.maze[new_row][new_col] == 'WALL':
            continue
        # 计算向某个方向移动后到目标物品的距离
        new_dis = len(api.check.path(
            (new_row, new_col), dst, method="jps", player_id=stuck_check())) - 1
        # 若离目标物品的距离没有变小，也不予考虑
        if new_dis >= me_dis:
            continue
        # 若下一个位置是某物品（一步之遥），则直接定为该方向，结束update函数
        for item in itemlist:
            if new_row == item.row and new_col == item.col:
                return DRC_STR[i]
        for j in range(itemlen):
            # 计算物品离自己的距离
            pathlen = len(api.check.path(
                me, itemlist[j], method="jps", player_id=stuck_check())) - 1
            drc_weight[i] += itemlist[j].score / pathlen**2
    # 找出泛化期望收益权重最大的方向
    direction = DRC_STR[drc_weight.index(max(drc_weight))]

    pre_pos = (me.row, me.col)
    pre_item_count = me.item_count
    return direction


'''
作者：严文岳（本人）
'''
'''
待实现：
'''
r'''
废稿：
# 统计所收集到的宝石总数
                for j in me.item_count:
                    if j != BOX:
                        tot_gem += me.item_count[j]
                # 计算X'。若开宝箱拿体力，则is_box_energy == 1，计入mean_gem；反之为0，不影响
                mean_gem2 = MEAN_GEM - me.item_count[BOX]/5 + \
                    IS_BOX_ENERGY * BOX_VALUE_MEAN * \
                    me.item_count[BOX] / MEAN_COST / 5
                if mean_gem2 - me.item_count[itemlist[i].name] <= 0:
                    print("警告：mean_gem2 - item_count[itemlist[i].name]<=0！")
                elif (5*mean_gem2 - tot_gem) <= 0:
                    print("警告：(5*mean_gem2 - tot_gem)<=0！")
                # 加上成套额外收益估计
                else:
                    item_value[i] += GEM_SET * \
                        (mean_gem2 - me.item_count[itemlist[i].name]
                         ) / (5*mean_gem2 - tot_gem)
'''
