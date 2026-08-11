import json

from ChatbotWebsite.chatbot.paths import MINDFULNESS_PATH

# load mindfulness exercises from json file
with MINDFULNESS_PATH.open(encoding="utf-8") as file:
    mindfulness_exercises = json.load(file)


# get mindfulness exercise description and filename
def get_description(title):
    for exercise in mindfulness_exercises["mindfulness_exercises"]:
        if exercise["title"] == title:
            return exercise["description"], exercise["file_name"]
    return "Exercise not found"
