from flask import Flask, request, jsonify
import pandas as pd
from head import main1
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/search', methods=['POST'])


def search_rentals():
    try:
        # Get JSON data from the POST request
        data = request.json
        app.logger.debug(f"Received data: {data}")  # Log the incoming data

        address = data.get("address")
        radius = int(data.get("radius", 2000))  # Default to 2000 meters
        limit = int(data.get("limit", 20))      # Default to 20 results

        if not address:
            return jsonify({"error": "Address is required."}), 400

        # Call the main function to get the DataFrame result
        df_result = main1(address, radius, limit)
        df_result = df_result.fillna(0)  #new preprocessing for handling json import errors


        # Convert DataFrame to JSON for the frontend
        result_json = df_result.to_dict(orient="records")
        return jsonify(result_json), 200
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")  # Log the error
        return jsonify({"error": str(e)}), 500


    


if __name__ == '__main__':
    app.run(debug=True)
