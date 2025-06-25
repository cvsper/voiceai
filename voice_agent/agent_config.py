from config import Config

def get_voice_agent_config():
    """Configure Deepgram Voice Agent with function calling"""
    return {
        "model": "nova-2",
        "voice": "aura-2-amalthea-en",
        "prompt": """You are a professional AI receptionist. You are friendly, efficient, and helpful. 

You can help with:
- Booking appointments
- Checking availability
- Answering questions about services
- Taking messages

When booking appointments, always confirm the details with the caller before finalizing.
Be conversational and natural, but stay focused on helping the caller efficiently.""",
        
        "functions": [
            {
                "name": "book_appointment",
                "description": "Book an appointment for a customer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "Full name of the customer"
                        },
                        "customer_phone": {
                            "type": "string", 
                            "description": "Customer's phone number"
                        },
                        "appointment_date": {
                            "type": "string",
                            "description": "Date for appointment in YYYY-MM-DD format"
                        },
                        "appointment_time": {
                            "type": "string",
                            "description": "Time for appointment in HH:MM format (24-hour)"
                        },
                        "service_type": {
                            "type": "string",
                            "description": "Type of service requested"
                        }
                    },
                    "required": ["customer_name", "customer_phone", "appointment_date", "appointment_time"]
                }
            },
            {
                "name": "get_availability",
                "description": "Check available appointment slots for a given date",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date to check availability in YYYY-MM-DD format"
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "cancel_appointment",
                "description": "Cancel an existing appointment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference_id": {
                            "type": "string",
                            "description": "Appointment reference ID"
                        }
                    },
                    "required": ["reference_id"]
                }
            },
            {
                "name": "trigger_crm_webhook",
                "description": "Send data to CRM system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_type": {
                            "type": "string",
                            "description": "Type of CRM event (lead, appointment, message)"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to send to CRM"
                        }
                    },
                    "required": ["event_type", "data"]
                }
            }
        ]
    }