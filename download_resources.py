from urllib.request import urlretrieve
from bs4 import BeautifulSoup as bs 
import hjson, json
import datetime
import os
courseURL = "https://uisapppr3.njit.edu/scbldr/include/datasvc.php?p=/"
eventURL = "https://njit.campuslabs.com/engage/events.rss"

urlretrieve(courseURL, "courses.json")
urlretrieve(eventURL, "events.html")


with open("courses.json", "r") as f:
    lines = f.readlines()
with open("new_courses.json", "w") as f:
    lines[-1].strip("\n")
    f.write(lines[-1].replace("define(", "")[:-2])

f = open("new_courses.json")
courseJSON = hjson.load(f)

newCourse = {}
for course in courseJSON["data"]:
    for sec in course[3:]:
        secClasses = sec[-1]
        for secClass in secClasses:
            start = secClass[1] // 60 + secClass[0] * (24 * 60)
            end = secClass[2] // 60 + secClass[0] * (24 * 60)
            if secClass[-1] not in newCourse:
                newCourse[secClass[-1]] = [(course[1], start, end)]
            else:
                newCourse[secClass[-1]].append(tuple((course[1], start, end)))
del newCourse[" "]
with open("courses_processed.json", "w") as f:
    json.dump(newCourse, f)

# html=open('events.html', encoding="utf8") 
# soup=bs(html, 'html.parser')
# newEvent = {}
# for item in soup.find_all("item"):

os.remove("new_courses.json")