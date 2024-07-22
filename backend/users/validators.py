
#? RegistrationView
def validate_request_data_register(request):
    required_keys = {"type", "data"}
    if set(request.keys()) != required_keys:
        return False

    if request['type'] not in ['normal', 'oauth']:
        return False

    if request["type"] == 'normal':
        normal_required_keys = {"username", "email", "password", "retype_password"}

        if set(request["data"].keys()) != normal_required_keys:
            return False

    elif request["type"] == 'oauth':
        oauth_required_keys = {"code", "state"}
        
        if set(request["data"].keys()) != oauth_required_keys:
            return False
    return True


#? LoginView
def validate_request_data_login(request):
    required_keys = {"type", "data", "refer"}
    if set(request.keys()) != required_keys:
        return False

    if request['type'] not in ['normal', 'oauth']:
        return False

    if request["type"] == 'normal':
        normal_required_keys = {"identity", "password"}
        identity_required_keys = {"type", "value"}
        
        if set(request["data"].keys()) != normal_required_keys:
            return False
        
        if set(request["data"]["identity"].keys()) != identity_required_keys:
            return False

    elif request["type"] == 'oauth':
        oauth_required_keys = {"code", "state"}
        
        if set(request["data"].keys()) != oauth_required_keys:
            return False
    return True


#? Check_2FAView
def validate_request_data_2fa(request):
    required_keys = {"otp", "token", "refer"}
    request_keys = set(request.keys())

    if required_keys == request_keys:
        return True
    return False


#? ForgetPasswordView
def validate_request_data_forget_pwd(request):

    required_keys = {"email", "refer"}
    request_keys = set(request.keys())

    if required_keys == request_keys:
        return True
    return False

#? UpdatePasswordView

def validate_request_data_upgrade_pwd(request):
    required_keys = {"token", "data"}
    request_keys = set(request.keys())

    if required_keys != request_keys:
        return False

    if not isinstance(request.get("data"), dict):
        return False
    
    required_data_args = {"password", "retype_password"}

    data_keys = set(request["data"].keys())
    if required_data_args != data_keys:
        return False
    return True


#? TFA_Register
def validate_request_data_oauth_register(request):
    required_keys = {"username"}
    request_keys = set(request.keys())

    if required_keys == request_keys:
        return True
    return False