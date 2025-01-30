import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError
import matplotlib.pyplot as plt
import seaborn as sns

# Set page configuration
st.set_page_config(page_title="Forest Fire Prediction", layout="wide")

# Title of the app
st.title("Forest Fire Prediction using Random Forest")

# Embed ArcGIS map using iframe HTML
st.markdown("""
    <iframe src="https://firemap.live/" 
            width="100%" height="600px">
    </iframe>
""", unsafe_allow_html=True)

# Sidebar for uploading dataset
st.sidebar.header("Upload Dataset")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    # Load dataset
    df = pd.read_csv(uploaded_file)

    # Display the dataset preview
    st.subheader("Dataset Preview")

    # Ensure year column is displayed as integers without formatting
    if "Year" in df.columns:  # Replace "Year" with the actual column name, if different
        df["Year"] = df["Year"].astype(int)

    # Format the 'Year' column to ensure no commas in display
    df['Year'] = df['Year'].apply(lambda x: f"{x:.0f}")  # Remove comma formatting by converting to string

    st.dataframe(df.head())

    # Strip extra spaces from column names
    df.columns = df.columns.str.strip()

    # Input to select the target column
    target_column = st.sidebar.selectbox("Select Target Column", options=df.columns)

    # Check for non-numeric columns
    exclude_columns = [target_column]
    for col in df.columns:
        if col not in exclude_columns:
            try:
                pd.to_numeric(df[col], errors="raise")
            except ValueError:
                pass

    # Convert all numeric columns
    df = df.apply(lambda x: pd.to_numeric(x, errors="coerce") if x.name != target_column else x)

    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].apply(lambda col: col.fillna(col.mean()))

    # Ensure target column is categorical
    df[target_column] = df[target_column].astype(str)

    # Define feature and target variables
    X = df.drop(target_column, axis=1)
    y = df[target_column]

    # Split dataset
    test_size = st.sidebar.slider("Test Size (Fraction)", 0.1, 0.5, 0.2)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    # Standardize feature data
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Initialize model_trained flag and rf_model in session_state
    if 'model_trained' not in st.session_state:
        st.session_state.model_trained = False
    if 'rf_model' not in st.session_state:
        st.session_state.rf_model = None

    # Train Random Forest Classifier
    n_estimators = st.sidebar.slider("Number of Trees (n_estimators)", 50, 500, 100)
    rf_model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)

    if st.sidebar.button("Train Model"):
        rf_model.fit(X_train, y_train)
        st.session_state.rf_model = rf_model  # Save the trained model in session state
        st.session_state.model_trained = True  # Set the model_trained flag to True
        y_pred = rf_model.predict(X_test)

        # Evaluate the model
        st.subheader("Model Evaluation")
        st.write(f"**Accuracy:** {accuracy_score(y_test, y_pred):.2f}")

        # Feature Importance
        st.subheader("Feature Importance")
        feature_importance = rf_model.feature_importances_
        features = X.columns
        importance_df = pd.DataFrame({"Feature": features, "Importance": feature_importance}).sort_values(
            by="Importance", ascending=False)

        # Display Feature Importance
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="Importance", y="Feature", data=importance_df, palette="viridis", ax=ax)
        ax.set_title("Feature Importance in Forest Fire Prediction")
        ax.set_xlabel("Importance")
        ax.set_ylabel("Feature")
        st.pyplot(fig)

    # Input form for prediction
    st.header("Predict Forest Fire")
    st.subheader("Enter Feature Values for Prediction")
    user_input = {}

    # Create number input fields for each feature on the main page
    for feature in X.columns:
        user_input[feature] = st.number_input(f"Enter {feature}", value=float(X[feature].mean()))

    # Prediction button on the main page
    if st.button("Predict"):
        if not st.session_state.model_trained:
            st.error("The model is not trained yet. Please train the model before making predictions.")
        else:
            # Retrieve the trained model
            rf_model = st.session_state.rf_model

            # Create a DataFrame for the user input
            input_df = pd.DataFrame([user_input])

            # Check if there are any missing values and handle them (fill with column means, similar to training data preprocessing)
            input_df = input_df.apply(lambda x: x.fillna(x.mean()) if x.name != target_column else x)

            # Apply the same scaling transformation as used on the training data
            input_scaled = scaler.transform(input_df)

            try:
                # Make prediction
                prediction = rf_model.predict(input_scaled)

                # Debugging: Output raw prediction
                #st.write(f"Prediction Array: {prediction}")

                # Strip any leading/trailing whitespace from the prediction
                cleaned_prediction = prediction[0].strip()

                # Map prediction to Fire/No Fire based on the class labels
                fire_prediction = "Fire" if cleaned_prediction.lower() == 'fire' else "No Fire"

                st.subheader("Prediction Results")
                st.write(f"Prediction: **{fire_prediction}**")
            except NotFittedError:
                st.error("The model is not trained yet. Please train the model before making predictions.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
