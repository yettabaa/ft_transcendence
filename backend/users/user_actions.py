from  .utils  import UserRelation ,get_relation 
from .models import * 
import re 
from django.db.models import Q 
import json

def make_websocket_response(type,identifier,data ,code=200,message="ok"):
           res =  {
            "type":  type ,
            "code": code, 
            "message" : message ,
            "identifier": identifier,
            "data": data 
            }
           return json.dumps(res)
def isUserOnline(username:str ) -> bool: 
    from game.GameWebsocket import onlineUser 
    try:
        count  = onlineUser[username]
        return count != 0   
    except KeyError:
        return False

class UserActions():

    def BAD_REQUEST(type, identifier):
        return json.dumps({
            "type":  type ,
            "code": 400,
            "message": "bad request",
            "identifier": identifier
              })

    def online(user, username):   
        
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user, user2=user2)
            online   = False
            if relation == UserRelation.FRIEND:
                 online = isUserOnline(username=username)
            return make_websocket_response(type="online", identifier=username,data=  {"value" : online})

        except Exception as ex:
            return UserActions.BAD_REQUEST(type="user-action", identifier=username)

    def add(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user, user2=user2)
            print(f"{relation}")
            if relation == UserRelation.NONE:
                invi = Invitation.objects.create(sender=user, receiver=user2)
                invi.save()
                return make_websocket_response(type="user-action",identifier=username,data=  {"value" : "add"})
            else:
                return UserActions.BAD_REQUEST(type="user-action",identifier=username)

        except Exception as ex:
            return UserActions.BAD_REQUEST(type="user-action",identifier=username) 

    def accept(user, username):
        print("accept")
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user,user2=user2)
            print(f'relation {relation}')
            if relation == UserRelation.REC_REQ:
                invi = Invitation.objects.filter(Q(sender=user2) | Q(receiver=user2))[0]
                print(f'invi {invi}')
                invi.delete()
                conv =  Conversation.objects.all()[0] ## here must Be add new Object 
                print(f"conversation {conv}")
                # if not conv:
                #     return UserActions.BAD_REQUEST(type="user-action",identifier=username) 
                friend = Friend.objects.create(user1=user, user2=user2,conversation_id=conv)
                friend.save()
                return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "accept"})
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)

    def deny(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user,user2=user2)
            print(f'relation {relation}')
            if relation == UserRelation.REC_REQ:
                invi = Invitation.objects.filter(Q(sender=user2) | Q(receiver=user))[0]
                if invi == None:
                    return UserActions.BAD_REQUEST(type="user-action",identifier=username)
                invi.delete()
                return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "deny"})
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)

    def block(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user,user2=user2)
            print(f'relation {relation}')
            if relation != UserRelation.BLOCKED and relation != UserRelation.BLOCKER:
                # step1 remove send and receive Friends 
             
                invi = Invitation.objects.filter(Q(sender=user2) | Q(receiver=user2))
                if invi == None:
                    return UserActions.BAD_REQUEST(type="user-action",identifier=username)
                for item in invi:
                    if item.sender == user or item.receiver:
                        item.delete()

                #step2 remove friends 
                friends = Friend.objects.filter(Q(user1=user2) | Q(user2=user2))
                if friends == None:
                    return UserActions.BAD_REQUEST(type="user-action",identifier=username)
                for item in friends:
                    if item.user1 == user or item.user2 == user:
                        item.delete()
                block_record = Blocked_Friend.objects.create(blocker=user, blocked=user2)
                block_record.save()
                return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "block"})
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)

    def unblock(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user,user2=user2)
            print(f'get_relation = {relation}')
            if relation != UserRelation.BLOCKER:
                 return UserActions.BAD_REQUEST(type="user-action",identifier=username)
            block_record =  Blocked_Friend.objects.get(blocker=user,blocked=user2)
            print("record")
            block_record.delete()
            return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "unblock"})
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)
        
    def unfriend(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user, user2=user2)
        
            print(f'get_relation = {relation}')
            if relation != UserRelation.FRIEND:
                 return UserActions.BAD_REQUEST(type="user-action",identifier=username)
            records =  Friend.objects.filter(Q(user1=user) | Q(user2=user))
            for item in records: 
                if item.user1 == user2 or item.user2 == user2:
                    print(f"friends record found {item}")
                    item.delete()
            return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "unfriend"})
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)

    def cancel(user, username):
        try:
            user2   =  User.objects.get(username=username)
            relation = get_relation(user1=user, user2=user2)
        
            print(f'get_relation = {relation}')
            if relation != UserRelation.SEND_REQUEST:
                 return UserActions.BAD_REQUEST(type="user-action",identifier=username)
            record =  Invitation.objects.get(sender=user, receiver=user2)      
            record.delete()
            return make_websocket_response(type="user-action", identifier=username,data=  {"value" : "cancel"})
        except Exception as ex:
            print(ex)
            return UserActions.BAD_REQUEST(type="user-action",identifier=username)

class UserUpdates() :

    def update(user : User, data) -> str :
        try: 
            if data["identifier"] == 'username' :
                return  UserUpdates.update_username(user=user,username=data["data"]["value"])
            elif data["identifier"] == 'email' :
                return  UserUpdates.update_email(user=user,email=data["data"]["value"])
            elif data["identifier"] == 'tfa-change':
                return  UserUpdates.update_tfa_email(user=user,email=data["data"]["value"])
            elif data["identifier"] == 'tfa-status':
                return  UserUpdates.update_tfa_status(user=user,status=data["data"]["value"])
        except Exception as e:
            print(f"update error {e}")
            return UserActions.BAD_REQUEST(type="update",identifier="?")

    def update_username(user, username):
        if username == None:
            return UserActions.BAD_REQUEST(type="update",identifier="?")
        regex = r'^[a-z][\w-]{2,15}[a-z\d]$'

        if re.match(regex, username):
            user.username=username
            try:
                user.save()
                return make_websocket_response(type="update",identifier="username",data={"value": username}, message="username changed successfully")
            except:
                return make_websocket_response(type="update", identifier="username", data={"value": username},message="username already  exist ")
        else:
            return make_websocket_response(type="update",identifier="username",data={"value": username},code=404,message="invalid username syntax")

    def update_email(user, email):
            try:
                user.email = email
                user.save()
                return make_websocket_response(type="update",identifier="email",data={"value": email}, message="email changed successfully")
            except:
                return make_websocket_response(type="update", identifier="email", data={"value": "email"},code=404,message="invalid email  or exist email")
        
    def update_tfa_email(user, email):
        
        regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        print(f"is match {re.match(regex, email)}")
        if  re.match(regex, email)  == None:
            return make_websocket_response(type="update", identifier="tfa-change", data={"value": email},code=404, message="Invalid Email Syntax")
        
        try:
            tfa_obj = Auth.objects.get(user_id=user)
            tfa_obj.content = email
            tfa_obj.is_enabled = True
            tfa_obj.save()
            return make_websocket_response(type="update", identifier="tfa-change", data={"value": email, "status": True},message="tfa updated  successfully")
        except Exception as e:
            tfa_obj =   Auth.objects.create(user_id=user, content=email,is_enabled=True)    
            tfa_obj.save()
            print(f"exeception{e}")
            return make_websocket_response(type="update", identifier="tfa-change", data={"value": email, "status": True},message="tfa create successfully")


    def update_tfa_status(user, status):
        try:
            tfa_obj = Auth.objects.get(user_id=user)
            tfa_obj.is_enabled = status
            tfa_obj.save()
            return make_websocket_response(type="update", identifier="tfa-status", data={"value": status},message="tfa status updated   successfully")
        except Exception as e:
            return make_websocket_response(type="update", identifier="tfa-status", data={"value": status},code=404, message="Invalid value")
