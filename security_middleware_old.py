from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from typing import List
    
class Config(BaseModel):    
    api_key: str = None
    client_name: str = None
    allowed_paths: List[str]  = [] 
    
configFile:str = None
hf:object = None
force200onException: bool = False
config:object = None
   
def __isSecurePathAllowed__(path: str, clientName: str, apiKey: str):   
    for pth in config.allowed_paths:
        if((path == pth) and (config.client_name == clientName) and (apiKey == config.api_key)):
            return True
    return False

async def doWork(request: Request, call_next):
    response = None                
    try:
        hf.print("In security_middleware...")
        if(not config):
            c = hf.getConfig(configFile)
            config = Config(**c)
            
        if(request.url.path in config.allowed_paths):
            hf.print("Running security_middleware...")        
            api_key = request.query_params.get("apikey")
            header_apikey = request.headers.get("apikey")    
            client_name = request.query_params.get("apiclient")
            header_client = request.headers.get("apiclient")    

            if(header_apikey):
                api_key = header_apikey
                
            if(header_client):
                client_name = header_client
            
            if(not api_key):
                raise HTTPException(status_code=403, detail="API Key not found")
            
            if(not client_name):
                raise HTTPException(status_code=403, detail="Client Name not found")
                           
            if(__isSecurePathAllowed__(request.url.path,client_name,api_key)):  
                hf.print("Path is allowed...")
                response = await call_next(request)
            else:
                raise HTTPException(status_code=403, detail="Access Denied")
        else:
            hf.print("Skipping securty_middleware for path: " + request.url.path)
            response = await call_next(request)
    except HTTPException as e:
        if(force200onException):
            response =  JSONResponse(content={"error": e.detail , "status_code": e.status_code})
        else:
            response =  JSONResponse(content={"error": e.detail , "status_code": e.status_code},status_code=e.status_code)
    return response
        