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
