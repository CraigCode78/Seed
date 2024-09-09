import streamlit as st
from openai import OpenAI
from deep_translator import GoogleTranslator
import re

# Initialize the OpenAI client
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_response(prompt, user_preferences):
    try:
        messages = [
            {"role": "system", "content": f"You are an expert AI travel concierge. Provide detailed, informative, and engaging responses about travel destinations, cultural insights, local customs, travel tips, and personalized recommendations. Consider the user's preferences: {user_preferences}. Always end your response with a follow-up question to encourage further engagement. When creating itineraries, use the format 'Day X:' for each day, followed by 'Morning:', 'Afternoon:', and 'Evening:' subsections."},
            {"role": "user", "content": prompt}
        ]
        
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        
        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
                yield response
        
    except Exception as e:
        yield f"An error occurred: {str(e)}"

def get_image_url(query):
    # This is a placeholder. In a real app, you'd use an actual image API.
    return f"https://source.unsplash.com/800x600/?{query}"

def parse_itinerary(response):
    days = re.split(r'Day \d+:', response)[1:]  # Split by "Day X:" and remove the first empty element
    parsed_itinerary = []
    for i, day in enumerate(days, 1):
        day_content = f"Day {i}:" + day
        parsed_itinerary.append({"day": i, "content": day_content.strip()})
    return parsed_itinerary

def initial_questionnaire():
    st.title("Welcome to Your Personal Travel Concierge!")
    st.write("To provide you with the best travel recommendations, please answer a few questions:")
    
    travel_style = st.selectbox("What's your preferred travel style?", 
                                ["Luxury", "Budget", "Adventure", "Cultural", "Relaxation"])
    
    interests = st.multiselect("Select your main interests when traveling:", 
                               ["History", "Food", "Nature", "Art", "Nightlife", "Shopping", "Sports"])
    
    budget = st.slider("What's your daily budget per person (in USD)?", 0, 1000, 100)
    
    trip_duration = st.number_input("How many days do you typically travel?", 1, 30, 7)
    
    preferred_climate = st.selectbox("What's your preferred climate for this trip?", 
                                     ["Tropical", "Mediterranean", "Alpine", "Desert", "Temperate"])
    
    if st.button("Start My Personalized Travel Experience"):
        preferences = {
            "travel_style": travel_style,
            "interests": interests,
            "budget": budget,
            "trip_duration": trip_duration,
            "preferred_climate": preferred_climate
        }
        st.session_state.user_preferences = preferences
        st.session_state.questionnaire_completed = True
        st.rerun()

def build_itinerary():
    if 'itinerary' not in st.session_state:
        st.session_state.itinerary = []
    
    # Display current itinerary
    for item in st.session_state.itinerary:
        st.subheader(f"Day {item['day']}")
        content = st.text_area(f"Edit Day {item['day']}", item['content'], height=200)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Update Day {item['day']}"):
                item['content'] = content
        with col2:
            if st.button(f"Delete Day {item['day']}"):
                st.session_state.itinerary.remove(item)
                st.rerun()
    
    # Add new day manually
    st.subheader("Add New Day")
    new_day = st.number_input("Day", min_value=1, max_value=30, value=len(st.session_state.itinerary) + 1)
    new_content = st.text_area("Day's Activities")
    if st.button("Add Day"):
        st.session_state.itinerary.append({"day": new_day, "content": new_content})
        st.session_state.itinerary.sort(key=lambda x: x['day'])
        st.rerun()

def language_learning():
    phrase = st.text_input("Enter a phrase to translate:")
    target_lang = st.selectbox("Select target language:", ["es", "fr", "de", "it", "ja", "zh-CN"])
    if st.button("Translate") and phrase:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translation = translator.translate(phrase)
        st.write(f"Translation: {translation}")

def main_chat_interface():
    st.title("Seed AI Travel Concierge (Powered by GPT-4)")

    st.markdown("""
    This AI Travel Concierge uses GPT-4 to provide you with expert travel advice, recommendations, and insights. 
    Your responses will be personalized based on your preferences. You'll see the response being typed out in real-time.
    """)

    # Create two columns: one for chat (wider) and one for additional features
    chat_col, feature_col = st.columns([2, 1])

    with chat_col:
        # Display user preferences
        st.sidebar.title("Your Travel Preferences")
        for key, value in st.session_state.user_preferences.items():
            st.sidebar.write(f"{key.replace('_', ' ').title()}: {value}")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"], caption="Relevant travel image")

        # React to user input
        if prompt := st.chat_input("What would you like to know about travel?"):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                for response in get_ai_response(prompt, st.session_state.user_preferences):
                    full_response = response
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Parse and save itinerary if present
            if "Day 1:" in full_response:
                parsed_itinerary = parse_itinerary(full_response)
                if st.button("Save This Itinerary"):
                    st.session_state.itinerary = parsed_itinerary
                    st.success("Itinerary saved successfully!")

            # Add a relevant image
            image_url = get_image_url(prompt.split()[-1])  # Use the last word of the prompt as the image query
            st.image(image_url, caption="Relevant travel image")
            st.session_state.messages[-1]["image"] = image_url

        # Add a sidebar with personalized travel tips
        st.sidebar.title("Personalized Travel Tips")
        travel_style = st.session_state.user_preferences['travel_style']
        if travel_style == "Luxury":
            tips = "1. Research exclusive experiences\n2. Book high-end accommodations in advance\n3. Consider hiring a personal guide"
        elif travel_style == "Budget":
            tips = "1. Look for free walking tours\n2. Stay in hostels or budget accommodations\n3. Cook your own meals to save money"
        elif travel_style == "Adventure":
            tips = "1. Check equipment requirements for activities\n2. Consider travel insurance for extreme sports\n3. Research local adventure tour operators"
        elif travel_style == "Cultural":
            tips = "1. Learn about local customs and etiquette\n2. Visit museums and historical sites\n3. Try authentic local cuisine"
        else:  # Relaxation
            tips = "1. Book spa treatments in advance\n2. Look for all-inclusive resorts\n3. Plan some downtime in your itinerary"
        
        st.sidebar.info(tips)

    with feature_col:
        st.subheader("Travel Tools")
        
        # Itinerary Builder
        with st.expander("Itinerary Builder", expanded=True):
            build_itinerary()
        
        # Language Translation
        with st.expander("Language Translation", expanded=True):
            language_learning()

# Main app logic
if 'questionnaire_completed' not in st.session_state:
    st.session_state.questionnaire_completed = False

if not st.session_state.questionnaire_completed:
    initial_questionnaire()
else:
    main_chat_interface()
