const express = require('express');
const router = express.Router();
const Exercise = require('../models/Exercise');

// Get all exercises
router.get('/', async (req, res) => {
    try {
        const exercises = await Exercise.find();
        res.json(exercises);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

// Create a new exercise
router.post('/', async (req, res) => {
    const exercise = new Exercise({
        name: req.body.name,
        description: req.body.description,
        image: req.body.image,
        defaultReps: req.body.defaultReps,
        defaultSets: req.body.defaultSets,
        defaultWeight: req.body.defaultWeight,
        restTime: req.body.restTime
    });

    try {
        const newExercise = await exercise.save();
        res.status(201).json(newExercise);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Update an exercise
router.put('/:id', async (req, res) => {
    try {
        const exercise = await Exercise.findById(req.params.id);
        if (!exercise) return res.status(404).json({ message: 'Exercise not found' });

        if (req.body.name) exercise.name = req.body.name;
        if (req.body.description) exercise.description = req.body.description;
        if (req.body.image) exercise.image = req.body.image;
        if (req.body.defaultReps) exercise.defaultReps = req.body.defaultReps;
        if (req.body.defaultSets) exercise.defaultSets = req.body.defaultSets;
        if (req.body.defaultWeight) exercise.defaultWeight = req.body.defaultWeight;
        if (req.body.restTime) exercise.restTime = req.body.restTime;

        const updatedExercise = await exercise.save();
        res.json(updatedExercise);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Delete an exercise
router.delete('/:id', async (req, res) => {
    try {
        const exercise = await Exercise.findById(req.params.id);
        if (!exercise) return res.status(404).json({ message: 'Exercise not found' });

        await exercise.deleteOne();
        res.json({ message: 'Exercise deleted' });
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

module.exports = router;
