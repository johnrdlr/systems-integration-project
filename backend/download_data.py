from urllib.request import urlretrieve
from bs4 import BeautifulSoup as bs 
import hjson, json
from datetime import datetime
import os

courseURL = "https://uisapppr3.njit.edu/scbldr/include/datasvc.php?p=/" #URL used to scrap the data directly from the website
urlretrieve(courseURL, "courses.json") #Download the data file and name it as courses.json

#Open courses.json and store the values into a variable
with open("courses.json", "r") as f:
    lines = f.readlines()

#Remove some characters encapsulating the data so we can parse it
with open("new_courses.json", "w") as f:
    lines[-1].strip("\n")
    f.write(lines[-1].replace("define(", "")[:-2])

#Reopen and parse with temporary name
f = open("new_courses.json")
courseJSON = hjson.load(f)

newCourse = {} #Initialize a dictionary to store the reformatted data into
for course in courseJSON["data"]: #Access the data atribute of the og dict
    for sec in course[3:]: #Go into the section of the dictionary that has the data we actually want
        secClasses = sec[-1] #Get the last thing in the list which is where the class meet times exist as well as other information
        for secClass in secClasses:
            start = secClass[1] // 60 + (secClass[0] - 2) * (24 * 60) #Convert the start time of the class from seconds of the week to minutes of the week and start from sunday
            end = secClass[2] // 60 + (secClass[0] - 2) * (24 * 60) #Convert the end time of the class from seconds of the week to minutes of the week and start from sunday
            
            #Add an entry into newCourses is that courses doesn't exist yet
            #Add the schedule data into that course into it as well
            if secClass[-1] not in newCourse:
                newCourse[secClass[-1]] = [(course[0], course[1], start, end)]
            else:
                newCourse[secClass[-1]].append(tuple((course[0], course[1], start, end)))

del newCourse[" "] #Delete online classes that were added

#New dictionary used to send to the messaging server and then database
courseMessage = {}
courseMessage["data"] = newCourse #Store the formatted data into the data attribute of the dict
courseMessage["term"] = courseJSON["term"].replace(" ", "") #Add the term of the semester to the term attribute

#Reformat and add the time the data was updated originally from the website to the update attribute of the message
courseMessage["update"] = datetime.strptime(" ".join(courseJSON["update"].replace(",", "").split(" ")), '%a %b %d %Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')

#Store the dict into a new file
with open("courses_processed.json", "w") as f:
    json.dump(courseMessage, f)

#Delete unnecessary files
os.remove("new_courses.json")
os.remove("courses.json")