import api
from collections import namedtuple
def calcright(score,length):
    result=(score+1)/(length+1)
    print(result)
    return result
def getmap(context):
    mapa=context.maze
    information={"WALL":-1,"ROAD":0}
    x,y=len(mapa[0]),len(mapa)
    for i in range(y):
        for j in range(x):
            if i == api.get.enemy(what="row") and j == api.get.enemy(what="col"):
                mapa[i][j]=-1
            elif i == api.get.exit(what="row") and j == api.get.exit(what="col"):
                mapa[i][j]=0
            else:
                if mapa[i][j] in information:
                    mapa[i][j]=information[mapa[i][j]]
    
    return mapa
def lenth(context,item,direction,is_exit=False):#算direction方向走过一格后到达item的长度
    DIR={"R":[1,0],"L":[-1,0],"U":[0,-1],"D":[0,1],"S":[0,0]}
    col = api.get.my(what="col")+DIR[direction][0]
    row = api.get.my(what="row")+DIR[direction][1]
    grid=getmap(context)
    if grid[row][col]==0:
        # 定义坐标和方向
        Point = namedtuple("Point", ["x", "y"])
        directions = [[0, 1, 'R'], [1, 0, 'D'], [0, -1, 'L'],[-1, 0, 'U']]
        #初始化
        
        #获得地图
        start=Point(row,col)
        diamond=Point(item.row,item.col)

        queue = [(start, '')]  # 使用list作为队列
        visited = set()
        visited.add(start)
        while queue:
            current, path = queue.pop(0)  # 从队列前端弹出元素
            x, y = current
            # 检查是否到达钻石位置
            if (x, y) == diamond:
                if is_exit:
                    print("exit ",len(path),end="   ")
                else:
                    print(item.name,len(path),end="   ")
                return len(path)  # 找到最短路径，返回指令序列
            for direction in directions:
                nx, ny = x + direction[0]  , y + direction[1]
                if (0 <= nx < len(grid)) and (0 <= ny < len(grid[0])) and (grid[nx][ny] == 0) and ((nx, ny) not in visited):
                    visited.add((nx, ny))
                    # 将新位置和路径加入队列后端
                    queue.append((Point(nx, ny), path + direction[2]))
        return -2  # 如果无法到达宝石，则返回-2
    else: 
        return -2  
def _r(context,score,rights,way):#计算一个方向上的权重
    r_item = api.check.closest_item(["red_gem"])
    b_item = api.check.closest_item(["blue_gem"])
    pu_item = api.check.closest_item(["purple_gem"])
    pi_item = api.check.closest_item(["pink_gem"])
    y_item = api.check.closest_item(["yellow_gem"])
    exit_item = context.exit
    r_item=calcright(score["red_gem"],lenth(context,r_item,way))
    b_item=calcright(score["blue_gem"],lenth(context,b_item,way))
    pu_item=calcright(score["purple_gem"],lenth(context,pu_item,way))
    pi_item=calcright(score["pink_gem"],lenth(context,pi_item,way))
    y_item=calcright(score["yellow_gem"],lenth(context,y_item,way))
    exit_item=calcright(score["exit"],lenth(context,exit_item,way,True))
    global flag_leave1
    rights[way]=r_item+b_item+pu_item+pi_item+y_item
    if flag_leave1:
        rights[way]+=exit_item
def complete_set_calc(context,score):
    bate=0
    bocket=context.players[0].item_count
    SUM=bocket["yellow_gem"]==0 or bocket["pink_gem"]==0 or bocket["red_gem"]==0 or bocket["purple_gem"]==0 or bocket["blue_gem"]==0
    while(not SUM):
        bocket["yellow_gem"]-=1
        bocket["pink_gem"]-=1
        bocket["red_gem"]-=1
        bocket["purple_gem"]-=1
        bocket["blue_gem"]-=1
        SUM=bocket["yellow_gem"]==0 or bocket["pink_gem"]==0 or bocket["red_gem"]==0 or bocket["purple_gem"]==0 or bocket["blue_gem"]==0
    for i in bocket:
        if bocket[i]==0:
            bate+=1#凑齐整套还需要的个数
    for i in bocket:
        if bocket[i]==0:
            score[i]+=20/bate
#def calc
flag_leave1=False
intention=[]
intention_count=[]
lastdistance={"yellow_gem":1000,"pink_gem":1000,"red_gem":1000,"purple_gem":1000,"blue_gem":1000,"exit":1000}
def update(context):
    
    rights={"R":0,"L":0,"U":0,"D":0}#设置权重
    score={"yellow_gem":1,"pink_gem":1,"red_gem":1,"purple_gem":1,"blue_gem":1,"exit":15000}
    complete_set_calc(context,score)

    global flag_leave1
    if not flag_leave1:#上一次不需要离开
        e=context.exit
        path_len = lenth(context,e,"S",True)
        my_energy = api.get.my(what="energy")
        if my_energy == path_len + 1 or my_energy == path_len + 2:
            flag_leave1=True

    print()
    print("现在是第",context.round,"回合")
    print()
    print("向左:")
    _r(context,score,rights,"L")
    print()
    print("向右:")
    _r(context,score,rights,"R")
    print()
    print("向上:")
    _r(context,score,rights,"U")
    print()
    print("向下:")
    _r(context,score,rights,"D")
    print(rights)
    max="R"
    for i in rights:
        if rights[i]>=rights[max]:
            max=i
    path_len = lenth(context,context.exit,"S",True)
    if flag_leave1 and True:
        mapa = getmap(context)
        x,y=len(mapa[0]),len(mapa)
        for i in range(y):
            print()
            for j in range(x):
                print(" "*(3-len(str(mapa[i][j]))),mapa[i][j],end="")
            
        #max = api.check.next(end=(context.exit.row, context.exit.col))
    return max