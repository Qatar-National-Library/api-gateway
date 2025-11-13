from fastapi import FastAPI, HTTPException

from fastapi.responses import JSONResponse
import requests
import security_middleware
import tokenManagement
import schemaManagement
from helperFunctions import Common
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()

load_dotenv()
app = FastAPI()

app.middleware("http")(security_middleware.doWork)
security_middleware.force200onException = True
security_middleware.configFile = "configs/security_config.json"

hf = Common("Development")
token = tokenManagement.Token(hf, os.getenv("SIERRA_URL"),os.getenv("DEFAULT_USER"),os.getenv("DEFAULT_PASSWORD"))
schemas = schemaManagement.Schemas(hf)
base_url =  os.getenv("SIERRA_URL")
security_middleware.hf = hf

def __executeAPI__(objName: str, queryName: str, replacements: dict[str, str], source: str):       
    try :
        (url, qtype, body, qSuccessCode) = schemas.getPreparedAPIQuery(objName, queryName, replacements)
        match source.lower():           
            case "sierra":        
                url =  base_url + "/" + url
            case _:
                url =  base_url + "/" + url
        
        if(qtype in ["POST", "PUT"]):              
            response = requests.post(url, data=body, headers=token.getSecureHeader(),verify=False)
            hf.log("INFO",f"POST | {url} | {body} | STATUS: {response.status_code}")
        else:            
            response = requests.get(url, headers=token.getSecureHeader(), verify=False)
            hf.log("INFO",f"GET | {url} | {body} | STATUS: {response.status_code}")
        return((response.status_code == qSuccessCode), response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
def getx():    
    resp = []
    resp["healthcheck"] = "ok"
    return JSONResponse(resp)
        
@app.get("/{base_object}/{qry_object}/{qry_name}")        
async def apiQuery(base_object:str, qry_object:str, qry_name: str, barcode:str = None, email:str = None, telephone:str = None, mobile:str= None, qid:str = None, id:str = None):
    params = {}      
    try:
        match qry_name:
            case "find":    
                if(id):
                    qry_name= "findByID"
                    params = { "id": id }            
                if(barcode):
                    qry_name = "findByBarcode"
                    params = { "barcode": barcode }
                
                if(email):
                    qry_name = "findByEmail"
                    params = { "email": email }
                
                if(telephone):
                    qry_name = "findByTelephone"
                    params = { "telephone": telephone }
                
                if(mobile):
                    qry_name = "findByMobile"
                    params = { "mobile": mobile }
                
                if(qid):
                    qry_name = "findByQID"
                    params = { "qid": qid}
                    
                return JSONResponse(runQuery(qry_object, qry_name, params, base_object))
            case _:
                raise HTTPException(status_code=404, detail="Unknown Query Name")
    except HTTPException as e:
        if(security_middleware.force200onException):
            return JSONResponse(content={"error": e.detail , "status_code": e.status_code})
        else:
            return JSONResponse(content={"error": e.detail }, status_code=e.status_code)
        
def runQuery(qry_object:str, qry_name:str, params, base_object:str):            
    objs = []
    
    try:
        (success,response) = __executeAPI__(qry_object, qry_name, params, base_object)        
        response.raise_for_status()  # Raise an exception for error status codes            
        data = response.json()
        if data['total'] > 0:
            for entry in data['entries']:                
                _,response = __executeAPI__("patron", "findByID", {"id": entry['link'].split("/")[-1] }, base_object)
                response.raise_for_status
                objs.append(schemas.populateObject("patron",response.json()))
        return objs
    except Exception as e:        
        raise HTTPException(status_code=500, detail="Error executing query: " + str(e))        