'''
Anuj kumar
23rd May 2025
AIM: Creating Multiple AI model in a single class

Models Added Till 23rd 2025
1. SambaNova Cloud 
2. Google Gemini Model
'''
# imports 
import os
from dotenv import load_dotenv
from openai import OpenAI

messages = [
    {'role':'system', 'content':'You are a very famous Stand-up comadian.'},
    {'role':'user', 'content':"Tell me a joke."}
]
class ModelsAPI:
    def __init__(self):
        load_dotenv()
        self.sambaNova_api = os.getenv('SAMBANOVA_API_KEY')
        self.google_api = os.getenv('GOOGLE_API_KEY')

    def sambanovaModel(self, messages=messages):
        self.MODEL = 'Llama-4-Maverick-17B-128E-Instruct'
        self.BASE_URL = 'https://api.sambanova.ai/v1'
        openai = OpenAI(
            api_key=self.sambaNova_api,
            base_url=self.BASE_URL,
        )
        response = openai.chat.completions.create(
            model=self.MODEL,
            messages=messages,
        )
        return response.choices[0].message.content
    
    def googleModel(self, messages=messages):
        self.MODEL = "gemini-2.0-flash"
        self.BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
        openai = OpenAI(
            api_key= self.google_api,
            base_url = self.BASE_URL
        )
        res = openai.chat.completions.create(
            model=self.MODEL,
            messages=messages,
        )
        return res.choices[0].message.content
    
obj1 = ModelsAPI()
messages = [
    {'role':'system', 'content':'You are a very good doodle artist.'},
    {'role':'user', 'content':"Create a sample doodle for me just generate the image i don't need discription"}
]
print(f"SambaNova Model Response:\n{obj1.sambanovaModel(messages)}\n\n")
print(f"Google Model Response:\n{obj1.googleModel(messages)}\n\n")