import streamlit as st
from openai import OpenAI
import os
import random
from datetime import datetime, timedelta
import re
import time
import tempfile

# OpenAI key management
def get_openai_key():
    # First, try to get the key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    
    # If not found in environment variables, try Streamlit secrets
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except FileNotFoundError:
            # If running locally and secrets file is not found, use a text input
            st.warning("OpenAI API key not found in environment variables or Streamlit secrets.")
            api_key = st.text_input("Please enter your OpenAI API key:", type="password")
            if api_key:
                # Save the entered key to session state for reuse
                st.session_state['openai_api_key'] = api_key
            elif 'openai_api_key' in st.session_state:
                # Reuse the previously entered key if available
                api_key = st.session_state['openai_api_key']
    
    if not api_key:
        st.error("OpenAI API key is required to run this application.")
        st.stop()
    
    return api_key

# Initialize the OpenAI client
client = OpenAI(api_key=get_openai_key())

# Mock data for simulated booking
mock_flights = [
    {"airline": "SkyHigh Airways", "departure": "10:00 AM", "arrival": "2:00 PM", "price": 320},
    {"airline": "Ocean Air", "departure": "2:00 PM", "arrival": "6:00 PM", "price": 280},
    {"airline": "Mountain Express", "departure": "8:00 PM", "arrival": "11:55 PM", "price": 350},
]

mock_hotels = [
    {"name": "Luxury Palace", "rating": 5, "price": 300},
    {"name": "Comfort Inn", "rating": 3, "price": 120},
    {"name": "Budget Stay", "rating": 2, "price": 80},
]

def get_ai_response(prompt, user_preferences, language="English"):
    try:
        system_message = f"""You are an expert AI travel concierge. Provide detailed, informative, and engaging responses about travel destinations, cultural insights, local customs, travel tips, and personalized recommendations. Consider the user's preferences: {user_preferences}. If appropriate, suggest 3 specific hotels that the user might be interested in, formatting them as 'Hotel: [Hotel Name]' on separate lines. 

        Important: Respond in {language}. Translate all your responses, including hotel names and any specific terms, into {language}."""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Respond in {language}: {prompt}"}
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
        
        hotel_suggestions = re.findall(r'Hotel: (.*)', full_response)
        st.session_state.suggested_hotels = hotel_suggestions
        
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

def text_to_speech(text, voice):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            for chunk in response.iter_bytes(chunk_size=4096):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        return tmp_file_path
    except Exception as e:
        st.error(f"An error occurred during text-to-speech conversion: {str(e)}")
        return None

def main_chat_interface():
    st.title("AI Travel Concierge (Powered by GPT-4 Turbo)")

    # Display confirmed booking at the top if it exists
    if st.session_state.get('confirmed_booking'):
        with st.expander("Your Confirmed Booking", expanded=True):
            for key, value in st.session_state.confirmed_booking.items():
                st.write(f"{key}: {value}")
            if st.button("Clear Booking"):
                del st.session_state.confirmed_booking
                st.rerun()

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                col1, col2 = st.columns([3, 1])
                with col1:
                    voice = st.selectbox("Select voice", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"], key=f"voice_{len(st.session_state.messages)}")
                with col2:
                    if st.button("🔊 Listen", key=f"listen_{len(st.session_state.messages)}"):
                        with st.spinner("Generating audio..."):
                            audio_file_path = text_to_speech(message["content"], voice)
                        if audio_file_path:
                            st.audio(audio_file_path, format="audio/mp3")
                            # Clean up the temporary file
                            os.remove(audio_file_path)

    # Show booking process after AI response if hotels were suggested
    if st.session_state.get('show_booking', False):
        show_booking_process()

    # Updated chat input prompt
    if prompt := st.chat_input("How can I help you with your travel plans today?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            language = st.selectbox("Select response language", ["English", "Spanish", "French", "German", "Chinese", "Japanese"])
            for response in get_ai_response(prompt, st.session_state.user_preferences, language):
                response_placeholder.markdown(response + "▌")
            response_placeholder.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Check if hotels were suggested and set show_booking to True
        if st.session_state.get('suggested_hotels', []):
            st.session_state.show_booking = True

        st.rerun()

def show_booking_process():
    with st.expander("Book a Hotel", expanded=True):
        form_key = f"booking_form_{int(time.time())}_{random.randint(0, 1000)}"
        
        with st.form(form_key):
            st.subheader("Book Your Hotel")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Check-in date", value=datetime.now() + timedelta(days=30))
            with col2:
                end_date = st.date_input("Check-out date", value=start_date + timedelta(days=7))

            suggested_hotels = st.session_state.get('suggested_hotels', [])
            hotel_options = [
                {
                    "name": hotel,
                    "rating": random.randint(3, 5),
                    "price": random.randint(100, 500)
                } for hotel in suggested_hotels
            ]

            hotel_display = [f"{hotel['name']} - Rating: {hotel['rating']} stars, Price: ${hotel['price']}/night" for hotel in hotel_options]
            selected_hotel = st.selectbox("Select a hotel", options=hotel_display)

            if st.form_submit_button("Confirm Booking"):
                selected_hotel_info = hotel_options[hotel_display.index(selected_hotel)]
                total_nights = (end_date - start_date).days
                total_cost = selected_hotel_info['price'] * total_nights

                booking_details = {
                    "Hotel": selected_hotel_info['name'],
                    "Check-in": start_date.strftime("%Y-%m-%d"),
                    "Check-out": end_date.strftime("%Y-%m-%d"),
                    "Total nights": total_nights,
                    "Price per night": f"${selected_hotel_info['price']}",
                    "Total cost": f"${total_cost}"
                }

                st.session_state.confirmed_booking = booking_details
                st.session_state.show_booking = False
                confirm_booking_and_continue()
                st.rerun()

def confirm_booking_and_continue():
    booking = st.session_state.confirmed_booking
    prompt = f"""
    Great news! I've successfully booked your hotel. Here are the details:

    Hotel: {booking['Hotel']}
    Check-in: {booking['Check-in']}
    Check-out: {booking['Check-out']}
    Total nights: {booking['Total nights']}
    Price per night: {booking['Price per night']}
    Total cost: {booking['Total cost']}

    Is there anything else I can help you with for your trip? Perhaps you'd like to:
    1. Book an activity or tour
    2. Get restaurant recommendations
    3. Learn about local transportation options
    4. Discover more about the local culture and customs
    5. Find out about nearby attractions or day trip ideas

    What would you like to explore next?
    """
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        for response in get_ai_response(prompt, st.session_state.user_preferences):
            response_placeholder.markdown(response + "▌")
        response_placeholder.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Main app logic
if 'questionnaire_completed' not in st.session_state:
    st.session_state.questionnaire_completed = False

if not st.session_state.questionnaire_completed:
    initial_questionnaire()
else:
    main_chat_interface()
