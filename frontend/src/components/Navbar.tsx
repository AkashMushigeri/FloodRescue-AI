import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldAlert, Activity, Users, LifeBuoy, Database, Cloud, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { HealthResponse } from '../types';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [seeding, setSeeding] = useState(false);

  const fetchHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      // offline fallback
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await api.seedSimulatedData();
      window.location.reload();
    } catch (e) {
      alert('Seeding error: ' + e);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <header className="bg-disaster-card border-b border-disaster-cardBorder text-white sticky top-0 z-30 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Tagline */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="p-2 bg-red-600 rounded-lg group-hover:bg-red-700 transition">
              <ShieldAlert className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-wide text-white">FloodRescue AI</span>
                <span className="text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded-full font-medium">
                  WeMakeDevs × AWS '26
                </span>
              </div>
              <p className="text-xs text-gray-400 hidden sm:block">
                Every Distress Signal Matters. Every Rescue Counts.
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-3">
            <Link
              to="/help"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-semibold transition ${
                location.pathname === '/help' || location.pathname === '/'
                  ? 'bg-red-600 text-white shadow-md'
                  : 'text-gray-300 hover:bg-disaster-cardBorder hover:text-white'
              }`}
            >
              <LifeBuoy className="h-4 w-4" />
              <span>Request Help (SOS)</span>
            </Link>

            <Link
              to="/responder"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-semibold transition ${
                location.pathname === '/responder'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-300 hover:bg-disaster-cardBorder hover:text-white'
              }`}
            >
              <Activity className="h-4 w-4" />
              <span>Operations Center</span>
            </Link>

            <Link
              to="/teams"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-semibold transition ${
                location.pathname === '/teams'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-gray-300 hover:bg-disaster-cardBorder hover:text-white'
              }`}
            >
              <Users className="h-4 w-4" />
              <span>Rescue Teams</span>
            </Link>
          </nav>

          {/* Cloud / Local Mode Badge & Seed Button */}
          <div className="hidden lg:flex items-center space-x-3">
            {health?.app_mode === 'aws' ? (
              <span className="flex items-center space-x-1 text-xs bg-blue-500/20 text-blue-300 border border-blue-500/40 px-2.5 py-1 rounded-md">
                <Cloud className="h-3.5 w-3.5 text-blue-400" />
                <span>AWS Cloud Mode</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-xs bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2.5 py-1 rounded-md">
                <Database className="h-3.5 w-3.5 text-amber-400" />
                <span>Local Dev Mode (Simulated)</span>
              </span>
            )}

            <button
              onClick={handleSeed}
              disabled={seeding}
              className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 px-2.5 py-1 rounded-md flex items-center space-x-1 transition"
              title="Reset and seed sample flood incidents for demo"
            >
              <RefreshCw className={`h-3 w-3 ${seeding ? 'animate-spin' : ''}`} />
              <span>Seed Demo Data</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
