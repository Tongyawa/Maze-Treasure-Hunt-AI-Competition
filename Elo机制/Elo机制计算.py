s="输平赢"
K=16
Ra=float(input("Ra="))
Rb=float(input("Rb="))
Ea=1/(1+10**((Rb-Ra)/400))

for i in range(3):
    Sa=i/2
    Ra2=Ra+K*(Sa-Ea)
    print(s[i], "：分数变化是", round(K*(Sa-Ea),2), "分; 最终总分为", round(Ra2,2), "分")
