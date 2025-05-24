import streamlit as st
import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
import time

# Page configuration
st.set_page_config(
    page_title="Company Brochure Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'brochure_generated' not in st.session_state:
    st.session_state.brochure_generated = False
if 'current_brochure' not in st.session_state:
    st.session_state.current_brochure = ""

# Main header
st.markdown("""
<div class="main-header">
    <h1>🏢 Company Brochure Generator</h1>
    <p>Generate professional company brochures from any website using AI</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Google AI API Key",
        type="password",
        help="Enter your Google AI (Gemini) API key"
    )
    
    if api_key:
        if api_key.startswith('AIzaS') and len(api_key) > 10:
            st.session_state.api_key_valid = True
            st.success("✅ API key is valid!")
        else:
            st.session_state.api_key_valid = False
            st.error("❌ Invalid API key format")
    
    st.markdown("---")
    
    # Model configuration
    st.subheader("🤖 Model Settings")
    model = st.selectbox(
        "Select Model",
        ["gemini-2.0-flash", "gemini-1.5-pro"],
        index=0
    )
    
    st.markdown("---")
    
    # Instructions
    st.subheader("📖 Instructions")
    st.markdown("""
    1. Enter your Google AI API key
    2. Provide company name and website URL
    3. Click 'Generate Brochure'
    4. Download or copy the generated brochure
    """)

# Website class
class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, timeout=10)
            self.body = response.content
            soup = BeautifulSoup(self.body, 'html.parser')
            self.title = soup.title.string if soup.title else 'No title found'
            
            if soup.body:
                for irrelevant in soup.body(['script', 'style', 'img', 'input']):
                    irrelevant.decompose()
                self.text = soup.body.get_text(separator='\n', strip=True)
            else:
                self.text = ''
                
            links = [link.get('href') for link in soup.find_all('a')]
            self.links = [link for link in links if link]
            
        except Exception as e:
            st.error(f"Error loading website: {str(e)}")
            self.title = "Error loading page"
            self.text = ""
            self.links = []
    
    def get_contents(self):
        return f'\nWebPage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n{self.url}\n\n'

# Initialize OpenAI client
@st.cache_resource
def get_openai_client(api_key):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    return OpenAI(api_key=api_key, base_url=BASE_URL)

# Function to get relevant links
def get_links(url, openai_client, model):
    link_system_prompt = """You are provided with a list of links found on a webpage. You are able to decide which of the links would be most relevant to include in a brochure about the company, such as links to an about page or a company page, or careers/jobs pages.
    
You should respond in JSON as in the examples:
{
    "links" : [
        {"type":"about page", "url":"http://full.url/goes/here/about"},
        {"type":"careers page", "url": "http://another.full.url/careers"}
    ]
}"""
    
    website = Website(url)
    user_prompt = f'Here is the list of links on the website of {website.url}.'
    user_prompt += "Please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in json format. Do not include Terms of service, privacy, email links.\n"
    user_prompt += "links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': link_system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            response_format={'type': 'json_object'}
        )
        result = response.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        st.error(f"Error getting links: {str(e)}")
        return {"links": []}

# Function to get all details
def get_all_details(url, openai_client, model):
    result = 'Loading page\n'
    website = Website(url)
    result += website.get_contents()
    
    with st.spinner("Finding relevant links..."):
        links_ai = get_links(url, openai_client, model)
        
    if links_ai.get('links'):
        st.info(f"Found {len(links_ai['links'])} relevant links")
        
        for i, link in enumerate(links_ai['links']):
            with st.spinner(f"Loading {link['type']}... ({i+1}/{len(links_ai['links'])})"):
                try:
                    result += f"\n\n{link['type']}\n"
                    result += Website(link['url']).get_contents()
                except Exception as e:
                    st.warning(f"Could not load {link['type']}: {str(e)}")
    
    return result

# Function to create brochure
def create_brochure(company_name, url, openai_client, model):
    system_prompt = """You are an assistant that analyzes the contents of several relevant pages from a company website and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown. Include details of company culture, customers and careers/jobs if you have the information."""
    
    with st.spinner("Gathering website information..."):
        all_details = get_all_details(url, openai_client, model)
    
    user_prompt = f"You are looking at the company called: {company_name}"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown\n"
    user_prompt += all_details[:20000]  # Limit content to avoid token limits
    
    with st.spinner("Generating brochure with AI..."):
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error generating brochure: {str(e)}")
            return None

# Main application
def main():
    # Input section
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input(
            "🏢 Company Name",
            placeholder="e.g., Hugging Face",
            help="Enter the name of the company"
        )
    
    with col2:
        website_url = st.text_input(
            "🌐 Website URL",
            placeholder="https://example.com",
            help="Enter the full website URL including https://"
        )
    
    # Validation
    url_valid = website_url.startswith(('http://', 'https://')) if website_url else False
    
    if website_url and not url_valid:
        st.error("Please enter a valid URL starting with http:// or https://")
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button(
            "🚀 Generate Brochure",
            disabled=not (st.session_state.api_key_valid and company_name and url_valid),
            use_container_width=True,
            type="primary"
        )
    
    # Generate brochure
    if generate_btn:
        if not st.session_state.api_key_valid:
            st.error("Please provide a valid API key in the sidebar")
            return
        
        if not company_name or not url_valid:
            st.error("Please provide both company name and valid website URL")
            return
        
        # Initialize OpenAI client
        openai_client = get_openai_client(api_key)
        
        # Create brochure
        brochure = create_brochure(company_name, website_url, openai_client, model)
        
        if brochure:
            st.session_state.current_brochure = brochure
            st.session_state.brochure_generated = True
            st.success("✅ Brochure generated successfully!")
        else:
            st.error("❌ Failed to generate brochure. Please try again.")
    
    # Display brochure
    if st.session_state.brochure_generated and st.session_state.current_brochure:
        st.markdown("---")
        st.header("📋 Generated Brochure")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Download as Markdown", use_container_width=True):
                st.download_button(
                    label="Download Brochure.md",
                    data=st.session_state.current_brochure,
                    file_name=f"{company_name.replace(' ', '_')}_brochure.md",
                    mime="text/markdown"
                )
        
        with col2:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.current_brochure, language="markdown")
        
        with col3:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.brochure_generated = False
                st.session_state.current_brochure = ""
                st.rerun()
        
        # Display the brochure with proper markdown rendering
        st.markdown("### Preview:")
        
        # Create tabs for different view modes
        tab1, tab2 = st.tabs(["📖 Rendered View", "📝 Raw Markdown"])
        
        with tab1:
            # Render the markdown properly
            st.markdown(brochure, unsafe_allow_html=True)
        
        with tab2:
            # Show raw markdown in a code block
            st.code(st.session_state.current_brochure, language="markdown")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>Built with ❤️ using Streamlit and Google AI</p>
        <p><small>Make sure to keep your API key secure and never share it publicly</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()