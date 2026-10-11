import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  MapPin,
  Users,
  HeartPulse,
  Send,
  CheckCircle2,
  Clock,
  Shield,
  Phone,
  Navigation,
  MessageSquare,
  Droplets,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import type { Incident, IncidentCreatePayload, WaterLevel, LocationType, LocationPrecision, Message } from '../types';
import { MapComponent } from '../components/MapComponent';

export const SurvivorHelp: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const trackId = searchParams.get('id');

  // Form State
  const [reporterName, setReporterName] = useState('');
  const [reporterContact, setReporterContact] = useState('');
  const [peopleReported, setPeopleReported] = useState(1);
  const [distressMessage, setDistressMessage] = useState('');
  const [landmarkDescription, setLandmarkDescription] = useState('');
  const [waterLevel, setWaterLevel] = useState<WaterLevel>('ankle');
  const [hasInjuries, setHasInjuries] = useState(false);
  const [injuriesDescription, setInjuriesDescription] = useState('');
  const [specialNeeds, setSpecialNeeds] = useState<string[]>([]);
  
  // Location details
  const [locationType, setLocationType] = useState<LocationType>('landmark_only');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [precision, setPrecision] = useState<LocationPrecision>('approximate');
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [geoLocating, setGeoLocating] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);

  // Submission & Tracking State
  const [submitting, setSubmitting] = useState(false);
  const [submittedIncident, setSubmittedIncident] = useState<Incident | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // If URL has ?id=INC-..., load existing incident for live tracking
  useEffect(() => {
    if (trackId) {
      loadIncidentStatus(trackId);
    }
  }, [trackId]);

  const loadIncidentStatus = async (id: string) => {
    try {
      const inc = await api.getIncident(id);
      setSubmittedIncident(inc);
      const msgs = await api.getMessages(id);
      setMessages(msgs);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleGetGPS = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser.');
      return;
    }
    setGeoLocating(true);
    setGeoError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setLocationType('gps');
        setPrecision('exact');
        setGeoLocating(false);
      },
      (err) => {
        setGeoLocating(false);
        setGeoError(`Location access error (${err.message}). You can still enter your landmark address below.`);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const handleMapPinSelect = (lat: number, lng: number) => {
    setLatitude(lat);
    setLongitude(lng);
    setLocationType('manual_pin');
    setPrecision('approximate');
  };

  const toggleSpecialNeed = (need: string) => {
    setSpecialNeeds((prev) =>
      prev.includes(need) ? prev.filter((n) => n !== need) : [...prev, need]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (peopleReported < 1) {
      setFormError('Number of people needing assistance must be at least 1.');
      return;
    }
    if (!landmarkDescription.trim()) {
      setFormError('Please provide a landmark, building name, or address so responders know where you are.');
      return;
    }
    if (!distressMessage.trim()) {
      setFormError('Please enter a brief message describing your situation.');
      return;
    }

    setSubmitting(true);

    const idempotencyKey = `sos-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    const payload: IncidentCreatePayload = {
      reporter_name: reporterName.trim() || 'Anonymous Survivor',
      reporter_contact: reporterContact.trim() || undefined,
      people_reported: peopleReported,
      distress_message: distressMessage.trim(),
      landmark_description: landmarkDescription.trim(),
      location_type: locationType,
      latitude: latitude ?? undefined,
      longitude: longitude ?? undefined,
      location_precision: precision,
      water_level: waterLevel,
      has_injuries: hasInjuries,
      injuries_description: hasInjuries ? injuriesDescription.trim() : undefined,
      special_needs: specialNeeds,
      idempotency_key: idempotencyKey,
      is_simulated: true,
    };

    try {
      const created = await api.createIncident(payload);
      setSubmittedIncident(created);
      setSearchParams({ id: created.incident_id });
      // Fetch initial confirmation messages
      const msgs = await api.getMessages(created.incident_id);
      setMessages(msgs);
    } catch (err: any) {
      setFormError(err.message || 'Failed to submit distress report. Please check connection and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || !submittedIncident) return;
    setSendingReply(true);
    try {
      await api.postMessage(
        submittedIncident.incident_id,
        replyText.trim(),
        'survivor',
        reporterName || 'Survivor'
      );
      setReplyText('');
      const updatedMsgs = await api.getMessages(submittedIncident.incident_id);
      setMessages(updatedMsgs);
    } catch (err) {
      alert('Failed to send message: ' + err);
    } finally {
      setSendingReply(false);
    }
  };

  // If an incident has been confirmed by the backend, display the Incident Tracking Experience!
  if (submittedIncident) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-disaster-card border border-disaster-cardBorder rounded-xl p-6 sm:p-8 shadow-2xl">
          {/* Header */}
          <div className="flex items-center space-x-3 border-b border-gray-700 pb-5 mb-6">
            <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-full">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider text-emerald-400 font-bold">
                Distress Signal Registered Successfully
              </span>
              <h1 className="text-2xl font-black text-white">
                Incident Ref: <span className="text-red-400 font-mono">{submittedIncident.incident_id}</span>
              </h1>
              <p className="text-xs text-gray-400">
                Created {new Date(submittedIncident.created_at).toLocaleTimeString()} • Mode: [SIMULATED TEST]
              </p>
            </div>
          </div>

          {/* Operational Status Card */}
          <div className="bg-disaster-dark/60 border border-disaster-cardBorder rounded-lg p-5 mb-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-700/60 pb-3 mb-3">
              <div>
                <span className="text-xs text-gray-400 block">Current Status</span>
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase mt-1 ${
                  submittedIncident.status === 'reported' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                  submittedIncident.status === 'acknowledged' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40' :
                  submittedIncident.status === 'assigned' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' :
                  'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                }`}>
                  {submittedIncident.status.replace('_', ' ')}
                </span>
              </div>

              <div>
                <span className="text-xs text-gray-400 block">Triage Priority</span>
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase mt-1 ${
                  submittedIncident.suggested_priority === 'critical' ? 'bg-red-500/20 text-red-300 border border-red-500/40' :
                  submittedIncident.suggested_priority === 'high' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                  'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                }`}>
                  {submittedIncident.suggested_priority}
                </span>
              </div>

              <div>
                <span className="text-xs text-gray-400 block">People Reported</span>
                <span className="text-lg font-bold text-white mt-1 block">
                  {submittedIncident.people_reported} {submittedIncident.people_reported === 1 ? 'Person' : 'People'}
                </span>
              </div>

              <div>
                <span className="text-xs text-gray-400 block">Assigned Unit</span>
                <span className="text-sm font-semibold text-gray-200 mt-1 block">
                  {submittedIncident.assigned_team_id || 'Awaiting Dispatch Approval'}
                </span>
              </div>
            </div>

            {/* Safety Guidance Notice */}
            <div className="bg-amber-950/30 border border-amber-500/30 rounded p-3 text-xs text-amber-200">
              <strong>Emergency Safety Reminder:</strong> Stay together on the highest accessible structure. Do not walk or wade through swift moving water. Turn off power mains if safely reachable. Keep this page open to receive updates.
            </div>
          </div>

          {/* AI Analysis Summary Preview (if available) */}
          {submittedIncident.ai_analysis && (
            <div className="bg-disaster-dark/40 border border-disaster-cardBorder rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2 text-xs font-bold text-disaster-accent mb-2">
                <Shield className="h-4 w-4" />
                <span>AI Agent Triage Assessment ({submittedIncident.ai_analysis.processing_status})</span>
              </div>
              <ul className="text-xs text-gray-300 space-y-1 list-disc list-inside">
                {submittedIncident.ai_analysis.priority_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 2-Way Message Thread with Responders */}
          <div className="border border-disaster-cardBorder rounded-lg p-4 bg-disaster-dark/30 mb-6">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2 mb-3">
              <MessageSquare className="h-4 w-4 text-blue-400" />
              <span>Operations Dispatch Channel</span>
            </h3>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-2 mb-4">
              {messages.length === 0 ? (
                <p className="text-xs text-gray-500 italic">No messages yet.</p>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.message_id}
                    className={`p-2.5 rounded text-xs ${
                      m.sender_role === 'survivor'
                        ? 'bg-blue-600/20 border border-blue-500/30 text-blue-200 ml-6'
                        : 'bg-gray-800 border border-gray-700 text-gray-200 mr-6'
                    }`}
                  >
                    <div className="flex justify-between font-semibold text-gray-400 text-[10px] mb-1">
                      <span>{m.sender_name} ({m.sender_role.toUpperCase()})</span>
                      <span>{new Date(m.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p>{m.message_content}</p>
                  </div>
                ))
              )}
            </div>

            {/* Reply Input */}
            <form onSubmit={handleSendFollowUp} className="flex gap-2">
              <input
                type="text"
                placeholder="Send additional update to rescue coordinators..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={sendingReply || !replyText.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-xs font-semibold flex items-center space-x-1 disabled:opacity-50"
              >
                <Send className="h-3 w-3" />
                <span>Send</span>
              </button>
            </form>
          </div>

          <div className="flex justify-between items-center text-xs text-gray-400">
            <button
              onClick={() => loadIncidentStatus(submittedIncident.incident_id)}
              className="text-disaster-accent hover:underline flex items-center space-x-1"
            >
              <Clock className="h-3.5 w-3.5" />
              <span>Refresh Status</span>
            </button>
            <button
              onClick={() => {
                setSubmittedIncident(null);
                setSearchParams({});
              }}
              className="text-gray-400 hover:text-white underline"
            >
              Submit Another Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Primary Distress Submission Form
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Emergency Header */}
      <div className="bg-red-950/40 border border-red-500/40 rounded-xl p-6 mb-8 text-white shadow-xl relative overflow-hidden">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-red-600 rounded-lg">
            <AlertTriangle className="h-8 w-8 text-white animate-bounce" />
          </div>
          <div>
            <span className="text-xs uppercase tracking-wider text-red-400 font-bold block">
              Emergency Flood Assistance Portal
            </span>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Submit Flood Distress Signal (SOS)
            </h1>
            <p className="text-xs sm:text-sm text-gray-300 mt-1">
              If you or people near you are trapped, injured, or in immediate danger from flood waters, fill out this report. No account or login required.
            </p>
          </div>
        </div>
      </div>

      {formError && (
        <div className="mb-6 bg-red-900/60 border border-red-500 text-red-200 px-4 py-3 rounded-lg text-sm flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      {/* Distress Form */}
      <form onSubmit={handleSubmit} className="bg-disaster-card border border-disaster-cardBorder rounded-xl p-6 sm:p-8 shadow-2xl space-y-6">
        {/* 1. People Count & Contact */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-1">
              People Needing Rescue *
            </label>
            <div className="relative">
              <Users className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="number"
                min="1"
                max="500"
                required
                value={peopleReported}
                onChange={(e) => setPeopleReported(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-disaster-dark border border-disaster-cardBorder rounded-lg pl-9 pr-3 py-2 text-white font-bold text-base focus:outline-none focus:border-red-500"
              />
            </div>
            <span className="text-[11px] text-gray-400 mt-1 block">Number of adults, children, or elderly trapped with you</span>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-1">
              Your Name (or Anonymous)
            </label>
            <input
              type="text"
              placeholder="e.g. Anand R / Anonymous"
              value={reporterName}
              onChange={(e) => setReporterName(e.target.value)}
              className="w-full bg-disaster-dark border border-disaster-cardBorder rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-1">
            Contact Number (Optional SMS / WhatsApp)
          </label>
          <div className="relative">
            <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="tel"
              placeholder="+91 98400 12345 (used by dispatch to verify location)"
              value={reporterContact}
              onChange={(e) => setReporterContact(e.target.value)}
              className="w-full bg-disaster-dark border border-disaster-cardBorder rounded-lg pl-9 pr-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* 2. Water Level & Immediate Hazard */}
        <div className="border-t border-disaster-cardBorder pt-5">
          <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-2 flex items-center space-x-1.5">
            <Droplets className="h-4 w-4 text-blue-400" />
            <span>Current Water Level at Your Location *</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { id: 'none', label: 'None / Dry', desc: 'No water inside' },
              { id: 'ankle', label: 'Ankle Deep', desc: '~0.5 ft' },
              { id: 'waist', label: 'Waist Deep', desc: '~3 ft' },
              { id: 'chest', label: 'Chest Deep', desc: '~4-5 ft' },
              { id: 'submerged_roof', label: 'Submerged Roof', desc: 'Trapped on terrace' },
            ].map((lvl) => (
              <button
                key={lvl.id}
                type="button"
                onClick={() => setWaterLevel(lvl.id as WaterLevel)}
                className={`p-2.5 rounded-lg border text-left transition ${
                  waterLevel === lvl.id
                    ? 'bg-red-600/30 border-red-500 text-white font-bold shadow-md'
                    : 'bg-disaster-dark/60 border-disaster-cardBorder text-gray-300 hover:border-gray-500'
                }`}
              >
                <span className="block text-xs font-bold">{lvl.label}</span>
                <span className="block text-[10px] text-gray-400">{lvl.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 3. Injuries & Special Needs */}
        <div className="border-t border-disaster-cardBorder pt-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-xs font-bold text-gray-200 uppercase tracking-wide flex items-center space-x-1.5">
              <HeartPulse className="h-4 w-4 text-red-400" />
              <span>Are there any injuries or medical emergencies?</span>
            </label>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setHasInjuries(false)}
                className={`px-3 py-1 rounded text-xs font-bold ${!hasInjuries ? 'bg-gray-700 text-white' : 'text-gray-400'}`}
              >
                No
              </button>
              <button
                type="button"
                onClick={() => setHasInjuries(true)}
                className={`px-3 py-1 rounded text-xs font-bold ${hasInjuries ? 'bg-red-600 text-white' : 'text-gray-400'}`}
              >
                Yes
              </button>
            </div>
          </div>

          {hasInjuries && (
            <div className="mb-4">
              <textarea
                placeholder="Describe injury, medical condition, or medication needed (e.g. diabetic patient, asthma inhaler, bleeding wound)..."
                rows={2}
                value={injuriesDescription}
                onChange={(e) => setInjuriesDescription(e.target.value)}
                className="w-full bg-disaster-dark border border-red-500/60 rounded-lg p-2.5 text-white text-xs placeholder-gray-500 focus:outline-none"
              />
            </div>
          )}

          <label className="block text-xs font-bold text-gray-300 uppercase tracking-wide mb-2">
            Vulnerable Occupants / Special Needs
          </label>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'infants_children', label: 'Infants / Young Children' },
              { id: 'elderly', label: 'Elderly Persons (65+)' },
              { id: 'mobility_impaired', label: 'Wheelchair / Bedridden' },
              { id: 'oxygen_medical_device', label: 'Oxygen / Dialysis Dependent' },
              { id: 'pets', label: 'Pets / Animals' },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => toggleSpecialNeed(item.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                  specialNeeds.includes(item.id)
                    ? 'bg-amber-600/30 border-amber-500 text-amber-200 font-bold'
                    : 'bg-disaster-dark border-gray-700 text-gray-400 hover:border-gray-500'
                }`}
              >
                {specialNeeds.includes(item.id) ? '✓ ' : '+ '}{item.label}
              </button>
            ))}
          </div>
        </div>

        {/* 4. Location & Landmark Reporting */}
        <div className="border-t border-disaster-cardBorder pt-5">
          <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-1 flex items-center space-x-1.5">
            <MapPin className="h-4 w-4 text-disaster-accent" />
            <span>Location, Landmark & Floor Number *</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Flat 3B, Sunshine Apartments, 4th Main Road, near Apollo Pharmacy"
            value={landmarkDescription}
            onChange={(e) => setLandmarkDescription(e.target.value)}
            className="w-full bg-disaster-dark border border-disaster-cardBorder rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-disaster-accent mb-2"
          />

          {/* GPS / Map Pin Controls */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <button
              type="button"
              onClick={handleGetGPS}
              disabled={geoLocating}
              className="bg-gray-800 hover:bg-gray-700 border border-gray-600 text-disaster-accent px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5"
            >
              <Navigation className={`h-3.5 w-3.5 ${geoLocating ? 'animate-spin' : ''}`} />
              <span>{geoLocating ? 'Fetching GPS...' : 'Use My GPS Location'}</span>
            </button>

            <button
              type="button"
              onClick={() => setShowMapPicker(!showMapPicker)}
              className="bg-gray-800 hover:bg-gray-700 border border-gray-600 text-gray-300 px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5"
            >
              <Layers className="h-3.5 w-3.5" />
              <span>{showMapPicker ? 'Hide Map Pin' : 'Set Pin on Map'}</span>
            </button>

            {latitude && longitude && (
              <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded">
                Coordinates: {latitude.toFixed(4)}, {longitude.toFixed(4)} ({precision.toUpperCase()})
              </span>
            )}
          </div>

          {geoError && (
            <p className="text-xs text-amber-300 bg-amber-950/40 p-2 rounded border border-amber-600/30 mb-2">
              {geoError}
            </p>
          )}

          {/* Mini Interactive Map Picker */}
          {showMapPicker && (
            <div className="mt-2 mb-4">
              <p className="text-[11px] text-gray-400 mb-1">Click on the map to place your rescue pin:</p>
              <div className="h-64 rounded-lg overflow-hidden border border-disaster-cardBorder">
                <MapComponent
                  pickerMode={true}
                  selectedCoords={latitude && longitude ? { lat: latitude, lng: longitude } : null}
                  onSelectCoords={handleMapPinSelect}
                />
              </div>
            </div>
          )}
        </div>

        {/* 5. Distress Message */}
        <div className="border-t border-disaster-cardBorder pt-5">
          <label className="block text-xs font-bold text-gray-200 uppercase tracking-wide mb-1">
            Distress Message & Situation Details *
          </label>
          <textarea
            required
            rows={3}
            placeholder="Describe what is happening right now (e.g. water entering living room, power cutoff, phone battery low, need boat for evacuation)..."
            value={distressMessage}
            onChange={(e) => setDistressMessage(e.target.value)}
            className="w-full bg-disaster-dark border border-disaster-cardBorder rounded-lg p-3 text-white text-sm focus:outline-none focus:border-red-500"
          />
        </div>

        {/* SOS Submit Button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-black py-4 px-6 rounded-xl text-lg sm:text-xl tracking-wider shadow-2xl flex items-center justify-center space-x-2 transition duration-150 disabled:opacity-50"
        >
          <AlertTriangle className="h-6 w-6 animate-pulse" />
          <span>{submitting ? 'TRANSMITTING DISTRESS SIGNAL...' : 'TRANSMIT RESCUE SOS'}</span>
        </button>

        <p className="text-center text-[11px] text-gray-400">
          FloodRescue AI will log your report immediately. Emergency dispatchers prioritize by water level and life threat.
        </p>
      </form>
    </div>
  );
};
