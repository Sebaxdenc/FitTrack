import axios from 'axios';
import { Platform } from 'react-native';

// Use 10.0.2.2 for Android Emulator, localhost for iOS/Web
// If running on physical device, replace with your computer's IP
const API_URL = 'http://192.168.1.21:5000';
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'x-api-key': 'gym-app-secret-key-123'
    }
});

export const getExercises = () => api.get('/exercises');

export const createExercise = (data) => {
    return api.post('/exercises', {
        name: data.name,
        description: data.description,
        image: data.image,
        defaultReps: data.defaultReps,
        defaultSets: data.defaultSets,
        defaultWeight: data.defaultWeight,
        restTime: data.restTime
    });
};
export const updateOnlineExercise = (id, data) => {
    return api.put(`/exercises/${id}`, {
        name: data.name,
        description: data.description,
        image: data.image,
        defaultReps: data.defaultReps,
        defaultSets: data.defaultSets,
        defaultWeight: data.defaultWeight,
        restTime: data.restTime
    });
};
export const deleteExercise = (id) => api.delete(`/exercises/${id}`);

export const getRoutine = (day) => api.get(`/routines/${day}`);
export const saveRoutine = (day, exercises) => api.post(`/routines/${day}`, { exercises });

export default api;
