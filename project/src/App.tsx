import React, { useState, useEffect } from 'react';
import { Droplets, Power, Wifi, WifiOff } from 'lucide-react';

const PICO_IP = '192.168.1.16';

interface SensorData {
  wifi_status: boolean;
  flow_rate: number;
  relay_status: boolean;
}

function App() {
  const [data, setData] = useState<SensorData>({
    wifi_status: false,
    flow_rate: 0,
    relay_status: false
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://${PICO_IP}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const newData = await response.json();
        setData(newData);
        setError(null);
      } catch (err) {
        setError('Failed to connect to the device');
      }
    };

    // Update every 2 seconds
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleRelay = async (state: boolean) => {
    try {
      await fetch(`http://${PICO_IP}/relay/${state ? 'on' : 'off'}`);
    } catch (err) {
      setError('Failed to control relay');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-800">
                Flow Sensor Dashboard
              </h1>
              <div className="flex items-center gap-2">
                {data.wifi_status ? (
                  <Wifi className="text-green-500" size={24} />
                ) : (
                  <WifiOff className="text-red-500" size={24} />
                )}
                <span className="text-sm text-gray-600">
                  {data.wifi_status ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Flow Rate Card */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">Flow Rate</h2>
                <Droplets className="text-blue-500" size={24} />
              </div>
              <div className="text-4xl font-bold text-blue-600">
                {data.flow_rate.toFixed(2)}
                <span className="text-2xl ml-2">L/min</span>
              </div>
            </div>

            {/* Relay Control Card */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">
                  Relay Control
                </h2>
                <Power
                  className={data.relay_status ? 'text-green-500' : 'text-red-500'}
                  size={24}
                />
              </div>
              <button
                onClick={() => toggleRelay(!data.relay_status)}
                className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-colors ${
                  data.relay_status
                    ? 'bg-red-500 hover:bg-red-600'
                    : 'bg-green-500 hover:bg-green-600'
                }`}
              >
                {data.relay_status ? 'Turn Off' : 'Turn On'}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              <strong className="font-bold">Error:</strong>
              <span className="block sm:inline"> {error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;