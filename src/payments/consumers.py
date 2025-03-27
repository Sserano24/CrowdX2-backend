 # payments/consumers.py

import json
from channels.generic.websocket import WebsocketConsumer

class PaymentStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = 'payment_status'
        self.accept()

        # Add the WebSocket to the group
        self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        # Remove the WebSocket from the group
        self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', 'No message received')

        # Broadcast the message to the group
        self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_status',
                'message': f'Received: {message}'
            }
        )

    def send_status(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': event['message']
        }))
