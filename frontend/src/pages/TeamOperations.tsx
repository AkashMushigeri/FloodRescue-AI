import React, { useState, useEffect } from 'react';
import {
  Users,
  MapPin,
  Radio,
  Truck,
  RotateCcw,
} from 'lucide-react';
import { api } from '../services/api';
import type { RescueTeam, TeamStatus } from '../types';

export const TeamOperations: React.FC = () => {
  const [teams, setTeams] = useState<RescueTeam[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      const data = await api.listTeams();
      setTeams(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleUpdateStatus = async (teamId: string, newStatus: TeamStatus) => {
    setUpdatingId(teamId);
    try {
      await api.updateTeamStatus(teamId, newStatus, 'FIELD-COMMANDER');
      await fetchTeams();
    } catch (e: any) {
      alert('Error updating team status: ' + e.message);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-disaster-cardBorder pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-white tracking-wide">
              Field Rescue Teams & Equipment Roster
            </h1>
            <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-2.5 py-0.5 rounded font-mono font-bold">
              [SIMULATED UNITS]
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Operational status of swift-water boat crews, paramedic squads, and high-clearance evacuation vehicles.
          </p>
        </div>

        <button
          onClick={fetchTeams}
          className="bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-600 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5"
        >
          <RotateCcw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Roster</span>
        </button>
      </div>

      {/* Grid of Teams */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {teams.map((team) => (
          <div
            key={team.team_id}
            className="bg-disaster-card border border-disaster-cardBorder rounded-xl p-6 shadow-xl flex flex-col justify-between"
          >
            <div>
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4 border-b border-gray-700/60 pb-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 bg-blue-600/20 text-blue-400 rounded-lg">
                    <Truck className="h-6 w-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white">{team.team_name}</h2>
                    <span className="text-xs font-mono text-gray-400">{team.team_id}</span>
                  </div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded text-xs font-black uppercase tracking-wider ${
                    team.status === 'available'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : team.status === 'dispatched'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : team.status === 'on_scene'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  {team.status.replace('_', ' ')}
                </span>
              </div>

              {/* Attributes */}
              <div className="space-y-2.5 text-xs text-gray-300 mb-5">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 flex items-center space-x-1.5">
                    <Users className="h-3.5 w-3.5" />
                    <span>Personnel Count:</span>
                  </span>
                  <span className="font-bold text-white">{team.personnel_count} Responders</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-400 flex items-center space-x-1.5">
                    <Radio className="h-3.5 w-3.5" />
                    <span>Comms Channel:</span>
                  </span>
                  <span className="font-mono text-blue-300">{team.contact_channel}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-400 flex items-center space-x-1.5">
                    <MapPin className="h-3.5 w-3.5" />
                    <span>Staging Base:</span>
                  </span>
                  <span className="text-gray-200">{team.current_location_name}</span>
                </div>

                <div>
                  <span className="text-gray-400 block mb-1">Equipment & Capabilities:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {team.capabilities.map((cap, i) => (
                      <span
                        key={i}
                        className="bg-gray-800 text-gray-300 text-[10px] px-2 py-0.5 rounded border border-gray-700 capitalize"
                      >
                        {cap.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Assigned Incidents */}
                <div className="pt-2 border-t border-gray-800">
                  <span className="text-gray-400 block mb-1">Assigned Distress Incidents:</span>
                  {team.assigned_incidents.length === 0 ? (
                    <span className="text-[11px] text-gray-500 italic">No current active assignments (Standing by)</span>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {team.assigned_incidents.map((id) => (
                        <span
                          key={id}
                          className="bg-red-500/20 text-red-300 border border-red-500/40 text-[11px] font-mono px-2 py-0.5 rounded font-bold"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Status Change Controls */}
            <div className="border-t border-gray-700/60 pt-3">
              <span className="text-[11px] font-bold text-gray-400 block mb-2">Update Operational Status:</span>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => handleUpdateStatus(team.team_id, 'available' as TeamStatus)}
                  disabled={updatingId === team.team_id || team.status === 'available'}
                  className="bg-emerald-950/60 hover:bg-emerald-800 border border-emerald-600/50 text-emerald-300 py-1.5 rounded text-xs font-semibold disabled:opacity-30"
                >
                  Available
                </button>
                <button
                  onClick={() => handleUpdateStatus(team.team_id, 'on_scene' as TeamStatus)}
                  disabled={updatingId === team.team_id || team.status === 'on_scene'}
                  className="bg-purple-950/60 hover:bg-purple-800 border border-purple-600/50 text-purple-300 py-1.5 rounded text-xs font-semibold disabled:opacity-30"
                >
                  On Scene
                </button>
                <button
                  onClick={() => handleUpdateStatus(team.team_id, 'returning' as TeamStatus)}
                  disabled={updatingId === team.team_id || team.status === 'returning'}
                  className="bg-gray-800 hover:bg-gray-700 border border-gray-600 text-gray-300 py-1.5 rounded text-xs font-semibold disabled:opacity-30"
                >
                  Returning
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
