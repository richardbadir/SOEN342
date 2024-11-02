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
customers = db['Customers']
bookings = db['Bookings'] 

class Organization:
    def __init__(self, name):
        self.name = name
        self.id= None
        if not organizations.find_one({"name":name}):
            result = organizations.insert_one({"name":name})
            self.id=result.inserted_id
        else:
            result=organizations.find_one({"name":name})
            self.id=result.get('_id')

class LessonType:
    def __init__(self, activity):
        self.activity = activity
        self.id= None
        if not lessonType.find_one({"activity":activity}):
            result = lessonType.insert_one({"activity":activity})
            self.id=result.inserted_id
        else:
            result=lessonType.find_one({"activity":activity})
            self.id=result.get('_id')

    def get_typical_duration(self):
        document=lessonType.find_one({"activity":self.activity})
        self.duration=document['duration']
        return self.duration

class Offering(ABC):
    def __init__(self, availability, public, status, lesson_type, id=None):
        self.availability = availability
        self.public = public
        self.status = status
        self.lesson_type = lesson_type
        self.id=id
    def add(self, start_time, duration, space,lesson,mode, organization):
        if mode=="g":
            result=offerings.insert_one({"availability":self.availability,"startTime": start_time, "duration": duration,"public":self.public, "status":self.status, "location":space,"lessonType":lesson, "mode":mode, "organization": organization, "places": 10})
            return str(result.inserted_id)
        else:
            result=offerings.insert_one({"availability":self.availability,"startTime": start_time, "duration": duration,"public":self.public, "status":self.status, "location":space,"lessonType":lesson, "mode":mode, "organization": organization})
            return str(result.inserted_id)
    def checkAvailability(self):
        return self.availability
    
    def getOfferingMode(self):
        result= offerings.find_one({"_id":ObjectId(self.id)})
        return result['mode']
    
    def updateStatus(self, status):
        if status=="booked":
            offerings.update_one( {"_id": ObjectId(self.id)},
            {"$set": {"availability": False}})
    
    def decreaseAvailableSpots(self):
        
        result= offerings.find_one({"_id": ObjectId(self.id)})
        spots= result['places']
        offerings.update_one( {"_id": ObjectId(self.id)},
            {"$set": {"places": spots-1}})
        if spots-1<=0:
            self.updateStatus("booked")

    
class Writer(ABC):
    #def __new__(cls, *args, **kwargs):
        #if not cls._instance:
            #cls._instance = super(Writer, cls).__new__(cls, *args, **kwargs)
        #return cls._instance
    pass
class Reader():
    def view_offerings(self):
        offs=offerings.find({"public":True})
        ofs=[]
        for o in offs:
            offer={}
            for element in o.keys():
                if element=='location':
                    location=spaces.find_one({"_id": o[element]})
                    offer[element]=location
                elif element=='lessonType':
                    lesson=lessonType.find_one({"_id": o[element]})
                    offer[element]=lesson
                elif element=='organization':
                    organization=organizations.find_one({"_id": o[element]})
                    offer[element]=organization
                else:
                    offer[element]=o[element]
            ofs.append(offer)
        print(ofs)



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
        self.console=Console()
        self.console.hasReader=True

        if not instructors.find_one({"name":name}):
            result = organizations.insert_one({"name":name, "phoneNumber": phone_number, "Specialization": specialization})
            self.id=result.inserted_id
        else:
            result=instructors.find_one({"name":name})
            self.id=result.get('_id')

    def viewAvailableOfferings(self):
        offers = offerings.find({"availability": True, "status": "available"})
        listOfferings = []
        for offering in offers:
            listOfferings.append(self.console.getActiveOfferings(offering))
        print(listOfferings)
        self.console.hasReader=False

    def takeOffering(self, offering_id):
        result = offerings.update_one(
            {"_id": ObjectId(offering_id), "status": "available"},
            {"$set": {"status": "taken", "instructor_phone": self.phone_number}}
        )
        off=self.console.find_offering(offering_id)
        self.console.setStatus(offering_id, 'taken')
        self.console.makeOfferingPublic(offering_id)
        self.console.hasReader=False
        self.console.hasWriter=False
        if result.modified_count > 0:
            return True
        return False

class Administrator(Writer):
    def __init__(self) -> None:
        self.console=Console()
        self.console.hasWriter=True

    def make_offering_public(self, offering_id):
        print(offering_id)
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
    def create_offering(self, lesson_type, start_time, location, city, mode, organization):
        lesson=LessonType(lesson_type)
        org=Organization(organization)
        duration = lesson.get_typical_duration()
        c = City(city)
        space=Space(lesson_type, location, c)
        if space.hasAvailableTimeslot(start_time, duration, space):
            if mode=="p":
                offering=PrivateLesson(True,False,"available", lesson.id)
            else:
                offering=GroupLesson(True,False,"available", lesson.id, 20)
            id=offering.add(start_time, duration, space.id, lesson.id, mode, org.id)
            print("Inserted Offering with id "+id)

        else:
            print("No available time slot at that location for that time.")
        self.hasWriter=False
        

    def getActiveOfferings(self, offering):
        offer={}
        for element in offering.keys():
            if element=='location':
                location=spaces.find_one({"_id": offering[element]})
                offer[element]=location
            elif element=='lessonType':
                lesson=lessonType.find_one({"_id": offering[element]})
                offer[element]=lesson
            elif element=='organization':
                organization=organizations.find_one({"_id": offering[element]})
                offer[element]=organization
            else:
                offer[element]=offering[element]
        return offer

    def find_offering(self, offering_id):
        offering = offerings.find_one({"_id": ObjectId(offering_id)})
        return offering

    def setStatus(self, offering_id, status):
        result = offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    def makeOfferingPublic(self, offering_id):
         offerings.update_one(
            {"_id": ObjectId(offering_id)},
            {"$set": {"public": True}}
        )
         
    
    def createBooking(self, offering, clientName, underageName, age):
        
        off= offerings.find_one({"_id": ObjectId(offering), 'public':True})
        if not off:
            print("Invalid offering ID.")
            return
        
        offer= Offering(off['availability'], off['public'], off['status'], off['lessonType'], off.get('_id'))
        if not offer.checkAvailability():
            print(f"Offering not available (Offering: {off})")
            return
        
        id = None

        if underageName:
            result=customers.find_one({"first_name":underageName[0], "last_name": underageName[1], "age":int(age)})
            id= result.get('_id')
        
        else:
            result= customers.find_one({"first_name":clientName[0], "last_name": clientName[1], "age":int(age)})
            id= result.get('_id')
        
        booking= Booking(offering,clientName, underageName, age, id)
        booking.setStatus('active')
        catalog=BookingCatalog()
        catalog.add(booking)
        

        mode =offer.getOfferingMode()

        if mode =="g":
            offer.decreaseAvailableSpots()
        else:
            offer.updateStatus("booked")
        
        if underageName:
            print(f"{clientName[0]} {clientName[1]} made a booking for their minor {underageName[0]} {underageName[1]} (who is {age} yrs old).")
        else:
            print(f"{clientName[0]} {clientName[1]} made a booking.")

    def viewBookingDetails(self, clientId):
        catalog=BookingCatalog()
        items=catalog.getBookings(clientId)
        for document in items:
            print(document)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Console, cls).__new__(cls, *args, **kwargs)
        return cls._instance


class BookingCatalog:
    def __init__(self) -> None:
        pass

    def getBookings(self, clientId):
        return bookings.find({"cid":ObjectId(clientId)})
    
    def add(self, booking):
        result=bookings.insert_one({"cid":ObjectId(booking.cid), "oid": ObjectId(booking.oid), "status": booking.status})
        print(f"Added booking {result}")

class Booking:
    def __init__(self, oid, clientName, underageName, age, cid) -> None:
        self.oid=oid
        self.clientName=clientName
        self.underageName=underageName,
        self.age=age
        self.cid=cid
    
    def setStatus(self, status):
        self.status=status
    
def main():

    
    
    console = Console()

    while True:
        if console.hasWriter:
            print("Writer already present")
            break
        
        print("\n1. Create Offering (Admin)")
        print("2. View Available Offerings (Instructor)")
        print("3. Take Offering (Instructor)")
        print("4. View Offerings (Public)")
        print("5. Register as a client")
        print("6. Book (Client)")
        print("7. View your bookings (Client)")
        print("8. Cancel Booking (Client)")
        print("9. Exit")
        
        choice = input("Enter your choice: ")

        
        if choice == "1":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            admin = Administrator()
            organization = input("Enter Organization name: ")
            lesson_type = input("Enter lesson type: ")
            while True:
                start_time = input("Enter a start time in format yyyy-mm-ddThh:mm ")
                try:
                    start=datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
                except ValueError:
                    print("Invalid format.")
                    continue
                break
            city= input("Enter a city: ")
            location = input("Enter address: ")
            mode = input("Enter p for private or g for group mode: ")
            while mode!="g" and mode!="p":
                print("Invalid mode selected")
                mode = input("Enter p for private or g for group mode: ")
            admin.console.create_offering(lesson_type, start, location, city, mode, organization)
            

        elif choice == "2":
            specialization= input("Enter your specialization: ")
            name= input("Enter your name: ")
            phone= input("Enter your phone number: ")
            instructor= Instructor(specialization, name, phone)
            instructor.viewAvailableOfferings()
            

        elif choice == "3":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            specialization= input("Enter your specialization: ")
            name= input("Enter your name: ")
            phone= input("Enter your phone number: ")
            instructor= Instructor(specialization, name, phone)
            offering_id = input("Enter offering ID to take: ")
            if instructor.takeOffering(offering_id):
                print("Offering taken successfully")
            else:
                print("Failed to take offering. Might already be taken or doesn't exist")

        elif choice == "4":
            console.hasReader=True
            reader=Reader()
            reader.view_offerings()
            console.hasReader=False
        
        elif choice == "5":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            fname= input("Enter your first name: ")
            lname= input("Enter your last name: ")
            age= input("Enter your age: ")

            if customers.find_one({"first_name":fname, "last_name": lname, "age":int(age)}):
                result = customers.find_one({"first_name":fname, "last_name": lname, "age":int(age)})
                print(f"You are already registered as a client ({result}).")
                continue

            if int(age)<18:
                print("Please pass the control over to your legal guardian.")
                pfname= input("Enter guardian's first name:")
                plname= input("Enter guardian's last name:")
                page =input("Enter guardian's age:")

                id= None
                if not customers.find_one({"first_name":pfname, "last_name": plname, "age":int(page)}):
                    result = customers.insert_one({"first_name":pfname, "last_name": plname, "age":int(page)})
                    id=result.inserted_id
                    print(f"Legal guardian, you are now registered as a client ({result}).")
                else:
                    result=customers.find_one({"first_name":pfname, "last_name": plname, "age":int(page)})
                    id=result.get('_id')
                    print(f"Legal guardian, you are already registered as a client ({result}).")

                kid = customers.insert_one({"first_name":fname, "last_name": lname, "age":int(age), "guardian": id})
                print(f"Minor, you are now registered as a client ({kid}).")
           
            else:
                
                result = customers.insert_one({"first_name":fname, "last_name": lname, "age":int(age)})
                print(f"You are now registered as a client ({result}).")
                

        
        elif choice == "6":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            fname= input("Enter your first name: ")
            lname= input("Enter your last name: ")
            age=  input("Enter your age:  ")

            if not customers.find_one({"first_name":fname, "last_name": lname, "age":int(age)}):
                print(f"You are not yet registered as a client. Please register as a client befor booking classes.")
                continue

            offering= input("Enter the offering ID: ")
            

            clientName=[]
            underageName=[]

            if int(age)<18:
                underageName.append(fname)
                underageName.append(lname)
                result=customers.find_one({"first_name":fname, "last_name": lname, "age":int(age)})
                result=customers.find_one({"_id":result.get('_id')})
                clientName.append(result['first_name'])
                clientName.append(result['last_name'])
            
            else:
                clientName.append(fname)
                clientName.append(lname)
            
            console.createBooking(offering, clientName, underageName, age)

        elif choice == "7":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            clientId= input("Enter your client ID: ")
            console.viewBookingDetails(clientId)

        elif choice == "8":
            if console.hasReader:
                print("Reader(s) already present")
                continue
            id= input("Enter your clientID:")
            


        elif choice == "9":
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()