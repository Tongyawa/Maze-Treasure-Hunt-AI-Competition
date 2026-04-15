s = "输平赢"
Ra = float(input("Ra="))
Rb = float(input("Rb="))
Ra2 = float(input("Ra2="))
Ea = 1/(1+10**((Rb-Ra)/400))
Sa = float(input("Sa="))
K = (Ra2-Ra)/(Sa-Ea)
print("K = ", round(K, 2))
