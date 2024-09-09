import streamlit as st
from openai import OpenAI
import os

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ai_response(prompt, user_preferences):
    try:
        messages = [
            {"role": "system", "content": f"You are an expert AI travel concierge. Provide detailed, informative, and engaging responses about travel destinations, cultural insights, local customs, travel tips, and personalized recommendations. Consider the user's preferences: {user_preferences}. Always end your response with a follow-up question to encourage further engagement."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                yield full_response
        
    except Exception as e:
        yield f"An error occurred: {str(e)}"

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

def main_chat_interface():
    st.title("AI Travel Concierge (Powered by GPT-4)")

    st.markdown("""
    This AI Travel Concierge uses GPT-4 to provide you with expert travel advice, recommendations, and insights. 
    Your responses will be personalized based on your preferences.
    """)

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

    # React to user input
    if prompt := st.chat_input("What would you like to know about travel?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            for response in get_ai_response(prompt, st.session_state.user_preferences):
                response_placeholder.markdown(response + "▌")
            response_placeholder.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Main app logic
if 'questionnaire_completed' not in st.session_state:
    st.session_state.questionnaire_completed = False

if not st.session_state.questionnaire_completed:
    initial_questionnaire()
else:
    main_chat_interface()
