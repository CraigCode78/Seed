import streamlit as st
from openai import OpenAI
import os
import random
from datetime import datetime, timedelta

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def get_ai_response(prompt, user_preferences, booking_stage=None):
    try:
        system_message = f"You are an expert AI travel concierge. Provide detailed, informative, and engaging responses about travel destinations, cultural insights, local customs, travel tips, and personalized recommendations. Consider the user's preferences: {user_preferences}."
        
        if booking_stage:
            system_message += f" The user is currently in the booking process at stage: {booking_stage}. Guide them through this stage and ask for necessary information."
        
        messages = [
            {"role": "system", "content": system_message},
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

def display_flight_options():
    st.subheader("Available Flights")
    for i, flight in enumerate(mock_flights):
        st.write(f"{i+1}. {flight['airline']} - Departure: {flight['departure']}, Arrival: {flight['arrival']}, Price: ${flight['price']}")
    choice = st.selectbox("Select a flight", options=[1, 2, 3])
    return mock_flights[choice-1]

def display_hotel_options():
    st.subheader("Available Hotels")
    for i, hotel in enumerate(mock_hotels):
        st.write(f"{i+1}. {hotel['name']} - Rating: {hotel['rating']} stars, Price: ${hotel['price']}/night")
    choice = st.selectbox("Select a hotel", options=[1, 2, 3])
    return mock_hotels[choice-1]

def simulate_booking_process():
    if 'booking_stage' not in st.session_state:
        st.session_state.booking_stage = 'destination'

    if st.session_state.booking_stage == 'destination':
        st.subheader("Where would you like to go?")
        destination = st.text_input("Enter your destination")
        if st.button("Next"):
            st.session_state.destination = destination
            st.session_state.booking_stage = 'dates'
            st.rerun()

    elif st.session_state.booking_stage == 'dates':
        st.subheader("When would you like to travel?")
        start_date = st.date_input("Start date", datetime.now() + timedelta(days=30))
        end_date = st.date_input("End date", start_date + timedelta(days=7))
        if st.button("Next"):
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.booking_stage = 'flight'
            st.rerun()

    elif st.session_state.booking_stage == 'flight':
        st.subheader("Let's choose a flight")
        selected_flight = display_flight_options()
        if st.button("Book Flight"):
            st.session_state.selected_flight = selected_flight
            st.session_state.booking_stage = 'hotel'
            st.rerun()

    elif st.session_state.booking_stage == 'hotel':
        st.subheader("Now, let's choose a hotel")
        selected_hotel = display_hotel_options()
        if st.button("Book Hotel"):
            st.session_state.selected_hotel = selected_hotel
            st.session_state.booking_stage = 'confirmation'
            st.rerun()

    elif st.session_state.booking_stage == 'confirmation':
        st.subheader("Booking Confirmation")
        st.write(f"Destination: {st.session_state.destination}")
        st.write(f"Dates: {st.session_state.start_date} to {st.session_state.end_date}")
        st.write(f"Flight: {st.session_state.selected_flight['airline']} - ${st.session_state.selected_flight['price']}")
        st.write(f"Hotel: {st.session_state.selected_hotel['name']} - ${st.session_state.selected_hotel['price']}/night")
        total_cost = st.session_state.selected_flight['price'] + (st.session_state.selected_hotel['price'] * (st.session_state.end_date - st.session_state.start_date).days)
        st.write(f"Total Cost: ${total_cost}")
        if st.button("Confirm Booking"):
            st.success("Booking confirmed! (This is a simulation, no actual booking has been made)")
            st.session_state.booking_stage = 'completed'

    return st.session_state.booking_stage

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

    # Simulate booking process
    booking_stage = simulate_booking_process()

    # React to user input
    if prompt := st.chat_input("What would you like to know about travel?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            for response in get_ai_response(prompt, st.session_state.user_preferences, booking_stage):
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
