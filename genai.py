import google.generativeai as genai

genai.configure(api_key="YOUR_KEY_HERE")

def ask_genai(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text
