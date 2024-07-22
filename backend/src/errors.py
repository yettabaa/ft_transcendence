from  users.design_patterns import * 
from rest_framework.response import Response 

INVALID_TOKEN_RES  =  Response(ErrorBuilder().set_type('tokens').set_message("invalid or expired").build() ,status=400)
INVALID_PARAMS_RES =  Response( ErrorBuilder().set_type('params').set_message("invalid params").build(),status=400)
USER_NOT_FOUND_RES =  Response(ErrorBuilder().set_type('User_Not_Found').set_message("User not Found").build(),status=404) 