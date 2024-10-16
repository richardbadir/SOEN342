import pymongo
from datetime import datetime, timedelta
from bson import ObjectId

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["lesson_booking_system"]

class LessonType:
    def __init__(self, activity, duration):
        self.activity = activity
        self.duration = duration

    def get_typical_duration(self):
        return self.duration

class Offering:
    def __init__(self, activity, availability, public, status, lesson_type):
        self.availability = availability
        self.public = public
        self.status = status
        self.lesson_type = lesson_type

class PrivateLesson(Offering):
    def __init__(self, activity, availability, public, status, lesson_type):
        super().__init__(activity, availability, public, status, lesson_type)
        self.type = "private"

class GroupLesson(Offering):
    def __init__(self, activity, availability, public, status, lesson_type, max_participants):
        super().__init__(activity, availability, public, status, lesson_type)
        self.type = "group"
        self.max_participants = max_participants

class Instructor:
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

class Administrator:
    def create_offering(self, lesson_type, start_time, location, mode):
        offering = {
            "lesson_type": lesson_type,
            "start_time": start_time,
            "location": location,
            "mode": mode,
            "availability": True,
            "status": "available"
        }
        result = db.offerings.insert_one(offering)
        return str(result.inserted_id)

    def make_offering_public(self, offering_id):
        result = db.offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"public": True}}
        )
        return result.modified_count > 0

class Console:
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

def main():
    admin = Administrator()
    instructor = Instructor("Yoga", "John Doe", "123-456-7890")
    console = Console()

    while True:
        print("\n1. Create Offering (Admin)")
        print("2. View Available Offerings (Instructor)")
        print("3. Take Offering (Instructor)")
        print("4. Make Offering Public (Admin)")
        print("5. Exit")
        
        choice = input("Enter your choice: ")

        if choice == "1":
            lesson_type = input("Enter lesson type: ")
            start_time = datetime.now() + timedelta(days=1)
            location = input("Enter location: ")
            mode = input("Enter p for private or g for group: ")
            offering_id = admin.create_offering(lesson_type, start_time, location, mode)
            print(f"Offering created with ID: {offering_id}")

        elif choice == "2":
            offerings = instructor.view_available_offerings()
            for offering in offerings:
                print(f"ID: {offering['_id']}, Type: {offering['lesson_type']}, Location: {offering['location']}")

        elif choice == "3":
            offering_id = input("Enter offering ID to take: ")
            if instructor.take_offering(offering_id):
                print("Offering taken successfully")
            else:
                print("Failed to take offering")

        elif choice == "4":
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