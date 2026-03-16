
import datetime
from datetime import date

class JSONSerializer:
    @staticmethod
    def serializeObject(obj):
        if isinstance(obj,dict): #si el objeto es un diccionario, lo devolvemos tal cual
            result = {}
            for key,value in obj.items():
                result[key] = JSONSerializer.serializeObject(value)
            return result
        if isinstance(obj,list):  #si el objeto es una lista, aplicamos la función a cada elemento de la lista
            for i in range(len(obj)):
                obj[i] = JSONSerializer.serializeObject(obj[i])
            return obj
        
        if obj is None:
            return None
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):#si el objeto tiene un atributo __dict__, lo convertimos a un diccionar
            return JSONSerializer.serializeObject(obj.__dict__)
        
      
        return obj
    
    @staticmethod
    def serializeList(items):
        result = []
        if items is None:
            return []
        if not isinstance(items, list):
            raise TypeError("serializeList espera una lista")
        for item in items:
            result.append(JSONSerializer.serializeObject(item))
        return result