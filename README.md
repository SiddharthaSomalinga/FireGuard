# FireGuard

**Inspiration:**

Currently, there are wildfires in California which have been deadly for the past few days. In order to help support the initiative of combating these fires, we decided to develop a chatbot through the s(CASP) system and a trained machine learning model, as well as an embedded world, live fire map to help first responders and firefighters monitor these wildfires, take safety measures and combat them while decreasing casualties in areas. These programs help determine critical information that aids firefighters and emergency responders in combating these fires and organizing resources and evacuations.

**How it works:**

This program calculates fire behavior metrics using established fire science equations such as the Rothermel and Byram equations that determine fire intensity, flame length, and flame height. We have also used equations that compute the required safety zone distances to protect firefighters and calculate the burn area and the escape time. Our program also evaluates areas considering a number of risk factors like fuel conditions, weather, topography, population density, infrastructure, etc. This program also provides recommendations for evacuation status and resource deployment by level of risk using the National Fire Danger Rating System (NFDRS) and creates a priority list that emergency responders and medical personnel can use. We also used Negation as Failure (NAF) at different levels of the fire to make sure certain conditions were not present at certain fire levels. All these features are implemented through a chatbot interface, where the user can enter information and immediately receive information on the risk level, resources needed, etc. The machine learning model uses a dataset from 2012 that provides key metrics that correlate to a fire occurring and is presented in a clean UI interface by utilizing the Streamlit library in Python for ease of use. The map uses data from NASA FIRMS and shows critical details about fires across the USA and the world.

**How we built it:**

The system was developed through the implementation of scientific fire behavior models and integrated with a wide-ranging risk assessment framework. We implemented core fire behavior calculations, including the Rothermel equation for the rate of fire spread and the Byram equation for fireline intensity, and then developed a multi-factor risk classification system that considers environmental conditions like fuel moisture, temperature, humidity, wind speed-geographical features topography, and human factors-issues such as population density and critical infrastructure. The system uses these inputs to classify areas into five risk levels (Low, Medium, High, Very High, and Extreme) and provides specific recommendations for evacuation and resource allocation. We also have several features that firefighters and fire departments can use to help determine fireline intensity, flame length and height, safety zones, burn area and escape time so that fire departments can make their work more efficient. The machine learning model was built by training the model on the dataset and using the Random Forest Algorithm in Machine Learning to predict the likelihood of a wildfire, achieving an accuracy of 95%. We also integrated a world live fire map that shows details about fires across the USA and the world.

**Challenges we ran into:**

These are some of the challenges we ran into: implementing complex fire behavior equations while maintaining accuracy, creating a balanced risk classification system that properly weighs multiple factors, developing clear decision rules for evacuation and resource deployment recommendations, ensuring the system remains efficient while processing multiple areas simultaneously and deploying the machine learning model through Streamlit.

**Accomplishments That We're Proud Of:**

We are proud that we were able to successfully integrate scientific fire behavior models and equations into an s(CASP) application through a chatbot that reflects human reasoning and common sense and provides a flexible and complete risk assessment system that provides clear, actionable output for first responders and critical information for firefighters and fire departments as well as multiple area analysis with sorted risk assessments based on the level of fire risk different areas have. We are also proud that we were able to provide a machine-learning model that can predict the likelihood of fire based on historical data. We are also proud to provide a map that users can use to get up-to-date details about fires in their proximity.

**What we learned:**

We learned about fire behavior modeling, combining multiple environmental and social factors into a single risk assessment through a chatbot interface, the Random Forest machine learning algorithm, and implementing scientific equations in a practical emergency management system that is relevant to today’s society due to the ongoing fires in California.


**What's next for FireGuard:**

We hope to integrate real-time weather data to calculate more real-time data and collaborate with AI companies that provide video feeds so we can develop a machine-learning model that can better help combat fires in the future. We also hope to use real-world sensors that collect data on fuel content and integrate that into the machine learning model, as well as train the model on more datasets to improve accuracy further.

**Setup Instructions:**

Running machine learning model directly from the link above: Download the forest fire dataset, upload the dataset on the website, select prediction on the target column, click train model based on desired test size and desired number of trees, and then enter in inputs and click predict.

Cloning the repository and running it locally: Download or clone the repository from Github. Install all the required libraries as shown in the app.py file. After that, go to the terminal and run the command streamlit run app.py, and the application should open locally in a new window.

s(CASP) chatbot: To run the prolog file, use the SWI-Prolog interpreter online or any other Prolog or s(CASP) interpreter and run "chatbot." to get the chatbot ui and "priority_list(OrderedResults)." to get the priority list based on the test cases.
