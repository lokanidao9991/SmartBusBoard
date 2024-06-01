from flask import Flask, render_template, request, redirect, url_for, jsonify
import configparser
import os
import pandas as pd

app = Flask(__name__)

# Path to the config.ini file
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

# Path to the CSV file with stop information
stops_csv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Betriebspunkt.csv')

# Inspect the first few lines of the CSV file
try:
    with open(stops_csv_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        print("CSV Raw Lines:")
        for line in lines[:5]:
            print(line.strip())
except Exception as e:
    print(f"Error reading CSV file: {e}")

# Load stops from the CSV file
try:
    stops_df = pd.read_csv(stops_csv_path, delimiter=',', encoding='utf-8')
    print("CSV loaded successfully")
    print("Data Frame Columns: ", stops_df.columns)
    print("Data Frame Head: ", stops_df.head())
except Exception as e:
    print(f"Error loading CSV: {e}")

@app.route('/')
def index():
    config = configparser.ConfigParser()
    config.read(config_path)
    settings = config['Settings']
    return render_template('index.html', settings=settings)

@app.route('/update', methods=['POST'])
def update():
    stop_point_ref = request.form['stop_point_ref']
    stop_title = request.form['stop_title']
    number_of_results = request.form['number_of_results']
    desired_destinations = request.form['desired_destinations']
    threshold = request.form['threshold']

    config = configparser.ConfigParser()
    config.read(config_path)
    config['Settings']['stop_point_ref'] = stop_point_ref
    config['Settings']['stop_title'] = stop_title
    config['Settings']['number_of_results'] = number_of_results
    config['Settings']['desired_destinations'] = desired_destinations
    config['Settings']['threshold'] = threshold

    with open(config_path, 'w') as configfile:
        config.write(configfile)

    return redirect(url_for('index'))

@app.route('/stops', methods=['GET'])
def get_stops():
    try:
        stops = stops_df.to_dict(orient='records')
        stops_autocomplete = [{"label": stop["Name"], "value": stop["Nummer"]} for stop in stops]
        return jsonify(stops_autocomplete)
    except KeyError as e:
        print(f"KeyError: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/update_stop', methods=['POST'])
def update_stop():
    ref = request.json.get('ref')
    stop_title = request.json.get('title')
    config = configparser.ConfigParser()
    config.read(config_path)
    config['Settings']['stop_point_ref'] = ref
    config['Settings']['stop_title'] = stop_title
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    return jsonify({"message": "Configuration updated"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
