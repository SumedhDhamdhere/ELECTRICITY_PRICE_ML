from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
import pandas as pd
import numpy as np
import pickle
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a more secure secret key

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['electric_forecast']
users_collection = db['users']

# Load the pre-trained Prophet model
with open('model.pkl', 'rb') as f:
    loaded_model = pickle.load(f)

@ app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@ app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@ app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = users_collection.find_one({'username': username})
        if not existing_user:
            users_collection.insert_one({'username': username, 'password': password})
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('signup.html', error='Username already exists')
    return render_template('signup.html')

@ app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@ app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Get the start and end dates from the form
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # Create a DataFrame with the date range
        prediction_dates = pd.date_range(start=start_date, end=end_date, freq='D')  # Assuming daily frequency
        prediction_df = pd.DataFrame({'ds': prediction_dates})

        # Make predictions using the loaded model
        prediction_result = loaded_model.predict(prediction_df)

        # Extract the predicted consumption values
        predicted_values = np.exp(prediction_result['yhat'])

        # Create a table of predicted values
        predicted_table = pd.DataFrame({
            'date': prediction_dates,
            'predicted_value': predicted_values
        })

        # Sum up the predicted values
        total_predicted_value = predicted_values.sum()

        # Pass the result to the HTML template
        return render_template('index.html', start_date=start_date, end_date=end_date, total_predicted_value=total_predicted_value, predicted_table=predicted_table.to_dict(orient='records'))

@ app.route('/chart_data/<start_date>/<end_date>')
def chart_data(start_date, end_date):
    # Create a DataFrame with the date range
    prediction_dates = pd.date_range(start=start_date, end=end_date, freq='D')  # Assuming daily frequency
    prediction_df = pd.DataFrame({'ds': prediction_dates})

    # Make predictions using the loaded model
    prediction_result = loaded_model.predict(prediction_df)

    # Extract the predicted consumption values
    predicted_values = np.exp(prediction_result['yhat'])

    # Create a dictionary with chart data
    chart_data = {
        'labels': prediction_dates.strftime('%Y-%m-%d').tolist(),
        'data': predicted_values.tolist(),
    }

    # Return JSON response
    return jsonify(chart_data)

if __name__ == '__main__':
    app.run(debug=True)
