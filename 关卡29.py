# 请你完整编写代码
import api


def update(context):
    print(context.items)

    m_row = context.me.row
    m_col = context.me.col
    
    # 使用寻路算法自动生成到达目标的路线
    if should_leave(context):
        target = context.exit
        print("体力不足，离场中")
    else:
        target = target_choice(context)
    path = api.check.path(start=(m_row, m_col), end=(target.row, target.col))
    #print(path)
    t_row = path[1][0]
    t_col = path[1][1]

    if t_row > m_row:
        return "D"
    elif t_row < m_row:
        return "U"
    elif t_col > m_col:
        return "R"
    elif t_col < m_col:
        return "L"


def target_choice(context):
    min_distance = 99
    # 遍历场上所有物品到企鹅的距离，将target_gem设置为距离更小的道具名称
    for i in context.items:
        if context.items[i]==[]:
            continue
        m_row = context.me.row
        m_col = context.me.col
        item = context.items[i][0]
        path = api.check.path(start=(m_row, m_col), end=(item.row, item.col))
        distance = len(path) - 1
        if distance < min_distance:
            min_distance = distance
            target = i
    # 遍历场上所有宝石到企鹅的距离，将target_gem设置为距离更小的宝石名称

    print(target)
    return context.items[target][0]


# 定义一个函数，判断是否需要立即离场
def should_leave(context):
    my_energy = api.get.my("energy")
    m_row = context.me.row
    m_col = context.me.col
    e_row = context.exit.row
    e_col = context.exit.col
    path_len = abs(m_row-e_row)+abs(m_col-e_col)
    return my_energy <= path_len + 1