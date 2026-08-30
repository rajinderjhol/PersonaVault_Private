import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { 
  Smartphone, Camera, Monitor, Wifi, Server, 
  Activity, AlertCircle, CheckCircle, XCircle,
  Plus, RefreshCw, Trash2, Edit2, Eye
} from 'lucide-react';

interface Device {
  id: string;
  device_type: string;
  device_name: string;
  device_model?: string;
  status: 'online' | 'offline' | 'degraded' | 'maintenance' | 'pending';
  trust_level: 'full' | 'high' | 'medium' | 'low' | 'untrusted';
  capabilities: string[];
  last_seen?: string;
  metadata: Record<string, any>;
}

interface DeviceType {
  type: string;
  description: string;
}

interface DeviceCapability {
  capability: string;
  description: string;
}

export const DeviceManager: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceTypes, setDeviceTypes] = useState<DeviceType[]>([]);
  const [capabilities, setCapabilities] = useState<DeviceCapability[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [newDevice, setNewDevice] = useState({
    device_type: 'iot',
    device_name: '',
    capabilities: [] as string[],
    config: {},
    trust_level: 'medium'
  });

  useEffect(() => {
    fetchDevices();
    fetchDeviceTypes();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await apiClient.get('/mcp/devices');
      setDevices(response.data || []);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDeviceTypes = async () => {
    try {
      const response = await apiClient.get('/mcp/devices/types');
      setDeviceTypes(response.data.device_types || []);
      setCapabilities(response.data.capabilities || []);
    } catch (error) {
      console.error('Failed to fetch device types:', error);
    }
  };

  const registerDevice = async () => {
    try {
      await apiClient.post('/mcp/devices/register', newDevice);
      setShowRegisterForm(false);
      setNewDevice({ device_type: 'iot', device_name: '', capabilities: [], config: {}, trust_level: 'medium' });
      await fetchDevices();
    } catch (error) {
      console.error('Failed to register device:', error);
    }
  };

  const updateTrustLevel = async (deviceId: string, trustLevel: string) => {
    try {
      await apiClient.patch(`/mcp/devices/${deviceId}/trust?trust_level=${trustLevel}`);
      await fetchDevices();
    } catch (error) {
      console.error('Failed to update trust level:', error);
    }
  };

  const revokeDevice = async (deviceId: string) => {
    if (!confirm('Revoke this device?')) return;
    try {
      await apiClient.delete(`/mcp/devices/${deviceId}`);
      await fetchDevices();
    } catch (error) {
      console.error('Failed to revoke device:', error);
    }
  };

  const executeAction = async (deviceId: string, action: string) => {
    try {
      const response = await apiClient.post(`/mcp/devices/${deviceId}/action`, {
        action,
        params: {}
      });
      alert(`Action executed: ${response.data?.result || 'Success'}`);
    } catch (error) {
      console.error('Failed to execute action:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="status-online" size={16} />;
      case 'offline': return <XCircle className="status-offline" size={16} />;
      case 'degraded': return <AlertCircle className="status-degraded" size={16} />;
      default: return <Activity className="status-pending" size={16} />;
    }
  };

  const getTrustColor = (trust: string) => {
    switch (trust) {
      case 'full': return '#10b981';
      case 'high': return '#34d399';
      case 'medium': return '#f59e0b';
      case 'low': return '#f97316';
      default: return '#ef4444';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'camera': return <Camera size={20} />;
      case 'medical': return <Activity size={20} />;
      case 'enterprise': return <Server size={20} />;
      case 'network': return <Wifi size={20} />;
      default: return <Smartphone size={20} />;
    }
  };

  if (isLoading) {
    return <div className="device-loading">Loading devices...</div>;
  }

  return (
    <div className="device-manager">
      <div className="device-header">
        <h3>🔌 Device Management</h3>
        <div className="device-actions">
          <button className="btn-refresh" onClick={fetchDevices}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowRegisterForm(true)}>
            <Plus size={16} /> Register Device
          </button>
        </div>
      </div>

      {/* Register Device Form */}
      {showRegisterForm && (
        <div className="device-form">
          <h4>Register New Device</h4>
          <div className="form-group">
            <label>Device Type</label>
            <select
              value={newDevice.device_type}
              onChange={(e) => setNewDevice({ ...newDevice, device_type: e.target.value })}
            >
              {deviceTypes.map((type) => (
                <option key={type.type} value={type.type}>{type.type} - {type.description}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Device Name</label>
            <input
              type="text"
              value={newDevice.device_name}
              onChange={(e) => setNewDevice({ ...newDevice, device_name: e.target.value })}
              placeholder="Device name"
            />
          </div>
          <div className="form-group">
            <label>Capabilities</label>
            <div className="capabilities-grid">
              {capabilities.map((cap) => (
                <label key={cap.capability} className="capability-checkbox">
                  <input
                    type="checkbox"
                    checked={newDevice.capabilities.includes(cap.capability)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setNewDevice({ ...newDevice, capabilities: [...newDevice.capabilities, cap.capability] });
                      } else {
                        setNewDevice({ ...newDevice, capabilities: newDevice.capabilities.filter(c => c !== cap.capability) });
                      }
                    }}
                  />
                  {cap.capability} - {cap.description}
                </label>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label>Trust Level</label>
            <select
              value={newDevice.trust_level}
              onChange={(e) => setNewDevice({ ...newDevice, trust_level: e.target.value })}
            >
              <option value="full">Full Trust</option>
              <option value="high">High Trust</option>
              <option value="medium">Medium Trust</option>
              <option value="low">Low Trust</option>
              <option value="untrusted">Untrusted</option>
            </select>
          </div>
          <div className="form-actions">
            <button className="btn-secondary" onClick={() => setShowRegisterForm(false)}>Cancel</button>
            <button className="btn-primary" onClick={registerDevice}>Register</button>
          </div>
        </div>
      )}

      {/* Device List */}
      <div className="devices-grid">
        {devices.length === 0 ? (
          <div className="devices-empty">No devices registered</div>
        ) : (
          devices.map((device) => (
            <div key={device.id} className={`device-card trust-${device.trust_level}`}>
              <div className="device-card-header">
                <div className="device-icon">{getDeviceIcon(device.device_type)}</div>
                <div className="device-info">
                  <h4>{device.device_name}</h4>
                  <span className="device-type">{device.device_type}</span>
                </div>
                <div className="device-status">
                  {getStatusIcon(device.status)}
                  <span className={`status-text ${device.status}`}>{device.status}</span>
                </div>
              </div>

              <div className="device-details">
                <div className="detail-row">
                  <span className="detail-label">Trust Level</span>
                  <span className="detail-value" style={{ color: getTrustColor(device.trust_level) }}>
                    {device.trust_level}
                  </span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Capabilities</span>
                  <span className="detail-value">{device.capabilities?.join(', ') || 'None'}</span>
                </div>
                {device.last_seen && (
                  <div className="detail-row">
                    <span className="detail-label">Last Seen</span>
                    <span className="detail-value">{new Date(device.last_seen).toLocaleString()}</span>
                  </div>
                )}
              </div>

              <div className="device-actions">
                <select
                  value={device.trust_level}
                  onChange={(e) => updateTrustLevel(device.id, e.target.value)}
                  className="trust-select"
                >
                  <option value="full">Full</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="untrusted">Untrusted</option>
                </select>
                <button 
                  className="btn-action" 
                  onClick={() => executeAction(device.id, 'ping')}
                  title="Ping device"
                >
                  <Activity size={14} />
                </button>
                <button 
                  className="btn-action" 
                  onClick={() => setSelectedDevice(device)}
                  title="View details"
                >
                  <Eye size={14} />
                </button>
                <button 
                  className="btn-action danger" 
                  onClick={() => revokeDevice(device.id)}
                  title="Revoke device"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Device Detail Modal */}
      {selectedDevice && (
        <div className="device-modal" onClick={() => setSelectedDevice(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedDevice.device_name}</h3>
              <button className="modal-close" onClick={() => setSelectedDevice(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="detail-row"><strong>ID:</strong> {selectedDevice.id}</div>
              <div className="detail-row"><strong>Type:</strong> {selectedDevice.device_type}</div>
              <div className="detail-row"><strong>Model:</strong> {selectedDevice.device_model || 'Unknown'}</div>
              <div className="detail-row"><strong>Status:</strong> {selectedDevice.status}</div>
              <div className="detail-row"><strong>Trust Level:</strong> {selectedDevice.trust_level}</div>
              <div className="detail-row"><strong>Capabilities:</strong> {selectedDevice.capabilities?.join(', ') || 'None'}</div>
              <div className="detail-row"><strong>Last Seen:</strong> {selectedDevice.last_seen ? new Date(selectedDevice.last_seen).toLocaleString() : 'Never'}</div>
              <div className="detail-row"><strong>Metadata:</strong> <pre>{JSON.stringify(selectedDevice.metadata, null, 2)}</pre></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
