dic = {}
var = 210
var1 = 310
print("player1" in dic["room_name"])
dic["room_name"] = {"player":var}
dic["room_name"] = {"player1":var}
# dic["room_name"]["player1"] = var
dic["room_name"]["player2"] = var


t = dic["room_name"]
t["lab"] = 45
print(dic)
print(t["player2"])