
class Resource:
  def __init__(self,id,name,service,region,date):
    self.id = id
    self.name = name
    self.service = service
    self.region = region
    if date is None:
      self.date = None
    elif hasattr(date, 'isoformat'):
      self.date = date.isoformat()
    else:
      self.date = date
    

  def get_id(self):
    return self.id
  
  def get_name(self):
    return self.name
  def get_service(self):
    return self.service
  def get_region(self):
    return self.region
  def get_date(self):
    return self.date
  
    

    

  
  