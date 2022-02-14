import re
from datetime import datetime

def isValidEmail(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def isRequiredFiled(value):
    if value == "":
        return False
    return True

def isValidPhone(number):
    regex = r'\b[0-9]{10}\b'
    if(re.fullmatch(regex, number)):
        return True
    else:
        return False

def isValidID(id):
    pat = re.compile(r"[A-Za-z0-9]+") # calling fullmatch function by passing pattern and n
    if re.fullmatch(pat, id):
        return True
    else:
        return False

def isValidDate(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False

def isValidDateTime(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S'):
            raise ValueError
        return True
    except ValueError:
        return False

def isValidInteger(value):
    return value.isnumeric()

def isValidString(value):
    if type(value) == int:
        return False
    else:
        return True

def isValidPassword(password): 
    if (len(password)<8):
        return False       
    elif not re.search("[a-z]", password):
        return False
    elif not re.search("[A-Z]", password):
        return False
    elif not re.search("[0-9]", password):
        return False
    elif re.search("\s", password):
        return False
    else:
        return True

def isValidUsername(username):
    if (len(username)<8):
        return False
    if not username.isalpha():
        return False

    if not any(x.isupper() for x in username):
        return False

    return True








