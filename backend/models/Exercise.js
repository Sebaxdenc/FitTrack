const mongoose = require('mongoose');

const exerciseSchema = new mongoose.Schema({
    name: {
        type: String,
        required: true
    },
    description: {
        type: String
    },
    image: {
        type: String // URL or path to image
    },
    defaultReps: {
        type: Number,
        default: 10
    },
    defaultSets: {
        type: Number,
        default: 3
    },
    defaultWeight: {
        type: String,
        default: ''
    },
    restTime: {
        type: Number,
        default: 60 // Seconds
    }
}, { timestamps: true });

module.exports = mongoose.model('Exercise', exerciseSchema);
