import axios from 'axios';
import { Platform } from 'react-native';

// Use 10.0.2.2 for Android Emulator, localhost for iOS/Web
// If running on physical device, replace wconst API_URL = 'https://your-backend-url.onrender.com'; // Placeholder for now
// const API_URL = Platform.OS === 'android' ? 'http://192.168.1.213:5000' : 'http://localhost:5000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'x-api-key': 'gym-app-secret-key-123'
    }
});

export const getExercises = () => api.get('/exercises');
export const createExercise = (data) => {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('description', data.description);
    formData.append('defaultReps', String(data.defaultReps));
    formData.append('defaultSets', String(data.defaultSets));
    if (data.defaultWeight) formData.append('defaultWeight', data.defaultWeight);
    if (data.restTime) formData.append('restTime', String(data.restTime));
    if (data.image) {
        const filename = data.image.split('/').pop();
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : `image`;
        formData.append('image', { uri: data.image, name: filename, type });
    }
    return api.post('/exercises', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const updateExercise = (id, data) => {
    // Similar to create, but PUT
    // For simplicity, let's assume same structure
    const formData = new FormData();
    if (data.name) formData.append('name', data.name);
    if (data.description) formData.append('description', data.description);
    if (data.defaultReps) formData.append('defaultReps', String(data.defaultReps));
    if (data.defaultSets) formData.append('defaultSets', String(data.defaultSets));
    if (data.defaultWeight) formData.append('defaultWeight', data.defaultWeight);
    if (data.restTime) formData.append('restTime', String(data.restTime));
    if (data.image) {
        const filename = data.image.split('/').pop();
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : `image`;
        formData.append('image', { uri: data.image, name: filename, type });
    }
    return api.put(`/exercises/${id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const deleteExercise = (id) => api.delete(`/exercises/${id}`);

export const getRoutine = (day) => api.get(`/routines/${day}`);
export const saveRoutine = (day, exercises) => api.post(`/routines/${day}`, { exercises });

export default api;
