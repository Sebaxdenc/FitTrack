const express = require('express');
const router = express.Router();
const Routine = require('../models/Routine');

// Get routine for a specific day
router.get('/:day', async (req, res) => {
    try {
        const routine = await Routine.findOne({ day: req.params.day }).populate('exercises.exercise');
        if (!routine) {
            // Return empty routine structure if not found, or 404?
            // Let's return 404 to let frontend know it needs to be created or is empty
            return res.status(404).json({ message: 'Routine not found for this day' });
        }
        res.json(routine);
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

// Create or Update routine for a day
router.post('/:day', async (req, res) => {
    try {
        let routine = await Routine.findOne({ day: req.params.day });

        if (routine) {
            // Update existing
            routine.exercises = req.body.exercises;
        } else {
            // Create new
            routine = new Routine({
                day: req.params.day,
                exercises: req.body.exercises
            });
        }

        const savedRoutine = await routine.save();
        res.json(savedRoutine);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

module.exports = router;
