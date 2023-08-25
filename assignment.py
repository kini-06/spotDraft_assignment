#Technology used: ASANA, AIRTABLE, FLASK, POSTMAN, NGROK

#Flask is commonly used to build web APIs (Application Programming Interfaces) that allow different software systems to communicate with each other over the web.
#Postman is a widely used API development and testing tool that provides a user-friendly interface for making API requests, creating and managing collections of requests, and automating workflows.
#ngrok is a tool that creates secure tunnels from a public internet endpoint to a locally running web service. It's commonly used during development and testing to expose a local server to the internet temporarily


from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

@app.route('/webhook/asana', methods=['POST'])
def asana_webhook():
    print('request.headers:', request.headers)
    ASANA_TOKEN = 'asana personal access token'

    # Airtable API settings
    AIRTABLE_TOKEN = "airtable token"
    AIRTABLE_BASE_ID = "base id"
    AIRTABLE_TABLE_NAME = "Table"

    #The X-Hook-Secret is a security token used in webhook communication. It's sent by the sender during the setup phase and echoed back by the receiver to confirm authenticity. This prevents unauthorized parties from impersonating the receiver
    if 'X-Hook-Secret' in request.headers:
        print('inside if:', request.headers['X-Hook-Secret'])
        handshake_secret = request.headers['X-Hook-Secret']
        data = {'X-Hook-Secret': handshake_secret}
        response = make_response(jsonify(data), 200)
        response.headers['X-Hook-Secret'] = handshake_secret
        print('resp---', response)
        return response
    #status code is 200 only if  handshake is successful

    event_data = request.json
    # Handle the received event (e.g., new task created in Asana)
    print('Received Asana webhook event:', event_data)
    new_task_event = None

    # Find the event where action is 'added' and resource type is 'task'
    for event in event_data['events']:
        if event['action'] == 'added' and event['resource']['resource_type'] == 'task':
            new_task_event = event
            break

    print('New task event-------', new_task_event)
    if new_task_event:
        task_gid = new_task_event['resource']['gid']
        print('task gid', task_gid)
        # Make API request to get task details
        task_url = f'https://app.asana.com/api/1.0/tasks/{task_gid}'
        headers = {'Authorization': f'Bearer {ASANA_TOKEN}'}
        response = requests.get(task_url, headers=headers)
        print('task resp------', response)

        if response.status_code == 200:            
            task_details = response.json().get('data')
            airtable_data = {"fields":{}}

            # Extract relevant task information
            if task_details is not None:
                airtable_data["fields"]['Task ID'] = task_details.get('gid')
                airtable_data["fields"]['Name'] = task_details.get('name')            
                airtable_data["fields"]['Assignee'] = task_details.get('assignee', {}).get('name')
                airtable_data["fields"]['Due Date'] = task_details.get('due_on')
                airtable_data["fields"]['Description'] = task_details.get('notes')
            

            print(f'airtable_data: {airtable_data}')

            #Create task in Airtable
            airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
            headers = {
                "Authorization": f"Bearer {AIRTABLE_TOKEN}",
                "Content-Type": "application/json"
            }
            print('airtable_url', airtable_url, headers, json.dumps(airtable_data))
            response = requests.post(airtable_url, headers=headers, data=json.dumps(airtable_data))
            print('response from airtable')
            if response.status_code == 200:
                return jsonify({"message": "Task copied to Airtable successfully"}), 200
            else:
                return jsonify({"message": "Error copying task to Airtable"}), response.status_code
        else:
            print(f'Failed to retrieve task details. Status Code: {response.status_code}')

    return jsonify({'message': 'Webhook received successfully'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    #specifying to run on port 5000