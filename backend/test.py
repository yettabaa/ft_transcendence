dic = {}
var = 210
var1 = 310


dic["room_name"] = {"player1":1}
dic["room_name"]["player2"] = 2
dic["room_name1"] = {"player1":3}
dic["room_name1"]["player2"] = 4
dic["room_name2"] = {"player1":5}
dic["room_name2"]["player2"] = 6
dic["room_name3"] = {"player1":6}
for key ,value in dic.items():
    if len(value) < 2:
        print (value, key)


print(dic)
# print(t["player2"])

# import asyncio
# from email import message

# # Define an asynchronous function to simulate downloading a file
# async def download_file(file_number, duration):

#     while 1:
#         print(file_number)
#         await asyncio.sleep(0.0003)

# # Define the main function to create and run multiple tasks
# async def main():
#     task2 = asyncio.create_task(download_file(2, 5))
#     task1 = asyncio.create_task(download_file(1, 3))
     
#     # while 1:
#     #     print ("")

#     await asyncio.sleep(10)
#     # task1.cancel()
#     # task2.cancel()

#     # await asyncio.gather(task1, task2)

# # Run the main function using the event loop
# asyncio.run(main())
