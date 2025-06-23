import React, { useState } from 'react';
import { SaveIcon, UserIcon, CalendarIcon, LinkIcon, MessageCircleIcon, ClockIcon } from 'lucide-react';
const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('business');
  const tabs = [{
    id: 'business',
    label: 'Business Info',
    icon: UserIcon
  }, {
    id: 'ai',
    label: 'AI Personality',
    icon: MessageCircleIcon
  }, {
    id: 'calendar',
    label: 'Calendar',
    icon: CalendarIcon
  }, {
    id: 'integrations',
    label: 'Integrations',
    icon: LinkIcon
  }, {
    id: 'hours',
    label: 'Business Hours',
    icon: ClockIcon
  }];
  return <div>
      <h1 className="mb-6 text-2xl font-bold">Settings</h1>
      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="rounded-lg bg-gray-800 p-4">
            <nav className="space-y-1">
              {tabs.map(tab => <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex w-full items-center rounded-lg px-4 py-3 text-left text-sm transition ${activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}>
                  <tab.icon className="mr-3 h-5 w-5" />
                  <span>{tab.label}</span>
                </button>)}
            </nav>
          </div>
        </div>
        {/* Content */}
        <div className="lg:col-span-3">
          <div className="rounded-lg bg-gray-800 p-6">
            {activeTab === 'business' && <div>
                <h2 className="mb-6 text-lg font-semibold">
                  Business Information
                </h2>
                <form>
                  <div className="mb-4 grid gap-6 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-400">
                        Business Name
                      </label>
                      <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="VoiceAI Solutions" />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-400">
                        Phone Number
                      </label>
                      <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="+1 (555) 123-4567" />
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-400">
                      Business Description
                    </label>
                    <textarea className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" rows={4} defaultValue="We provide professional web design and development services for small businesses." />
                    <p className="mt-1 text-xs text-gray-400">
                      This will be used by the AI to describe your business to
                      callers.
                    </p>
                  </div>
                  <div className="mb-4 grid gap-6 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-400">
                        Email Address
                      </label>
                      <input type="email" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="contact@voiceai.example.com" />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-400">
                        Website
                      </label>
                      <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="https://voiceai.example.com" />
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-400">
                      Business Address
                    </label>
                    <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="123 Business St, Suite 101, San Francisco, CA 94107" />
                  </div>
                  <div className="mt-6 flex justify-end">
                    <button type="button" className="flex items-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">
                      <SaveIcon className="mr-2 h-4 w-4" />
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>}
            {activeTab === 'ai' && <div>
                <h2 className="mb-6 text-lg font-semibold">
                  AI Personality Settings
                </h2>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    AI Voice
                  </label>
                  <select className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none">
                    <option>Professional Female (Default)</option>
                    <option>Professional Male</option>
                    <option>Friendly Female</option>
                    <option>Friendly Male</option>
                  </select>
                </div>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    AI Name
                  </label>
                  <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" defaultValue="Alex" />
                  <p className="mt-1 text-xs text-gray-400">
                    This is how the AI will introduce itself to callers.
                  </p>
                </div>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    Greeting Script
                  </label>
                  <textarea className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" rows={3} defaultValue="Hello, thank you for calling VoiceAI Solutions. This is Alex, how may I assist you today?" />
                </div>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    Personality Style
                  </label>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {['Professional', 'Friendly', 'Casual', 'Formal'].map(style => <div key={style} className="flex items-center">
                          <input type="radio" id={`style-${style.toLowerCase()}`} name="personality-style" className="h-4 w-4 border-gray-700 bg-gray-900 text-blue-600" defaultChecked={style === 'Professional'} />
                          <label htmlFor={`style-${style.toLowerCase()}`} className="ml-2 text-sm">
                            {style}
                          </label>
                        </div>)}
                  </div>
                </div>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    Response Speed
                  </label>
                  <input type="range" min="1" max="5" defaultValue="3" className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-700 accent-blue-600" />
                  <div className="mt-1 flex justify-between text-xs text-gray-400">
                    <span>Faster</span>
                    <span>Balanced</span>
                    <span>Slower</span>
                  </div>
                </div>
                <div className="mt-6 flex justify-end">
                  <button type="button" className="flex items-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">
                    <SaveIcon className="mr-2 h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </div>}
            {activeTab === 'calendar' && <div>
                <h2 className="mb-6 text-lg font-semibold">
                  Calendar Integration
                </h2>
                <div className="mb-6">
                  <label className="mb-2 block text-sm font-medium text-gray-400">
                    Calendar Provider
                  </label>
                  <select className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none">
                    <option>Google Calendar</option>
                    <option>Microsoft Outlook</option>
                    <option>Apple Calendar</option>
                    <option>Calendly</option>
                  </select>
                </div>
                <div className="mb-6 rounded-lg border border-blue-700 bg-blue-900/20 p-4">
                  <div className="flex items-start">
                    <div className="mr-3 rounded-full bg-blue-600/20 p-2">
                      <CalendarIcon className="h-5 w-5 text-blue-500" />
                    </div>
                    <div>
                      <h3 className="font-medium">Google Calendar Connected</h3>
                      <p className="mt-1 text-sm text-gray-300">
                        Connected as user@example.com
                      </p>
                      <button className="mt-2 text-sm text-blue-400 hover:text-blue-300">
                        Disconnect
                      </button>
                    </div>
                  </div>
                </div>
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-medium">
                    Appointment Settings
                  </h3>
                  <div className="mb-4 grid gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-xs text-gray-400">
                        Default Appointment Duration
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
                        <option>15 minutes</option>
                        <option>30 minutes</option>
                        <option selected>45 minutes</option>
                        <option>60 minutes</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-2 block text-xs text-gray-400">
                        Buffer Between Appointments
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
                        <option>None</option>
                        <option>5 minutes</option>
                        <option selected>10 minutes</option>
                        <option>15 minutes</option>
                      </select>
                    </div>
                  </div>
                  <div className="mb-4">
                    <label className="mb-2 block text-xs text-gray-400">
                      Appointment Types
                    </label>
                    <div className="space-y-2">
                      <div className="flex items-center">
                        <input type="checkbox" className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-blue-600" defaultChecked />
                        <span className="ml-2 text-sm">
                          Initial Consultation (45 min)
                        </span>
                      </div>
                      <div className="flex items-center">
                        <input type="checkbox" className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-blue-600" defaultChecked />
                        <span className="ml-2 text-sm">
                          Follow-up Meeting (30 min)
                        </span>
                      </div>
                      <div className="flex items-center">
                        <input type="checkbox" className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-blue-600" defaultChecked />
                        <span className="ml-2 text-sm">
                          Quick Call (15 min)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex justify-end">
                  <button type="button" className="flex items-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">
                    <SaveIcon className="mr-2 h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </div>}
            {activeTab === 'integrations' && <div>
                <h2 className="mb-6 text-lg font-semibold">Integrations</h2>
                <div className="mb-6 space-y-4">
                  <div className="rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-3 h-10 w-10 rounded-full bg-white p-2">
                          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="#FF5A5F">
                            <path d="M22.5 12c0 5.799-4.701 10.5-10.5 10.5S1.5 17.799 1.5 12 6.201 1.5 12 1.5 22.5 6.201 22.5 12zm-9.75-3v6.75a.75.75 0 0 1-1.5 0V9.749l-2.22 2.22a.75.75 0 0 1-1.06-1.06l3.5-3.5a.75.75 0 0 1 1.06 0l3.5 3.5a.75.75 0 1 1-1.06 1.06l-2.22-2.22z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="font-medium">HubSpot CRM</h3>
                          <p className="text-sm text-gray-400">
                            Connect to automatically create contacts and log
                            calls
                          </p>
                        </div>
                      </div>
                      <div>
                        <button className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1 text-sm hover:bg-gray-700">
                          Connect
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-3 h-10 w-10 rounded-full bg-[#1da1f2] p-2 flex items-center justify-center text-white font-bold">
                          S
                        </div>
                        <div>
                          <h3 className="font-medium">Salesforce</h3>
                          <p className="text-sm text-gray-400">
                            Sync leads and call data with Salesforce
                          </p>
                        </div>
                      </div>
                      <div>
                        <button className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1 text-sm hover:bg-gray-700">
                          Connect
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-3 h-10 w-10 rounded-full bg-[#3b5998] p-2 flex items-center justify-center text-white font-bold">
                          Z
                        </div>
                        <div>
                          <h3 className="font-medium">Zapier</h3>
                          <p className="text-sm text-gray-400">
                            Connect with 3,000+ apps via Zapier
                          </p>
                        </div>
                      </div>
                      <div>
                        <span className="rounded-lg bg-blue-600 px-3 py-1 text-sm text-white">
                          Connected
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="mr-3 h-10 w-10 rounded-full bg-[#7b68ee] p-2 flex items-center justify-center text-white font-bold">
                          S
                        </div>
                        <div>
                          <h3 className="font-medium">Slack</h3>
                          <p className="text-sm text-gray-400">
                            Get notifications about calls in Slack
                          </p>
                        </div>
                      </div>
                      <div>
                        <button className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1 text-sm hover:bg-gray-700">
                          Connect
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-medium">Webhook</h3>
                  <div className="mb-4">
                    <label className="mb-2 block text-xs text-gray-400">
                      Webhook URL
                    </label>
                    <input type="text" className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" placeholder="https://example.com/webhook" />
                    <p className="mt-1 text-xs text-gray-400">
                      We'll send call data to this URL in real-time
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex justify-end">
                  <button type="button" className="flex items-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">
                    <SaveIcon className="mr-2 h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </div>}
            {activeTab === 'hours' && <div>
                <h2 className="mb-6 text-lg font-semibold">Business Hours</h2>
                <div className="mb-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium">
                      Set your business hours
                    </h3>
                    <label className="relative inline-flex cursor-pointer items-center">
                      <input type="checkbox" className="peer sr-only" defaultChecked />
                      <div className="peer h-6 w-11 rounded-full bg-gray-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-600 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none"></div>
                      <span className="ml-2 text-sm text-gray-300">
                        Enabled
                      </span>
                    </label>
                  </div>
                  <p className="mt-1 text-sm text-gray-400">
                    The AI will only answer calls during these hours. Outside of
                    these hours, calls will go to voicemail.
                  </p>
                  <div className="mt-4 space-y-4">
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(day => <div key={day} className="flex items-center justify-between border-b border-gray-700 pb-3">
                        <div className="flex items-center">
                          <input type="checkbox" className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-blue-600" defaultChecked />
                          <span className="ml-2 w-28">{day}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <select className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none">
                            <option>9:00 AM</option>
                            <option>9:30 AM</option>
                            <option>10:00 AM</option>
                          </select>
                          <span>to</span>
                          <select className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none">
                            <option>5:00 PM</option>
                            <option>5:30 PM</option>
                            <option>6:00 PM</option>
                          </select>
                        </div>
                      </div>)}
                    {['Saturday', 'Sunday'].map(day => <div key={day} className="flex items-center justify-between border-b border-gray-700 pb-3">
                        <div className="flex items-center">
                          <input type="checkbox" className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-blue-600" />
                          <span className="ml-2 w-28">{day}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <select disabled className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-1 text-sm text-gray-500 focus:border-blue-500 focus:outline-none">
                            <option>9:00 AM</option>
                          </select>
                          <span>to</span>
                          <select disabled className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-1 text-sm text-gray-500 focus:border-blue-500 focus:outline-none">
                            <option>5:00 PM</option>
                          </select>
                        </div>
                      </div>)}
                  </div>
                </div>
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-medium">
                    Holidays & Special Hours
                  </h3>
                  <button className="flex items-center rounded-lg border border-dashed border-gray-600 px-4 py-2 text-sm text-gray-400 hover:border-gray-500 hover:text-gray-300">
                    <span className="mr-2 text-lg">+</span>
                    Add Holiday or Special Hours
                  </button>
                </div>
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-medium">
                    After Hours Message
                  </h3>
                  <textarea className="w-full rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-white focus:border-blue-500 focus:outline-none" rows={3} defaultValue="Thank you for calling VoiceAI Solutions. Our office is currently closed. Our regular business hours are Monday through Friday, 9 AM to 5 PM. Please leave a message and we'll get back to you during business hours." />
                </div>
                <div className="mt-6 flex justify-end">
                  <button type="button" className="flex items-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">
                    <SaveIcon className="mr-2 h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </div>}
          </div>
        </div>
      </div>
    </div>;
};
export default Settings;