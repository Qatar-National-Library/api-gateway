from datetime import datetime,timedelta
import base64
import requests
from pydantic import BaseModel
from helperFunctions import Common

class Token:
    def __init__(self, helperFunctions: Common, baseURL:str, user:str, passwd:str):
        self.token:str = ""
        self.token_death:datetime = datetime.now()
        self.token_type:str = ""  
        self.token_baseURL: str = baseURL
        self.token_user: str = user
        self.token_password:str = passwd
        self.hf = helperFunctions
    
    def renewToken(self):        
        if(self.token_death < datetime.now()):
            
            url = "{}/token".format(self.token_baseURL) #"https://library.qnl.qa:443/iii/sierra-api/v6/token"
            userpass = "{}:{}".format(self.token_user,self.token_password) #g5orCpSXbHJT9srOUEfcWOQdzJba:2S3fkjsdfD!"
        
            encoded_bytes = base64.b64encode(userpass.encode("utf-8"))
            headers = {
                "Authorization": "Basic {}".format(encoded_bytes.decode("utf-8")),
                "Content-Type" : "application/x-www-form-urlencoded"        
            }            
            response = requests.post(url, headers=headers, data="grant_type=client_credentials",verify=False)    
            response.raise_for_status()  # Raise an exception for error status codes
            data = response.json()              
            self.token=data["access_token"]
            self.token_death=datetime.now() + timedelta(seconds=data["expires_in"])
            self.token_type=data["token_type"]
            self.hf.log("DEBUG", f"NEW TOKEN | {self.token} | {self.token_death}")
        else:
            self.hf.log("DEBUG", f"TOKEN | {self.token} | {self.token_death}") 

    def getSecureHeader(self):
        self.renewToken()
        return { "Authorization" : "{} {}".format(self.token_type,self.token) }    