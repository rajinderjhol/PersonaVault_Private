import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { Calendar, Clock, Users, Plus, RefreshCw, Trash2, Edit2 } from 'lucide-react';

interface CalendarEvent {
  id: string;
  summary: string;
  description: string;
  start: { dateTime: string };
  end: { dateTime: string };
  attendees?: { email: string }[];
}

interface AvailableSlot {
  start: string;
  end: string;
}

export const CalendarManager: React.FC = () => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [availableSlots, setAvailableSlots] = useState<AvailableSlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEvent, setNewEvent] = useState({
    summary: '',
    description: '',
    start_time: '',
    end_time: '',
    attendees: ''
  });

  useEffect(() => {
    fetchEvents();
    fetchAvailableSlots();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await apiClient.get('/mcp/calendar/events');
      setEvents(response.data || []);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableSlots = async () => {
    try {
      const response = await apiClient.get('/mcp/calendar/available-slots?duration_minutes=60&days_ahead=7');
      setAvailableSlots(response.data || []);
    } catch (error) {
      console.error('Failed to fetch available slots:', error);
    }
  };

  const createEvent = async () => {
    try {
      const attendees = newEvent.attendees.split(',').map(email => email.trim()).filter(Boolean);
      await apiClient.post('/mcp/calendar/events', {
        summary: newEvent.summary,
        description: newEvent.description,
        start_time: newEvent.start_time,
        end_time: newEvent.end_time,
        attendees: attendees
      });
      setShowCreateForm(false);
      setNewEvent({ summary: '', description: '', start_time: '', end_time: '', attendees: '' });
      await fetchEvents();
    } catch (error) {
      console.error('Failed to create event:', error);
    }
  };

  const deleteEvent = async (eventId: string) => {
    if (!confirm('Delete this event?')) return;
    try {
      await apiClient.delete(`/mcp/calendar/events/${eventId}`);
      await fetchEvents();
    } catch (error) {
      console.error('Failed to delete event:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  if (isLoading) {
    return <div className="calendar-loading">Loading calendar...</div>;
  }

  return (
    <div className="calendar-manager">
      <div className="calendar-header">
        <h3>📅 Calendar Integration</h3>
        <div className="calendar-actions">
          <button className="btn-refresh" onClick={() => { fetchEvents(); fetchAvailableSlots(); }}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowCreateForm(true)}>
            <Plus size={16} /> New Event
          </button>
        </div>
      </div>

      {/* Create Event Form */}
      {showCreateForm && (
        <div className="calendar-form">
          <h4>Create New Event</h4>
          <div className="form-group">
            <label>Summary</label>
            <input
              type="text"
              value={newEvent.summary}
              onChange={(e) => setNewEvent({ ...newEvent, summary: e.target.value })}
              placeholder="Event summary"
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={newEvent.description}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              placeholder="Event description"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Start Time</label>
              <input
                type="datetime-local"
                value={newEvent.start_time}
                onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>End Time</label>
              <input
                type="datetime-local"
                value={newEvent.end_time}
                onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
              />
            </div>
          </div>
          <div className="form-group">
            <label>Attendees (comma separated emails)</label>
            <input
              type="text"
              value={newEvent.attendees}
              onChange={(e) => setNewEvent({ ...newEvent, attendees: e.target.value })}
              placeholder="team@example.com, manager@example.com"
            />
          </div>
          <div className="form-actions">
            <button className="btn-secondary" onClick={() => setShowCreateForm(false)}>Cancel</button>
            <button className="btn-primary" onClick={createEvent}>Create Event</button>
          </div>
        </div>
      )}

      {/* Events List */}
      <div className="events-list">
        {events.length === 0 ? (
          <div className="events-empty">No upcoming events</div>
        ) : (
          events.map((event) => (
            <div key={event.id} className="event-card">
              <div className="event-header">
                <h4>{event.summary}</h4>
                <div className="event-actions">
                  <button className="btn-icon" onClick={() => deleteEvent(event.id)}>
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p className="event-description">{event.description}</p>
              <div className="event-meta">
                <span className="meta-item"><Clock size={14} /> {formatDate(event.start?.dateTime)} - {formatDate(event.end?.dateTime)}</span>
                {event.attendees && event.attendees.length > 0 && (
                  <span className="meta-item"><Users size={14} /> {event.attendees.length} attendees</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Available Slots */}
      <div className="available-slots">
        <h4>Available Time Slots</h4>
        <div className="slots-grid">
          {availableSlots.slice(0, 6).map((slot, index) => (
            <div key={index} className="slot-card">
              <span className="slot-time">{formatDate(slot.start)}</span>
              <button className="btn-slot" onClick={() => {
                setNewEvent({
                  ...newEvent,
                  start_time: slot.start,
                  end_time: slot.end,
                  summary: 'Scheduled Decision Review'
                });
                setShowCreateForm(true);
              }}>
                Book
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
