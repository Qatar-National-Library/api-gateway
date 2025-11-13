from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from helperFunctions import Common

class PathConfig(BaseModel):
    api_key: Optional[str] = None
    client_name: Optional[str] = None
    allowed_paths: List[str] = Field(default_factory=list)

class Config(BaseModel):
    configs: List[PathConfig]

configFile: str = ""
hf: Common = None
force200onException: bool = False
config: Config = None



def __isSecurePathAllowed__(path: str, clientName: Optional[str], apiKey: Optional[str]) -> bool:
    global config
    ret = False
    for pc in config.configs:          
        if(path in pc.allowed_paths) and (pc.client_name == clientName) and (pc.api_key == apiKey):
            ret = ret or True
            
        if(path in pc.allowed_paths) and ((pc.client_name != clientName) or (pc.api_key != apiKey)):
            ret = ret or False
        
    return ret

async def doWork(request: Request, call_next):
    global config, hf, configFile, force200onException
    response = None
    try:        
        
        if not config:            
            c = hf.getConfig(configFile)
            config = Config(**c)        
                
        api_key = request.headers.get("apikey") if request.headers.get("apikey") else request.query_params.get("apikey")        
        client_name = request.headers.get("apiclient") if request.headers.get("apiclient") else request.query_params.get("apiclient")
       
        if __isSecurePathAllowed__(request.url.path, client_name, api_key):            
            if(request.method in ["PUT","POST"]):
                hf.log("DEBUG",f"ACCESS REQUEST | {request.method} | {client_name} / {api_key} | {request.url.path} | {request.body}")
            else:
                hf.log("DEBUG",f"ACCESS REQUEST | {request.method} | {client_name} / {api_key} | {request.url.path} | {request.query_params}")
            response = await call_next(request)
        else:            
            hf.log("DEBUG",f"PATH ERROR | {request.method} | {client_name} / {api_key} | {request.url.path} | {request.body}")        
            raise HTTPException(status_code=403, detail="Access Denied")    
        #response = await call_next(request)
    except HTTPException as e:
        # return 200 when force200onException is set, otherwise use original status
        if force200onException:
            response = JSONResponse(content={"error": e.detail, "status_code": e.status_code})
            hf.log("DEBUG",f"SERVER EXCEPTION - FORCE200 | {request.method} | {client_name} / {api_key} | {request.url.path} | {request.body}")
        else:
            response = JSONResponse(content={"error": e.detail, "status_code": e.status_code}, status_code=e.status_code)
            hf.log("DEBUG",f"SERVER EXCEPTION | {request.method} | {client_name} / {api_key} | {request.url.path} | {request.body}")
    return response