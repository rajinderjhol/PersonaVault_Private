import { create } from 'zustand';

export interface Device {
  id: string;
  name: string;
  type: 'mobile' | 'desktop' | 'edge' | 'iot';
  trustScore: number; // 0-1.0
  status: 'online' | 'offline';
  lastSeen: number;
  syncProgress: number; // 0-100
}

interface DeviceState {
  devices: Device[];
  addDevice: (device: Device) => void;
  updateTrust: (id: string, score: number) => void;
}

export const useDeviceStore = create<DeviceState>((set) => ({
  devices: [
    { id: '1', name: 'MacBook Pro', type: 'desktop', trustScore: 0.98, status: 'online', lastSeen: Date.now(), syncProgress: 100 },
    { id: '2', name: 'iPhone 15', type: 'mobile', trustScore: 0.95, status: 'online', lastSeen: Date.now(), syncProgress: 92 },
    { id: '3', name: 'Edge Node #01', type: 'edge', trustScore: 0.82, status: 'online', lastSeen: Date.now(), syncProgress: 45 },
    { id: '4', name: 'Smart Watch', type: 'iot', trustScore: 0.45, status: 'offline', lastSeen: Date.now() - 3600000, syncProgress: 0 },
  ],
  addDevice: (device) => set((state) => ({ devices: [...state.devices, device] })),
  updateTrust: (id, score) => set((state) => ({
    devices: state.devices.map(d => d.id === id ? { ...d, trustScore: score } : d)
  })),
}));
