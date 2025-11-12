from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from typing import List, Optional

class PathConfig(BaseModel):
    api_key: Optional[str] = None
    client_name: Optional[str] = None
    allowed_paths: List[str] = Field(default_factory=list)

class Config(BaseModel):
    configs: List[PathConfig]

configFile: str = ""
hf: object = None
force200onException: bool = False
config: Config = None
logging.basicConfig(filename="log.log",encoding="utf-8",filemode="a",format="{asctime} - {levelname} - {message}",style="{",datefmt="%Y-%m-%d %H:%M",)

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
        
        hf.print("Running security_middleware...")        
                
        api_key = request.headers.get("apikey") if request.headers.get("apikey") else request.query_params.get("apikey")        
        client_name = request.headers.get("apiclient") if request.headers.get("apiclient") else request.query_params.get("apiclient")
       
        hf.print(f"Client Name: {client_name}, API Key: {api_key}, Path: {request.url.path}")
        
        logging.info(f"{request.url.path} {request.method} - {client_name}/{api_key}")
        
        if(request.method in ["PUT","POST"]):
            logging.info(f"Body: {request.body}")
        else:
            logging.info(f"Params: {request.query_params}")
        
        if __isSecurePathAllowed__(request.url.path, client_name, api_key):
            if hf:
                hf.print("Path is allowed...")                                
            response = await call_next(request)
        else:                        
            raise HTTPException(status_code=403, detail="Access Denied")    
        response = await call_next(request)
    except HTTPException as e:
        # return 200 when force200onException is set, otherwise use original status
        if force200onException:
            response = JSONResponse(content={"error": e.detail, "status_code": e.status_code})
            logging.info("Reject: 200 | forced200")
        else:
            response = JSONResponse(content={"error": e.detail, "status_code": e.status_code}, status_code=e.status_code)
            logging.info(f"Reject: {e.status_code} | {e.detail}")
    return response