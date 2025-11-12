from fastapi import FastAPI, HTTPException

from fastapi.responses import JSONResponse
import requests
import security_middleware
import tokenManagement
import schemaManagement
from helperFunctions import Common
import os

from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


app.middleware("http")(security_middleware.doWork)
security_middleware.force200onException = True
security_middleware.configFile = "configs/security_config.json"

hf = Common("Development")
token = tokenManagement.Token(hf, os.getenv("SIERRA_URL"),os.getenv("DEFAULT_USER"),os.getenv("DEFAULT_PASSWORD"))
schemas = schemaManagement.Schemas(hf)

security_middleware.hf = hf

def __executeAPI__(objName: str, queryName: str, replacements: dict[str, str], base_url: str):   
    try :
        (url, qtype, body, qSuccessCode) = schemas.getPreparedAPIQuery(objName, queryName, replacements)
        match base_url:           
            case "sierra":        
                base_url =  os.getenv("SIERRA_URL") + "/" + url
            case _:
                base_url =  os.getenv("SIERRA_URL") + "/" + url
        
        if(qtype in ["POST","PUT"]):              
            response = requests.post(url, data=body, headers=token.getSecureHeader(),verify=False)
        else:
            response = requests.get(url, headers=token.getSecureHeader(), verify=False)
        return((response.status_code == qSuccessCode), response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
def getx():    
    return "Runnng..."
        
@app.get("/{base_url}/{qry_object}/{qry_name}")        
async def apiQuery(base_url:str, qry_object:str, qry_name: str, barcode:str = None, email:str = None, telephone:str = None, mobile:str= None, qid:str = None, id:str = None):
    params = {}
    objs = []    
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
                    
                return JSONResponse(runQuery(qry_object, qry_name, params, base_url))
            case _:
                raise HTTPException(status_code=404, detail="Unknown Query Name")
    except HTTPException as e:
        if(security_middleware.force200onException):
            return JSONResponse(content={"error": e.detail , "status_code": e.status_code})
        else:
            return JSONResponse(content={"error": e.detail }, status_code=e.status_code)
        
def runQuery(qry_object:str, qry_name:str, params:str, base_url:str):            
    objs = []
    try:
        (success,response) = __executeAPI__(qry_object,qry_name, params, base_url)        
        response.raise_for_status()  # Raise an exception for error status codes            
        data = response.json()
        if data['total'] > 0:
            for entry in data['entries']:                
                _,response = __executeAPI__("patron", "findByID", {"id": entry['link'].split("/")[-1] })
                response.raise_for_status
                objs.append(schemas.populateObject("patron",response.json()))
        return objs
    except Exception as e:        
        raise HTTPException(status_code=e.status_code, detail=e.detail)        