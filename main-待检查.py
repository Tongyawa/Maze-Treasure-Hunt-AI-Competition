import api
import copy

# 可调常量
GEM_SET = 20  # 成套宝石得分
IS_BOX_ENERGY = 1  # 若开宝箱拿体力则为1，拿分数为0（后续用于mean_gem2的计算）
box_values = [0, 2, 4, 6, 8, 10]
BOX_VALUE_MEAN = sum(box_values) / len(box_values)
TOTAL_ENERGY = 1000  # 总体力值
MEAN_COST = 5  # 平均每个物品获取所需步数
MEAN_GEM = TOTAL_ENERGY/MEAN_COST/5  # 平均每种宝石的期望获取量（常量，后续通过计算mean_gem2来实时调整）

# 固定常量
BOX = "box"
RG = "red_gem"
BG = "blue_gem"
PG = "pink_gem"
YG = "yellow_gem"
PG = "purple_gem"

# 全局变量
prepos = None
is_stuck = False
itemlist = []
itemlen = 0  # 存储itemlist长度
itemgragh = []
itemspan = {}  # 存储物品“寿命”
item_weight = {}  # 存储物品权重


# 定义一个函数，判断是否需要立即离场
def should_leave(context):
    my_energy = context.me.energy
    e_row = context.exit.row
    e_col = context.exit.col
    path_len = api.check.path_len(row=e_row, col=e_col)
    return my_energy <= path_len + 1

# 判断是否被卡住


def stuck_check():
    if is_stuck:
        return 0
    else:
        return -1

# 遍历，处理itemspan


def traverse(current_index, traverse_list):
    global itemspan
    print("traverse函数调用------------")
    if traverse_list == []:
        print("current_index:", current_index, "列表为空，返回")
        return
    print("current_index:", current_index, "traverse_list(开头):", traverse_list)
    min_pathlen = 99999
    for i in traverse_list:
        pathlen = itemgragh[current_index][i]
        if pathlen > 0 and pathlen < min_pathlen:
            min_pathlen = pathlen
    # 在还没遍历过的物品中，找出所有离当前物品最近的物品作为下一层遍历的起点，组成列表
    next_index_list = [
        i for i in traverse_list if itemgragh[current_index][i] == min_pathlen]
    for i in next_index_list:
        print("current_index:", current_index,
              "traverse_list(循环内):", traverse_list)
        # 设置itemspan（第n层遍历，置为原先的span 和 前一层的span+当前物品到下一物品的距离 当中较小的值）
        if i in itemspan:  # 若i已在itemspan中，则取较小值
            itemspan[i] = min(
                itemspan[i], itemspan[current_index] + min_pathlen)
        else:
            itemspan[i] = min_pathlen

        # 创建traverse_list的新副本进行递归调用
        new_traverse_list = copy.deepcopy(traverse_list)
        print("Processing:", i)
        print("Before remove:", new_traverse_list)
        if i in new_traverse_list:
            new_traverse_list.remove(i)
        else:
            print("Warning: Element", i, "not in traverse_list")
        print("After remove:", new_traverse_list)
        traverse(i, new_traverse_list)


def permutation(initial_index, current_index, next_index_list, item_count, tot_pathlen, tot_weight):
    global item_weight
    # #边界处理#
    if next_index_list == []:
        if initial_index in item_weight:  # 若item_weight中已有值，则取较大者保留
            item_weight[initial_index] = max(
                item_weight[initial_index], tot_weight)
        else:  # 否则新增
            item_weight[initial_index] = tot_weight
    # #完成物品权重第n层遍历#
    item_value = [0]*itemlen
    for i in next_index_list:  # 枚举下一个目标物品
        # #处理item_value#
        print("Line86 i:", i)
        item_value[i] += itemlist[i].score
        # 如果当前目标是宝箱
        if itemlist[i].name == BOX:
            1 == 1  # 不知道写什么，先随便放个东西凑数
        # 若当前目标是宝石
        else:
            # 统计所收集到的宝石总数
            tot_gem = 0
            for j in item_count:
                if j != BOX:
                    tot_gem += item_count[j]
            # 计算X'。若开宝箱拿体力，则is_box_energy == 1，计入mean_gem；反之为0，不影响
            mean_gem2 = MEAN_GEM - item_count[BOX]/5 + \
                IS_BOX_ENERGY * BOX_VALUE_MEAN * \
                item_count[BOX] / MEAN_COST / 5
            # 加上成套额外收益估计
            item_value[i] += GEM_SET * \
                (mean_gem2 - item_count[itemlist[i].name]
                 ) / (5*mean_gem2 - tot_gem)

        # #第n层遍历#
        new_next_index_list = copy.deepcopy(next_index_list)
        new_next_index_list.remove(i)
        new_item_count = copy.deepcopy(item_count)
        new_item_count[itemlist[i].name] += 1
        # 若该物品在自己获取之前可能已被对手获取，则不将该物品计入item_count、tot_pathlen和tot_weight（但new_next_index_list需更新）
        if itemspan[i] < tot_pathlen + itemgragh[current_index][i]:
            permutation(initial_index, i, new_next_index_list,
                        item_count, tot_pathlen, tot_weight)
        # 否则记为获取
        else:
            permutation(initial_index, i, new_next_index_list, new_item_count, tot_pathlen +
                        itemgragh[current_index][i], tot_weight + item_value[i] / itemgragh[current_index][i])


def update(context):
    
    me = context.me
    # print(context.items)
    if should_leave(context):
        e_row = api.get.exit("row")
        e_col = api.get.exit("col")
        direction = api.check.next((e_row, e_col))
        print("体力不足，离场中")
    else:
        # #完成物品权重第一层遍历#
        item_value = [0]*itemlen
        for i in range(itemlen):
            # #处理item_value#
            item_value[i] += itemlist[i].score
            # 如果当前目标是宝箱
            if itemlist[i].name == BOX:
                1 == 1  # 不知道写什么，先随便放个东西凑数
            # 若当前目标是宝石
            else:
                tot_gem = 0
                # 统计所收集到的宝石总数
                for j in me.item_count:
                    if j != BOX:
                        tot_gem += me.item_count[j]
                # 计算X'。若开宝箱拿体力，则is_box_energy == 1，计入mean_gem；反之为0，不影响
                mean_gem2 = MEAN_GEM - me.item_count[BOX]/5 + \
                    IS_BOX_ENERGY * BOX_VALUE_MEAN * \
                    me.item_count[BOX] / MEAN_COST / 5
                # 加上成套额外收益估计
                item_value[i] += GEM_SET * \
                    (mean_gem2 -
                     me.item_count[itemlist[i].name]) / (5*mean_gem2 - tot_gem)

            # #第一层遍历#
            # 计算物品离自己的距离
            me = context.me
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
            permutation(i, i, next_index_list, new_item_count,
                        pathlen, item_value[i]/pathlen)
        print("item_weight:")
        for i in item_weight:
            print(i, item_weight[i])
        # 找到item_weight中的最大值
        target = 0
        for i in item_weight:
            if item_weight[i] > item_weight[target]:
                target = i
        direction = api.check.next(itemlist[target])

    prepos = (me.row, me.col)
    return direction



