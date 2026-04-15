
rival_score = 21
me_score = 43
item_count = {0: 4, 1: 3, 2: 3, 3: 4, 4: 1}
item_count_min = min(item_count.values())
i = 1
while rival_score <= me_score - 20*i:
    i += 1
i += 1
expected_remaining_gems_count = sum(
    item_count_min + i - value for value in item_count.values() if value < item_count_min + i)
print([item_count_min + i - value for value in item_count.values() if value < item_count_min + i])
print("补至", item_count_min + i, "套")
print("expected_remaining_gems_count = ", expected_remaining_gems_count)
