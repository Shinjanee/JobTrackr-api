from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_cors import CORS
from datetime import datetime, timedelta
import requests
from openai_client import gpt_client

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "YOUR_MONGO_URI"
mongo = PyMongo(app)

applications = mongo.db.applications
users = mongo.db.users

@app.route('/applications/<string:user_id>', methods=['GET'])
def get_applications(user_id):
    result = []
    for application in applications.find({"userId": user_id}):
        result.append({
            '_id': str(application['_id']),
            'companyName': application['companyName'],
            'jobLink': application['jobLink'],
            'position': application['position'],
            'status': application['status']
        })
    return jsonify(result)

@app.route('/applications', methods=['POST'])
def add_application():
    application_data = request.get_json()
    new_application = {
        'userId': application_data['userId'],
        'companyName': application_data['companyName'],
        'jobLink': application_data['jobLink'],
        'position': application_data['position'],
        'status': application_data['status']
    }
    applications.insert_one(new_application)
    return jsonify({'result': 'Application added'}), 200


@app.route('/applications/<id>', methods=['PUT'])
def update_application(id):
    application = applications.find_one({'_id': ObjectId(id)})
    if not application:
        return jsonify({'error': 'Application not found'})

    update_data = {
        'companyName': request.json.get('companyName', application['companyName']),
        'jobLink': request.json.get('jobLink', application['jobLink']),
        'position': request.json.get('position', application['position']),
        'status': request.json.get('status', application['status'])
    }
    applications.update_one({'_id': ObjectId(id)}, {'$set': update_data})
    return jsonify({'result': 'Application updated'})

@app.route('/applications/<id>', methods=['DELETE'])
def delete_application(id):
    application = applications.find_one({'_id': ObjectId(id)})
    if not application:
        return jsonify({'error': 'Application not found'})

    applications.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'Application deleted'})

def reset_tries(user):
    time_difference = datetime.utcnow() - user['last_update']
    if user['tries'] == 0 and time_difference > timedelta(hours=2):
        user['tries'] = 5
        user['last_update'] = datetime.utcnow()
        users.update_one({'userId': user['userId']}, {'$set': {'tries': user['tries'], 'last_update': user['last_update']}})

@app.route('/users/tries/reset/<string:user_id>', methods=['GET'])
def get_reset_tries(user_id):
    user = users.find_one({"userId": user_id})
    if user:
        reset_tries(user)
        return jsonify({'tries': user['tries']}), 200
    else:
        new_user = {'userId': user_id, 'resumeText':'', 'tries': 5, 'last_update': datetime.utcnow()}
        users.insert_one(new_user)
        return jsonify({'tries': new_user['tries']})
    
@app.route('/users/tries/<string:user_id>', methods=['PUT'])
def update_user_tries(user_id):
    user = users.find_one({"userId": user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_tries = request.json.get('tries')
    users.update_one({'userId': user_id}, {'$set': {'tries': new_tries}})
    return jsonify({'result': 'Tries updated'})

@app.route('/users/openai/<string:user_id>', methods=['POST'])
def call_openai_api(user_id):
    resume_response, status_code = get_resume(user_id)
    if status_code == 200:
        resume_text = resume_response.json['resumeText']
    else:
        return jsonify({'error': 'Failed to fetch resume'}), 500

    input_text = request.json.get('inputText')
    message = [
        {"role":"user", "content": "Is this resume a good fit for the given job description? \n\nResume:\n" + resume_text + ".\n\n Job description.\n" + input_text}
    ]
    try:
        reply, total_tokens = gpt_client.generate_reply(message)
        return jsonify({'reply': reply, 'total_tokens': total_tokens}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/users/resume/<string:user_id>', methods=['GET'])
def get_resume(user_id):
    user = users.find_one({"userId": user_id})
    if not user:
        new_user = {'userId': user_id, 'resumeText': '', 'tries': 5, 'last_update': datetime.utcnow()}
        users.insert_one(new_user)
        return jsonify({'resumeText': user['resumeText']}), 200
    elif user and 'resumeText' in user:
        return jsonify({'resumeText': user['resumeText']}), 200
    else:
        return jsonify({'resumeText': ''}), 200

@app.route('/users/resume/<string:user_id>', methods=['POST'])
def save_resume(user_id):
    user = users.find_one({"userId": user_id})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    resume_text = request.json.get('resumeText')
    users.update_one({'userId': user_id}, {'$set': {'resumeText': resume_text}})
    return jsonify({'result': 'Resume saved/updated'})

if __name__ == '__main__':
    app.run(debug=True)
