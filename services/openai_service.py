import openai
import json
import logging
from flask import current_app
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            openai.api_key = current_app.config['OPENAI_API_KEY']
            self.client = openai.OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def analyze_intent(self, transcript_text, conversation_history=None):
        """Analyze user intent from transcript"""
        try:
            # Build conversation context
            context = "You are an AI assistant analyzing customer service calls. "
            context += "Identify the customer's intent from their message. "
            context += "Common intents include: booking_appointment, cancel_appointment, "
            context += "reschedule_appointment, general_inquiry, complaint, pricing_info, "
            context += "service_info, technical_support, billing_inquiry.\n\n"
            
            if conversation_history:
                context += f"Previous conversation: {conversation_history}\n\n"
            
            context += f"Customer message: {transcript_text}\n\n"
            context += "Respond with a JSON object containing: intent, confidence (0-1), "
            context += "key_entities (list), suggested_response, and action_required."
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": transcript_text}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content.strip())
            
            return {
                'intent': result.get('intent', 'unknown'),
                'confidence': result.get('confidence', 0.0),
                'entities': result.get('key_entities', []),
                'suggested_response': result.get('suggested_response', ''),
                'action_required': result.get('action_required', False),
                'raw_response': response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                'intent': 'error',
                'confidence': 0.0,
                'entities': [],
                'suggested_response': "I'm sorry, I didn't understand that. Could you please repeat?",
                'action_required': False,
                'error': str(e)
            }
    
    def generate_response(self, user_input, intent_data, conversation_history=None):
        """Generate natural AI response based on intent"""
        try:
            # Build system prompt based on intent
            system_prompt = self._build_system_prompt(intent_data['intent'])
            
            # Build conversation context
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    messages.append({
                        "role": "user" if msg['speaker'] == 'caller' else "assistant",
                        "content": msg['text']
                    })
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            return {
                'response': response.choices[0].message.content.strip(),
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': "I apologize, but I'm having trouble processing your request right now. Could you please try again?",
                'tokens_used': 0,
                'error': str(e)
            }
    
    def extract_appointment_details(self, transcript_text):
        """Extract appointment booking details from conversation"""
        try:
            prompt = """
            Extract appointment booking details from this conversation.
            Look for: date, time, service type, duration, customer name, email, phone.
            
            Conversation: {transcript}
            
            Respond with JSON containing:
            - date: YYYY-MM-DD format
            - time: HH:MM format (24-hour)
            - service_type: string
            - duration_minutes: integer
            - customer_name: string
            - customer_email: string
            - customer_phone: string
            - notes: any additional information
            
            Use null for missing information.
            """.format(transcript=transcript_text)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts structured appointment data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=400
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error extracting appointment details: {e}")
            return None
    
    def _build_system_prompt(self, intent):
        """Build system prompt based on detected intent"""
        base_prompt = "You are a helpful AI assistant for a business. Be professional, concise, and friendly. "
        
        intent_prompts = {
            'booking_appointment': base_prompt + "Help the customer book an appointment. Ask for necessary details like date, time, and service type.",
            'cancel_appointment': base_prompt + "Help the customer cancel their appointment. Ask for booking reference or details to locate it.",
            'reschedule_appointment': base_prompt + "Help the customer reschedule their appointment. Get their current booking details and new preferred time.",
            'general_inquiry': base_prompt + "Answer general questions about the business, services, and policies.",
            'complaint': base_prompt + "Handle complaints professionally. Listen to concerns and offer appropriate solutions.",
            'pricing_info': base_prompt + "Provide pricing information for services. Be clear about costs and any additional fees.",
            'service_info': base_prompt + "Explain services offered, procedures, requirements, and what customers can expect.",
            'technical_support': base_prompt + "Provide technical assistance. Ask clarifying questions to understand the issue.",
            'billing_inquiry': base_prompt + "Help with billing questions. Explain charges, payment options, and resolve billing issues."
        }
        
        return intent_prompts.get(intent, base_prompt + "Assist the customer with their request to the best of your ability.")
    
    def summarize_call(self, transcripts):
        """Generate a summary of the entire call"""
        try:
            # Combine all transcripts
            full_conversation = "\n".join([
                f"{t['speaker']}: {t['text']}" for t in transcripts
            ])
            
            prompt = f"""
            Summarize this customer service call. Include:
            - Customer's main request/issue
            - Actions taken
            - Outcome
            - Any follow-up required
            - Key points discussed
            
            Conversation:
            {full_conversation}
            
            Provide a concise but comprehensive summary.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates concise call summaries for customer service."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing call: {e}")
            return "Unable to generate call summary."
    
    def generate_text(self, prompt, max_tokens=150):
        """Generate text response using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Be concise and professional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return "Hello! Thank you for calling. I'm your AI assistant. How can I help you today?"