from pydantic import BaseModel
from typing import List
import json
import os
import glob
from helperFunctions import Common

class SchemaField(BaseModel):
    name: str = None
    validators: str = None
    jsonReadBack: str = None

class SchemaQuery(BaseModel):
    name: str = None
    type: str = None
    urlSuffix: str = None
    template: str = None
    successCode: int = None

class Schema(BaseModel):
    fields: List[SchemaField] = None
    queries: List[SchemaQuery] = None
    
class Schemas:
    def __init__(self,  helperFunctions: Common, objectConfigFileDirectory:str = "./schemas/"):
        self.hf = helperFunctions
        self.schemas = dict[str, Schema]()        
        for filep in glob.glob(os.path.join(objectConfigFileDirectory,"*.json")):        
            objName = os.path.basename(filep)
            
            if "." in objName:
                objName, _ = objName.split(".")
            
            objName = objName.lower().replace(" ", "")
            with open(filep, "r") as f:                
                self.schemas[objName] = Schema(**json.load(f))  # Load the JSON array        
        
    
    def getQuery(self, objName:str, queryName:str):
        for query in self.schemas[objName.lower()].queries:
            if query.name == queryName:
                return query
        return None

    def populateObject(self, objName: str, inputJson):
        obj = dict[str,str]()
        data = inputJson        
        for fld in self.schemas[objName].fields:                        
            cmd = "{}['{}']={}".format("obj",fld.name,fld.jsonReadBack)
            try:
                exec(cmd)
            except Exception as e:
                obj[fld.name] = ""
        return obj 

    def getPreparedAPIQuery(self, objName:str, queryName:str, replacements: dict[str, str]):
        query = self.getQuery(objName, queryName)
        if(query == None):
            raise Exception("Query {} not found".format(queryName))
        url =  self.hf.replace_keys_with_values(query.urlSuffix, replacements)
        qtype = query.type
        qSuccessCode = query.successCode
        body = None    
        if(query.type in ["POST","PUT"]):
            body = self.hf.replace_keys_with_values(query.template, replacements)                           
        return(url, qtype, body, qSuccessCode)