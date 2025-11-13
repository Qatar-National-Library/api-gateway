import re
import logging
import json

class Common:    
    def __init__(self, runMode:str="Production"):        
        self.mode = runMode        
        self.logger = logging.getLogger('appLogger')
        self.logger.setLevel(logging.DEBUG)
        
        if(self.mode.lower() != "production"):
            screenlogger = logging.StreamHandler()
            screenlogger.setFormatter(logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S"))
            screenlogger.setLevel(logging.DEBUG)        
            self.logger.addHandler(screenlogger)
        else:
            debuglogger = logging.FileHandler("debug.log", mode='a', encoding='utf-8')
            debuglogger.setFormatter(logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S"))
            debuglogger.setLevel(logging.DEBUG)
            
            basiclogger = logging.FileHandler("log.log", mode='a', encoding='utf-8')
            basiclogger.setFormatter(logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S"))
            basiclogger.setLevel(logging.INFO)    
            
            self.logger.addHandler(debuglogger)
            self.logger.addHandler(basiclogger)
        

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
            
    def getConfig(self, file_to_load: str = None):    
        obj:object = None
        if not file_to_load:
            return None
        with open(file_to_load, "r") as f:
            obj = json.load(f)  # Load the JSON array
        return obj
    
    def log(self, log_level: str =  "INFO", msg: str = ""):
        match log_level.upper():
            case "DEBUG":
                self.logger.debug(msg)
            case "INFO":
                self.logger.info(msg)
            case "WARNING":
                self.logger.warning(msg)
            case "ERROR":
                self.logger.error(msg)
            case "CRITICAL":
                self.logger.critical(msg)
        