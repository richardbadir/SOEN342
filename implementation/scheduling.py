from datetime import datetime, timedelta
from typing import List
from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://richard:hello123@cluster0.ohtoh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection

db = client['Organizations']
timeSlot = db['TimeSlots'] 
spaces = db['Spaces'] 

class TimeSlot:
    def __init__(self, start: datetime, end: datetime, id):
        self.booked: bool = False
        self.start: datetime = start
        self.end: datetime = end
        self.id=id
    def is_valid_slot(self, start, duration) -> bool:
        # Check if the time slot is available
        if (self.start <= start and  self.end >= start+ timedelta(minutes=duration)):
            timeSlot.update_one(
                {"_id": ObjectId(self.id)},
                {"$set": {"available": False}}
                )
            return True
        return False

class City:
    def __init__(self, name: str):
        self.name: str = name

class Space:
    def __init__(self, space_type: str, address: str, city: City):
        self.type: str = space_type
        self.address: str = address
        self.city: City = city
        self.availabilities: List[TimeSlot] = []
        self.id=None
        if not spaces.find_one({"address":address, "city": city.id}):
            result=spaces.insert_one({"address":address, "city": city.id})
            self.id=result.inserted_id
        else:
            result=spaces.find_one({"address":address, "city": city.id})
            self.id=result.get('_id')
    
    def hasAvailableTimeslot(self,startTime,TypicalDuration, space):
        time_slots=timeSlot.find({"space":space.id, "available": True})
        
        for ts in time_slots:
            Timeslot= TimeSlot(ts['start'], ts['end'], ts.get('_id'))
            if Timeslot.is_valid_slot(startTime, TypicalDuration):
                return Timeslot
        return False


    

    def add_availability(self, time_slot: TimeSlot):
        self.availabilities.append(time_slot)

class Owned(Space):
    def __init__(self, space_type: str, address: str, city: City, organization: 'Organization'):
        super().__init__(space_type, address, city)
        self.organization: 'Organization' = organization

class Rented(Space):
    def __init__(self, space_type: str, address: str, city: City, rental_cost: float):
        super().__init__(space_type, address, city)
        self.rental_cost: float = rental_cost

class Organization:
    def __init__(self, name: str):
        self.name: str = name
        self.owned_spaces: List[Owned] = []

    def add_owned_space(self, space: Owned):
        self.owned_spaces.append(space)