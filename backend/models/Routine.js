const mongoose = require('mongoose');

const routineSchema = new mongoose.Schema({
    day: {
        type: String, // Monday, Tuesday, etc.
        required: true,
        unique: true
    },
    exercises: [{
        exercise: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Exercise'
        },
        order: {
            type: Number,
            default: 0
        },
        targetReps: {
            type: Number
        },
        targetSets: {
            type: Number
        },
        notes: {
            type: String
        }
    }]
}, { timestamps: true });

module.exports = mongoose.model('Routine', routineSchema);
