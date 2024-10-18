from datetime import datetime, timedelta
from bson import ObjectId
from scheduling import *
from abc import ABC, abstractmethod
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://richard:hello123@cluster0.ohtoh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
except Exception as e:
    print("Error with MongoDB connection.")
    print(e)
db = client['Organizations']
organizations = db['Organizations'] 
offerings = db['Offerings'] 
spaces = db['Spaces'] 
cities = db['City'] 
instructors = db['Instructors'] 
lessonType = db['LessonType'] 


class LessonType:
    def __init__(self, activity):
        self.activity = activity
        if not lessonType.find_one({"activity":activity}):
            lessonType.insert_one({"activity":activity})

    def get_typical_duration(self):
        document=lessonType.find_one({"activity":self.activity})
        self.duration=document.duration
        return self.duration

class Offering(ABC):
    def __init__(self, availability, public, status, lesson_type):
        self.availability = availability
        self.public = public
        self.status = status
        self.lesson_type = lesson_type
    def add(self, start_time, duration, space,lesson,mode):
        
        result=offerings.insert_one({"availability":self.availability,"startTime": start_time, "duration": duration,"public":self.public, "status":self.status, "location":space,"lessonType":lesson, "mode":mode})
        return str(result.inserted_id)
    
class Writer(ABC):
    #def __new__(cls, *args, **kwargs):
        #if not cls._instance:
            #cls._instance = super(Writer, cls).__new__(cls, *args, **kwargs)
        #return cls._instance
    pass
class Reader():
    def view_offerings():
        return offerings.find({})


class PrivateLesson(Offering):
    def __init__(self,  availability, public, status, lesson_type):
        super().__init__( availability, public, status, lesson_type)
        self.type = "private"

class GroupLesson(Offering):
    def __init__(self,  availability, public, status, lesson_type, max_participants):
        super().__init__( availability, public, status, lesson_type)
        self.type = "group"
        self.max_participants = max_participants

class Instructor(Writer):
    def __init__(self, specialization, name, phone_number):
        self.specialization = specialization
        self.name = name
        self.phone_number = phone_number

    def view_available_offerings(self):
        offerings = offerings.find({"availability": True, "status": "available"})
        return list(offerings)

    def take_offering(self, offering_id):
        result = offerings.update_one(
            {"_id": ObjectId(offering_id), "status": "available"},
            {"$set": {"status": "taken", "instructor_phone": self.phone_number}}
        )
        if result.modified_count > 0:
            return True
        return False

class Administrator(Writer):
    def __init__(self) -> None:
        self.console=Console()
        self.console.hasWriter=True

    def make_offering_public(self, offering_id):
        result = offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"public": True}}
        )
        return result.modified_count > 0

class City():
    def __init__(self, city) -> None:
        self.id= None
        if not cities.find_one({"name":city}):
            result=cities.insert_one({"name":city})
            self.id=result.inserted_id
        else:
            result=cities.find_one({"name":city})
            self.id=result.get('_id')



class Console:
    hasWriter=False
    hasReader=False
    _instance = None
    def create_offering(self, lesson_type, start_time, location, city, mode):
        lesson=LessonType(lesson_type)
        duration = lesson.get_typical_duration(start_time,duration)
        
        c = City(city)
        space=Space(lesson_type, location, city)
        if space.hasAvailableTimeslot(start_time, duration):
            if mode=="p":
                offering=PrivateLesson(lesson,True,False,"available")
            else:
                offering=GroupLesson(lesson,True,False,"available", 0)
            offering.add(start_time, duration, space.id, lesson.id, mode)

        else:
            print("No available time slot at that location, for that activity and at that time.")
            return
        
        offering={
            "lessonType":lesson_type,
            "startTime": start_time,
            "location": location,
            "mode": mode
        } 
        

        result = offerings.insert_one(offering)
        return str(result.inserted_id)
    def get_active_offerings(self):
        offerings = offerings.find({"status": "available"})
        return list(offerings)

    def find_offering(self, offering_id):
        offering = offerings.find_one({"_id": ObjectId(offering_id)})
        return offering

    def set_status(self, offering_id, status):
        result = offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Console, cls).__new__(cls, *args, **kwargs)
        return cls._instance

def main():
    
    instructor = Instructor("Yoga", "John Doe", "123-456-7890")
    console = Console()

    while True:
        if console.hasWriter:
            console.log("Writer already present")
            break
        
        print("\n1. Create Offering (Admin)")
        print("2. View Available Offerings (Instructor)")
        print("3. Take Offering (Instructor)")
        print("4. Make Offering Public (Admin)")
        print("5. Exit")
        
        choice = input("Enter your choice: ")

        
        if choice == "1":
            if console.hasReader:
                console.log("Reader(s) already present")
                continue
            admin = Administrator()
            lesson_type = input("Enter lesson type: ")
            start_time = input("Enter a start time in format yyyy-mm-ddThh:mm")
            city= input("Enter a city: ")
            location = input("Enter address: ")
            mode = input("Enter p for private or g for group mode: ")
            while mode!="g" and mode!="p":
                print("Invalid mode selected")
                mode = input("Enter p for private or g for group mode: ")
            offering_id = admin.console.create_offering(lesson_type, start_time, location, city, mode)
            print(f"Offering created with ID: {offering_id}")

        elif choice == "2":
            offerings = instructor.view_available_offerings()
            for offering in offerings:
                print(f"ID: {offering['_id']}, Type: {offering['lesson_type']}, Location: {offering['location']}")

        elif choice == "3":
            if console.hasReader:
                console.log("Reader(s) already present")
                continue
            offering_id = input("Enter offering ID to take: ")
            if instructor.take_offering(offering_id):
                print("Offering taken successfully")
            else:
                print("Failed to take offering")

        elif choice == "4":
            if console.hasReader:
                console.log("Reader(s) already present")
                continue
            offering_id = input("Enter offering ID to make public: ")
            if admin.make_offering_public(offering_id):
                print("Offering made public successfully")
            else:
                print("Failed to make offering public")

        elif choice == "5":
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()