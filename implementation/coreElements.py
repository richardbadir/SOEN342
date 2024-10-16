import pymongo
from datetime import datetime, timedelta
from bson import ObjectId
from scheduling import *
from abc import ABC, abstractmethod

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["lesson_booking_system"]

class LessonType:
    def __init__(self, activity):
        self.activity = activity

    def get_typical_duration(self):
        self.duration=db.lessons.find_one("activity", self.activity)
        return self.duration

class Offering(ABC):
    def __init__(self, availability, public, status, lesson_type):
        self.availability = availability
        self.public = public
        self.status = status
        self.lesson_type = lesson_type
    def add():
        #add to mongoDB
        pass
class Writer(ABC):
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Writer, cls).__new__(cls, *args, **kwargs)
        return cls._instance
class Reader():
    def view_offerings():
        pass


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
        offerings = db.offerings.find({"availability": True, "status": "available"})
        return list(offerings)

    def take_offering(self, offering_id):
        result = db.offerings.update_one(
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
        result = db.offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"public": True}}
        )
        return result.modified_count > 0

class Console:
    hasWriter=False
    hasReader=False
    _instance = None
    def create_offering(self, lesson_type, start_time, location, mode):
        lesson=LessonType(lesson_type)
        duration = lesson.get_typical_duration(start_time,duration)
        space=Space(location)
        if space.hasAvailableTimeslot(start_time, duration):
            if mode=="p":
                offering=PrivateLesson(lesson,True,False,"available")
            else:
                offering=GroupLesson(lesson,True,False,"available", 0)
            offering.add()

        else:
            print("No available time slot at that location, for that activity and at that time.")
        offering={
            "test":"test"
        } 
        

        result = db.offerings.insert_one(offering)
        return str(result.inserted_id)
    def get_active_offerings(self):
        offerings = db.offerings.find({"status": "available"})
        return list(offerings)

    def find_offering(self, offering_id):
        offering = db.offerings.find_one({"_id": ObjectId(offering_id)})
        return offering

    def set_status(self, offering_id, status):
        result = db.offerings.update_one(
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
            start_time = input("Enter a start time in format hh:mm")
            location = input("Enter location: ")
            mode = input("Enter p for private or g for group mode: ")
            while mode!="g" and mode!="p":
                print("Invalid mode selected")
                mode = input("Enter p for private or g for group mode: ")
            offering_id = admin.console.create_offering(lesson_type, start_time, location, mode)
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