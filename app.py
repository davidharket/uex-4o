from openai import *
from flask import session
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_response(message):
    response_content = ""
    buttons = []

    valid_roles = ["system", "user", "assistant"]
    messages = [{"role": "system", "content": "Alltid svar kort. Omkring 25 ord. start en samtale, deretter gi ressurser etter du har et forhold med den du snakker med. Du er en assistent som hjelper de du snakker med med å forstå tjenester og å selge løsningen deres. Du jobber for Uex. Du er morsom og underholdende, men først av alt hjelpsom. Beskrivelse av Uex: 'Uex er et selskap som lager skreddersydde chat-applikasjoner med dynamisk funksjonalitet som kan plasseres på en hver nettside til en rimelig pris. Disse chatbottene kan fungere som salgsassistenter, guider, og så mye annet.' Som en som jobber for uex har du et par verktøy. Du kan bruke disse verktøyene ved å skrive de som en del av svaret ditt. Det første verktøyet er: {knapp_1}. Om du skriver {knapp_1} kommer det opp en knapp som lar kunder besøke 'Om oss'-siden. Det andre verktøyet er: {knapp_2}. Om du skriver {knapp_2} kommer det opp en knapp som lar kunder besøke 'Produkter'-siden. Det tredje verktøyet er: {skjema}. Om du skriver {skjema} kommer det opp et skjema som lar kunder ta direkte kontakt"}]

    # Validate and append historical messages
    for msg in session.get('chat_history', []):
        if msg["role"] in valid_roles:
            messages.append(msg)
    # Append the current user message
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=1,
            max_tokens=255,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        response_content = response.choices[0].message.content

        # Check for specific keywords to add buttons
        if "{knapp_1}" in response_content:
            buttons.append({"label": "Om oss", "link": "https://example.com/about"})
            response_content = response_content.replace("{knapp_1}", "")

        if "{knapp_2}" in response_content:
            buttons.append({"label": "Produkter", "link": "https://example.com/products"})
            response_content = response_content.replace("{knapp_2}", "")

    except OpenAIError as e:
        response_content = "An error occurred while processing your request. Please try again."

    return response_content, buttons
