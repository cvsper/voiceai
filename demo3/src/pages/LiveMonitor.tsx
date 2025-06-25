import React, { useEffect, useState } from 'react';
import { PhoneIcon, MicOffIcon, VolumeXIcon, UserIcon } from 'lucide-react';
const LiveMonitor: React.FC = () => {
  const [activeCalls, setActiveCalls] = useState([{
    id: 1,
    caller: '+1 (555) 123-4567',
    status: 'in-progress',
    duration: '00:01:23',
    transcript: [{
      speaker: 'AI',
      text: 'Hello, thank you for calling VoiceAI Solutions. How can I assist you today?',
      time: '00:00:05'
    }, {
      speaker: 'Caller',
      text: "Hi, I'm interested in scheduling a demo of your product.",
      time: '00:00:12'
    }, {
      speaker: 'AI',
      text: "I'd be happy to help you schedule a demo. Could you please provide your name?",
      time: '00:00:18'
    }, {
      speaker: 'Caller',
      text: 'My name is John Smith.',
      time: '00:00:22'
    }, {
      speaker: 'AI',
      text: 'Thank you, John. We have several available time slots next week. Would you prefer morning or afternoon?',
      time: '00:00:30'
    }, {
      speaker: 'Caller',
      text: 'Afternoon would be better for me.',
      time: '00:00:36'
    }, {
      speaker: 'AI',
      text: 'Great. We have availability on Tuesday at 2:00 PM, Wednesday at 3:30 PM, or Thursday at 1:00 PM. Which would work best for you?',
      time: '00:00:45'
    }, {
      speaker: 'Caller',
      text: 'Tuesday at 2:00 PM sounds perfect.',
      time: '00:00:52'
    }, {
      speaker: 'AI',
      text: "Excellent. I've scheduled a demo for Tuesday at 2:00 PM. Could I get your email address to send a confirmation?",
      time: '00:01:00'
    }, {
      speaker: 'Caller',
      text: "Yes, it's john.smith@example.com",
      time: '00:01:08'
    }, {
      speaker: 'AI',
      text: "Thank you. I've sent a calendar invite to john.smith@example.com. Is there anything else I can help you with today?",
      time: '00:01:18'
    }]
  }, {
    id: 2,
    caller: '+1 (555) 987-6543',
    status: 'in-progress',
    duration: '00:00:45',
    transcript: [{
      speaker: 'AI',
      text: 'Hello, thank you for calling VoiceAI Solutions. How can I assist you today?',
      time: '00:00:05'
    }, {
      speaker: 'Caller',
      text: 'I have a question about your pricing plans.',
      time: '00:00:12'
    }, {
      speaker: 'AI',
      text: "I'd be happy to go over our pricing plans with you. We offer several tiers based on call volume and features needed. Could you tell me a bit about your business needs?",
      time: '00:00:20'
    }, {
      speaker: 'Caller',
      text: "We're a small business with about 5-10 calls per day.",
      time: '00:00:30'
    }, {
      speaker: 'AI',
      text: 'For that volume, our Starter Plan would be a good fit. It includes AI call answering, basic scheduling, and call transcripts for $49 per month. Would you like more details about this plan?',
      time: '00:00:42'
    }]
  }]);
  const [selectedCall, setSelectedCall] = useState(activeCalls[0]);
  // Simulate real-time transcript updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (activeCalls.length > 0 && selectedCall) {
        const updatedCalls = activeCalls.map(call => {
          // Update duration
          const [min, sec] = call.duration.split(':').slice(1).map(Number);
          let newSec = sec + 1;
          let newMin = min;
          if (newSec >= 60) {
            newSec = 0;
            newMin++;
          }
          const newDuration = `00:${String(newMin).padStart(2, '0')}:${String(newSec).padStart(2, '0')}`;
          return {
            ...call,
            duration: newDuration
          };
        });
        setActiveCalls(updatedCalls);
        setSelectedCall(updatedCalls.find(call => call.id === selectedCall.id) || updatedCalls[0]);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [activeCalls, selectedCall]);
  return <div>
      <h1 className="mb-6 text-2xl font-bold">Live Monitor</h1>
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Active Calls List */}
        <div className="lg:col-span-1">
          <div className="rounded-lg bg-gray-800 p-6">
            <h2 className="mb-4 text-lg font-semibold">
              Active Calls ({activeCalls.length})
            </h2>
            {activeCalls.length > 0 ? <div className="space-y-3">
                {activeCalls.map(call => <div key={call.id} onClick={() => setSelectedCall(call)} className={`cursor-pointer rounded-lg border p-4 transition ${selectedCall?.id === call.id ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 bg-gray-750 hover:border-gray-600'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-3 rounded-full bg-blue-600/20 p-2">
                          <PhoneIcon className="h-4 w-4 text-blue-500" />
                        </div>
                        <div>
                          <p className="font-medium">{call.caller}</p>
                          <p className="text-sm text-gray-400">
                            {call.duration}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        <span className="mr-2 h-2 w-2 rounded-full bg-green-500"></span>
                        <span className="text-xs text-green-400">Live</span>
                      </div>
                    </div>
                  </div>)}
              </div> : <div className="flex h-32 flex-col items-center justify-center rounded-lg border border-dashed border-gray-700 p-6 text-center text-gray-400">
                <p>No active calls at the moment</p>
                <p className="mt-1 text-sm">Active calls will appear here</p>
              </div>}
          </div>
        </div>
        {/* Call Transcript */}
        <div className="lg:col-span-2">
          {selectedCall ? <div className="rounded-lg bg-gray-800">
              {/* Call Header */}
              <div className="border-b border-gray-700 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {selectedCall.caller}
                    </h2>
                    <p className="text-sm text-gray-400">
                      Duration: {selectedCall.duration}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button className="rounded-full bg-gray-700 p-2 hover:bg-gray-600" title="Mute">
                      <MicOffIcon className="h-5 w-5" />
                    </button>
                    <button className="rounded-full bg-gray-700 p-2 hover:bg-gray-600" title="Turn off speaker">
                      <VolumeXIcon className="h-5 w-5" />
                    </button>
                    <button className="rounded-full bg-red-600 p-2 hover:bg-red-700" title="End Call">
                      <PhoneIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
              {/* Live Transcript */}
              <div className="h-[500px] overflow-y-auto p-6">
                <div className="space-y-4">
                  {selectedCall.transcript.map((item, index) => <div key={index} className="flex">
                      <div className={`mr-4 mt-1 h-8 w-8 rounded-full ${item.speaker === 'AI' ? 'bg-blue-600' : 'bg-gray-700'} flex items-center justify-center`}>
                        {item.speaker === 'AI' ? <span className="text-xs font-bold">AI</span> : <UserIcon className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center">
                          <p className="font-medium">{item.speaker}</p>
                          <span className="ml-2 text-xs text-gray-400">
                            {item.time}
                          </span>
                        </div>
                        <p className="mt-1 text-gray-300">{item.text}</p>
                      </div>
                    </div>)}
                </div>
              </div>
              {/* Quick Actions */}
              <div className="border-t border-gray-700 p-4">
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-lg bg-blue-600 px-3 py-1 text-sm hover:bg-blue-700">
                    Book Appointment
                  </button>
                  <button className="rounded-lg bg-gray-700 px-3 py-1 text-sm hover:bg-gray-600">
                    Send Information
                  </button>
                  <button className="rounded-lg bg-gray-700 px-3 py-1 text-sm hover:bg-gray-600">
                    Transfer to Human
                  </button>
                </div>
              </div>
            </div> : <div className="flex h-full flex-col items-center justify-center rounded-lg border border-dashed border-gray-700 p-6 text-center text-gray-400">
              <p className="mb-2 text-lg">No call selected</p>
              <p>
                Select an active call from the list to view the live transcript
              </p>
            </div>}
        </div>
      </div>
    </div>;
};
export default LiveMonitor;