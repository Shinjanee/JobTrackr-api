from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb+srv://shinjanee18:Qwerty123@cluster0.is9eero.mongodb.net/track_applications?retryWrites=true&w=majority"
mongo = PyMongo(app)

applications = mongo.db.applications

@app.route('/applications', methods=['GET'])
def get_applications():
    result = []
    for application in applications.find():
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
    new_application = {
        'companyName': request.json['companyName'],
        'jobLink': request.json['jobLink'],
        'position': request.json['position'],
        'status': request.json['status']
    }
    applications.insert_one(new_application)
    return jsonify({'result': 'Application added'})

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

if __name__ == '__main__':
    app.run(debug=True)
