import json

from ChatbotWebsite.chatbot.paths import TOPICS_PATH

# load topics from json file
with TOPICS_PATH.open(encoding="utf-8") as file:
    topics = json.load(file)


# get topic content
def get_content(title):
    for topic in topics["topics"]:
        if topic["title"] == title:
            return topic["content"]
    return "Topic not found"
