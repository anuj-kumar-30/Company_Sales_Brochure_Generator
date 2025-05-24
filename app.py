# Imports 
import os #for getting environment variables
import requests # we need this lib to make requests on url
import json # this will be used in the json type output
from typing import List # 
from dotenv import load_dotenv # for loading .env file
from bs4 import BeautifulSoup # this pkg is used so that we can parse the html documnet
from IPython.display import Markdown, display, update_display # for displaying content in particular formate
from openai import OpenAI # for loading or connecting openai model i.e gemini, sambanova

# Initialize and Constants
load_dotenv()
ai_api_key = os.getenv('GOOGLE_API_KEY')

if ai_api_key and ai_api_key.startswith('AIzaS') and len(ai_api_key)>10:
    print('AI API key valid')
else:
    print('API key is invalid or Some Error occured Try after some')

MODEL = 'gemini-2.0-flash'
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
openai = OpenAI(
    api_key=ai_api_key,
    base_url=BASE_URL,
)

# checking if the model is working fine or not
def check_model(msg=[{'role':'system', 'content':'You are snarky assistant.'},{'role':'user', 'content':'what is 2+2?'}]):
    res = openai.chat.completions.create(
        model=MODEL,
        messages=msg
    )

    return res.choices[0].message.content
check_model()

msg = [
    {'role':'system', 'content':'You are snarky assistant.'},
    {'role':'user', 'content':'count the number of "a" in this sentence: This is a test sentence and my Name is anuj.'}
]
print(check_model(msg=msg))

class Website:
    def __init__(self, url):
        self.url = url # saving url 
        response = requests.get(url) # getting html response
        self.body = response.content # getting all the content inside of body tag
        soup = BeautifulSoup(self.body, 'html.parser') # adding html parser to make it little bit readable 
        self.title = soup.title.string if soup.title else 'No title found' # extracting title if present
        if soup.body: # removing all the irrelevant content like script, style, img, input
            for irrelevant in soup.body(['script', 'style', 'img', 'input']):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator='\n', strip=True) # now we will store all the content in the string by using separating it by \n
        else:
            self.text = '' # empty string
        links = [link.get('href') for link in soup.find_all('a')] # grabbing all the a tag with links/relative as well the absolute.
        self.links = [link for link in links if link]
    
    def get_contents(self):
        return f'\nWebPage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n{self.url}\n\n'
    
huggingface_url = 'https://huggingface.co/'
ed = Website(huggingface_url)
print(type(ed.text))

# Now as we have got all the necessary things from the website. which is 
# 1. title
# 2. text_content
# 3. all the links 

# Our next tasks now is to find the relevant links which we can add to our brochure.
# And it can be done with the help of our ai model gemini-2.0-flash
# step 01: create a system prompt for getting relevant links
# step 02: user prompt for providing and telling ai what kind of output i want
# step 03: pass this prompt to our model and get the result

link_system_prompt = "You are provided with a list of links found on a webpage. You are able to decide which of the links would be most relevant to include in a brochure.\
    about the company, such as links to an about page or a company page, or carrers/jobs pages.\n"
link_system_prompt += "You should respond in JSON as in the examples"
link_system_prompt += """
{
    "links" : [
        {'type':'about page', 'url':'http://full.url/goes/here/about'},
        {'type':'carrers page', 'url': 'http://another.full.url/carrers'}
    ]
}
"""

# user prompt
def get_links_user_prompt(website):
    user_prompt = f'Here is the list of links on the website of {website.url}.'
    user_prompt += "please decide which of these are relevent web links for a brochure about the company, respond with the full https URL in json format. Do not include Terms of service, privacy, email links.\n"
    user_prompt += "links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

# Now as we completed the step 1 and 2 user_prompt as well as system_prompt
def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role':'system', 'content':link_system_prompt},
            {'role':'user', 'content': get_links_user_prompt(Website(huggingface_url))}
        ],
        response_format={'type':'json_object'}
    )
    result = response.choices[0].message.content
    return json.loads(result)

def get_all_details(url):
    result = 'loading page\n'
    result += Website(url).get_contents()
    links_ai = get_links(url)
    print('found Links: ', links_ai)

    for link in links_ai['links']:
        result += f"\n\n{link['type']}\n"
        result += Website(link['url']).get_contents()
    return result

# from the above function we have gathered all the relevant information at one place now only thing we need to do is create a company brochure
system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website and creates a short brochure about the company for\
    prospective customers, investors and recruts. Respond in markdonw. Include details of company culture, customers and carrers/jobs if you have the information."

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"You are looking at the company called: {company_name}"
    user_prompt += f"Here are the contents of its, landing page and other relevant pages; use this information to build a short brochure of the company in markdown\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:20_000]
    return user_prompt

def create_brochure(company_name, url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {'role':'system', 'content': system_prompt},
            {'role':'user', 'content':get_brochure_user_prompt(company_name, url)}
        ]
    )
    result = response.choices[0].message.content
    display(Markdown(result))

print(create_brochure('Hugging Face', huggingface_url))