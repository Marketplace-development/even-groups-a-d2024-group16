import random

# Standaardreacties voor de chatbot
responses = {
    "greetings": [
        "Hello! How can I assist you today?",
        "Hi there! What do you need help with?",
        "Welcome to Dishcovery! How can I help you?"
    ],
    "faq": {
        "find recipes": "You can use the search bar on the dashboard to find recipes by name, ingredient, or category.",
        "add recipe": "As a chef, you can add new recipes by clicking on 'Add Recipe' in the menu.",
        "edit profile": "To update your profile, go to 'Edit Profile' in the menu.",
        "logout": "To logout, click on the 'Logout' button in the menu.",
        "menu": "You can find the menu options by clicking on the menu icon in the top-right corner.",
        "default": "I'm sorry, I didn't understand that. Could you please rephrase?"
    },
    "fallback": [
        "I'm not sure about that. Could you clarify?",
        "Hmm, I don't have an answer for that. Could you try asking something else?",
        "I'm sorry, I don't have information about that right now."
    ]
}

def get_response(user_message):
    """
    Retourneer een reactie op basis van het gebruikersbericht.
    """
    user_message = user_message.lower()

    # Basislogica voor reacties
    if "hello" in user_message or "hi" in user_message:
        return random.choice(responses["greetings"])
    elif "find recipes" in user_message:
        return responses["faq"]["find recipes"]
    elif "add recipe" in user_message:
        return responses["faq"]["add recipe"]
    elif "edit profile" in user_message:
        return responses["faq"]["edit profile"]
    elif "menu" in user_message:
        return responses["faq"]["menu"]
    elif "logout" in user_message:
        return responses["faq"]["logout"]
    else:
        # Kies een fallback als er geen specifieke match is
        return random.choice(responses["fallback"])
