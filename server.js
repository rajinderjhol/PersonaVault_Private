const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors()); // Enable CORS for frontend-backend communication
app.use(express.json()); // Parse JSON request bodies

// Chat endpoint
app.post('/chat', (req, res) => {
    const { message } = req.body;
    if (!message) {
        return res.status(400).json({ error: 'Message is required' });
    }
    console.log('Received message:', message);

    // Simulate a chatbot response
    const response = `You said: ${message}`;
    res.json({ response });
});

// Start the server
const PORT = 5001;
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});