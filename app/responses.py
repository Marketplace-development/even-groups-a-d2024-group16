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
        "delete account": "To delete your account, please contact our support team via the 'Contact' page.",
        "login": "To log in, click on the 'Login' button on the homepage and enter your email. This will take you to the Dashboard page.",
        "register": "To create an account, click on the 'Register' button on the homepage and fill in your details.",
        "contact": "For help, visit the 'Contact' page or email us at dishcovery101@gmail.com.",
        "upload image": "As a chef, you need to upload images for your recipes when adding or editing a recipe. This will make your recipe more appealing!",
        "update recipe": "To update a recipe, go to 'My Stats&Uploads' and click on the 'Edit recipe' button for the specific recipe you want to update.",
        "edit recipe": "To edit a certain recipe, go to the recipe via 'My Stats&Uploads' in the menu, and click on the 'Edit recipe' button.",
        "leave review": "You can leave a review for a recipe by clicking on 'View Reviews' and filling in the review form.",
        "dashboard": "You can always go to the Dishcovery dashboard and view all recipes by clicking on our logo in the navigation bar, at the top left corner of your screen",
        "view profile": "You can view your profile information by selecting 'Edit Profile' from the menu.",
        "filter recipes": "You can filter recipes based on categories, origin, ingredients, rating, price range or allergenes by using the filter box on the dashboard.",
        "account settings": "To update your account settings, go to 'Edit Profile' in the menu.",
        "about us": "Visit the 'Contact' page to learn more about Dishcovery and our mission.",
        "how to search recipes": "You can search for recipes using the search bar. Simply enter the recipe name, an ingredient, or a category.",
        "favorite recipes": "You can save your favorite recipes by clicking on the heart icon next to a recipe. These favorite recipes are added to your personal Dishcovery wishlist.",
        "wishlist": "You can save recipes in Dishcovery your wishlist by clicking on the heart icon next to a recipe. Go to your wishlist via the navigation bar.",
        "view uploaded recipes": "You can view all the recipes you've uploaded under 'My Stats&Uploads' in the menu.",
        "categories": "We organize recipes into categories such as starters, main dishes, desserts, snacks, drinks and more.",
        "category": "We organize recipes into categories such as starters, main dishes, desserts, snacks, drinks and more.",
        "origin": "We have recipes from different origins such as Italian, French, Chinese, Mexican and many more. Search recipes based on your favorite origin by using the filter on the dashboard.",
        "cooking time": "Each recipe includes an estimated cooking time. You can use filters to search for quick or longer recipes.",
        "allergies filter": "Use the filters on the filter box to exclude recipes that contain specific allergens.",
        "allergies": "If you have certain allergies, you can filter recipes according to them. Use the filter box on your dashboard.",
        "how to review recipes": "You can leave a review by clicking on 'View Reviews' and then filling in your rating and comments.",
        "new features": "We are constantly improving Dishcovery. Keep an eye out for new features on our homepage! Suggestions are always appreciated, you can send them via dishcovery101@gmail.com.",
        "support": "For further assistance, you can email dishcovery101@gmail.com or visit the 'Contact' page.",
        "login problem": "If you're unable to log in, please check your email for typos. If you still can't login, it means you haven't created an account yet. Go to the Register page to make your Dishcovery profile!",
        "update email": "You can't update the email address on your current profile. Make a new Dishcovery account with your new email address",
        "chef benefits": "As a chef, you can upload and share recipes, gain followers, and interact with food lovers to become more popular as a specialized chef and gain some extra income.",
        "user benefits": "As a user, you can search for recipes, save favorites, leave reviews, and follow your favorite chefs.",
        "feedback": "We value your feedback! If you have some, please send us an email and share it with us.",
        "email address": "Our email address is dishcovery101@gmail.com. You can reach us at all times.",
        "default": "I'm sorry, I didn't understand that. Could you please rephrase?"
    },
    "fallback": [
        "I'm not sure about that. Could you clarify?",
        "Hmm, I don't have an answer for that. Could you try asking something else?",
        "I couldn't find an answer for that. Try asking about account settings, adding recipes, or website features.",
        "I'm sorry, I don't have information about that right now."
    ]
}

def get_response(user_message):
    """
    Retourneer een reactie op basis van het gebruikersbericht.
    """
    user_message = user_message.lower()

    # Basislogica voor reacties
    if "hello" in user_message or "hi" in user_message or "hey" in user_message:
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
    elif "delete account" in user_message:
        return responses["faq"]["delete account"]
    elif "login" in user_message:
        return responses["faq"]["login"]
    elif "register" in user_message:
        return responses["faq"]["register"]
    elif "contact" in user_message:
        return responses["faq"]["contact"]
    elif "upload image" in user_message:
        return responses["faq"]["upload image"]
    elif "update recipe" in user_message:
        return responses["faq"]["update recipe"]
    elif "edit recipe" in user_message:
        return responses["faq"]["edit recipe"]
    elif "leave review" in user_message:
        return responses["faq"]["leave review"]
    elif "dashboard" in user_message:
        return responses["faq"]["dashboard"]
    elif "view profile" in user_message:
        return responses["faq"]["view profile"]
    elif "filter recipes" in user_message:
        return responses["faq"]["filter recipes"]
    elif "account settings" in user_message:
        return responses["faq"]["account settings"]
    elif "about us" in user_message:
        return responses["faq"]["about us"]
    elif "search recipes" in user_message:
        return responses["faq"]["how to search recipes"]
    elif "favorite recipes" in user_message:
        return responses["faq"]["favorite recipes"]
    elif "wishlist" in user_message:
        return responses["faq"]["wishlist"]
    elif "view uploaded recipes" in user_message:
        return responses["faq"]["view uploaded recipes"]
    elif "categories" in user_message:
        return responses["faq"]["categories"]
    elif "category" in user_message:
        return responses["faq"]["category"]
    elif "origin" in user_message:
        return responses["faq"]["origin"]
    elif "cooking time" in user_message:
        return responses["faq"]["cooking time"]
    elif "allergies filter" in user_message:
        return responses["faq"]["allergies filter"]
    elif "allergies" in user_message:
        return responses["faq"]["allergies"]
    elif "review recipes" in user_message:
        return responses["faq"]["how to review recipes"]
    elif "new features" in user_message:
        return responses["faq"]["new features"]
    elif "support" in user_message:
        return responses["faq"]["support"]
    elif "login problem" in user_message:
        return responses["faq"]["login problem"]
    elif "update email" in user_message:
        return responses["faq"]["update email"]
    elif "chef benefits" in user_message:
        return responses["faq"]["chef benefits"]
    elif "user benefits" in user_message:
        return responses["faq"]["user benefits"]
    elif "feedback" in user_message:
        return responses["faq"]["feedback"]
    elif "email address" in user_message:
        return responses["faq"]["email address"]
    else:
        # Kies een fallback als er geen specifieke match is
        return random.choice(responses["fallback"])
