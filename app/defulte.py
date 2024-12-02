# Import required libraries
import google.generativeai as genai  # Gemini AI library
import os  # For accessing environment variables

# Configure the Gemini API with an API key stored in environment variable
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create a generative model instance using Gemini 1.5 Flash
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Infinite loop for continuous interaction
while True:
    # Prompt user for input
    qes = str(input('ask google gemeni: '))
    
    # Generate content based on user input
    response = model.generate_content(qes)
    
    # Print the generated response
    print(response.text)