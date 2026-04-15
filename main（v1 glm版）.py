import api

# 定义一个函数，判断是否需要立即离场


def should_leave():
    my_energy = api.get.my("energy")
    e_row = api.get.exit("row")
    e_col = api.get.exit("col")
    path_len = api.check.path_len(row=e_row, col=e_col)
    return my_energy <= path_len + 1

# 定义一个函数，获取离自己最近的物品（宝石或宝箱）


def closest_item():
    items = api.get.items()
    min_dist = float('inf')
    closest_item = None
    for item in items:
        if item.name in ["red_gem", "blue_gem", "pink_gem", "yellow_gem", "purple_gem", "box"]:
            dist = api.check.path_len(row=item.row, col=item.col)
            if dist < min_dist:
                min_dist = dist
                closest_item = item
    return closest_item


def update(context):
    if should_leave():
        e_row = api.get.exit("row")
        e_col = api.get.exit("col")
        direction = api.check.next((e_row, e_col))
        print("体力不足，离场中")
    else:
        item = closest_item()
        if item:
            direction = api.check.next(item)
            print(f"前往最近的{item.name}")
        else:
            direction = "S"
            print("没有最近的物品，保持不动")

    return direction
