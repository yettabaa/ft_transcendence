import json 
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from users.models import User
from users.user_actions import UserActions , UserUpdates
from .serializer import SystemSocketSerializer

from channels.generic.websocket import WebsocketConsumer 
from urllib.parse import parse_qs 
import uuid

onlineUser = {}

def addToOnline(username):

    try:
        onlineUser[username] += 1; 
        print(f"addToOnline  Acount {onlineUser[username]}")
    except KeyError:
        onlineUser[username] = 0

def RemoveOneOnline(username):
    try:
        print(f"online Acount {onlineUser[username]}")
        onlineUser[username] -= 1;  
        if onlineUser[username] <= 0 :
            del  onlineUser[username] 
          
    except KeyError:
        return

import time 
class SystemSocket(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.user = User.objects.get(username='beta')
        addToOnline(self.user.username)

        self.room_name = str(uuid.uuid4()).replace("-","_")
        self.notification_name = f'notification_{self.user.username}'

        print(f"chanel name {self.channel_name }")
        self.channel_layer = get_channel_layer()
        async_to_sync(self.channel_layer.group_add)(self.room_name, self.channel_name)
        async_to_sync(self.channel_layer.group_add)(self.notification_name, self.channel_name)


    def receive(self, text_data):
        data_dict = None
        try:
            print(text_data)
            data_dict = json.loads(text_data)
            serializer =  SystemSocketSerializer(data=data_dict)
            if serializer.is_valid() == False:
                raise  ValueError()  
            
            type = data_dict["type"]
            identifier = data_dict['identifier']  # this for check identifier is present  in  data_dict 
            print(f"sys.{type}")
            print(f"chanel name {self.room_name } ")
            async_to_sync(self.channel_layer.group_send)(
            self.room_name ,
            {
                "type":f"sys.{type}",
                "data": data_dict
            }
            )
            print("send event --- ")
        except Exception as ex:
            async_to_sync(self.channel_layer.group_send)(self.room_name, {"type" :  "sys.error"})
            print(f"<> invalid Json <>{ex}")
    

    def sys_error(self, event):
            data = {"code": 400, "message": "bad request" }
            self.send(text_data= json.dumps(data))

    def sys_online(self, event):
        print("call -> online")
        data = UserActions.online(self.user, event["data"]['identifier'])
        self.send(text_data=data)

    def sys_add(self, event):
        data = UserActions.add(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_accept(self, event):
        data = UserActions.accept(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_deny(self, event):
        data = UserActions.deny(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_block(self, event):
        data = UserActions.block(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_unblock(self, event):
        data = UserActions.unblock(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_unfriend(self, event):
        data = UserActions.unfriend(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_cancel(self, event):
        data = UserActions.cancel(self.user, event["data"]['identifier'])
        self.send(text_data=data)
        pass

    def sys_update(self, event):
        print("update...")
        user = None 
        try:
            user = User.objects.get(username="beta")
        except:
            print("User doesn't exist ")

        data = UserUpdates.update(user,  event["data"])
        if data == None :
            data = {"code": 400, "message": "bad request" }.__str__()
        self.send(text_data=data)
        pass 

    def disconnect(self, code):
        
        async_to_sync(self.channel_layer.group_discard)(self.room_name , self.channel_name)
        async_to_sync(self.channel_layer.group_discard)(self.notification_name, self.channel_name)
        RemoveOneOnline(self.user.username)
        self.close()