const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const API_KEY = process.env.API_KEY || 'gym-app-secret-key-123';

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads'));

// Security Middleware
app.use((req, res, next) => {
    // Allow access to static images without key if needed, or require it everywhere
    // For simplicity, requiring it everywhere except maybe uploads if the image component doesn't send headers easily
    // But React Native Image component supports headers.
    // Let's allow uploads to be public for simplicity in image loading, protect API routes.
    if (req.path.startsWith('/uploads')) return next();

    const apiKey = req.headers['x-api-key'];
    if (apiKey && apiKey === API_KEY) {
        next();
    } else {
        res.status(403).json({ message: 'Forbidden: Invalid API Key' });
    }
});

const exercisesRouter = require('./routes/exercises');
const routinesRouter = require('./routes/routines');

app.use('/exercises', exercisesRouter);
app.use('/routines', routinesRouter);

mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/gym-app')
    .then(() => console.log('MongoDB connected'))
    .catch(err => console.log(err));

app.get('/', (req, res) => {
    res.send('Gym App Backend is running');
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
