import re

import json

class Common:    
    def __init__(self, runMode:str="Production"):        
        self.mode = runMode    

    def replace_keys_with_values(self,input_text:str, key_value_pairs: dict[str, str]):
        """Replaces keys enclosed within '%' in the input string with values from the key_value_pairs dictionary.

        Args:
            input_text (str): The input string to process.
            key_value_pairs (dict): A dictionary of key/value pairs for replacement.

        Returns:
            str: The modified string with keys replaced with values.
        """

        regex = r"%(\w+)%"  # Match keys enclosed in %
        pattern = re.compile(regex)

        def replacer(match):
            key = match.group(1)
            return key_value_pairs.get(key, match.group(0))  # Return value or original key if not found

        return pattern.sub(replacer, input_text)

    def print(self, msg: str):
        if(self.mode != "Production"):
            print(msg)
            
    def getConfig(self, file_to_load: str = None):    
        obj:object = None
        if not file_to_load:
            return None
        with open(file_to_load, "r") as f:
            obj = json.load(f)  # Load the JSON array
        return obj