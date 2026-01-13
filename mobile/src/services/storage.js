import { Directory, Paths, File } from 'expo-file-system'
import { createExercise, getExercises as fetchExercises, getRoutine as fetchRoutine, deleteExercise as deleteExerciseAPI, saveRoutine as saveRoutineAPI } from './api';
import { getLocalExercises, getLocalRoutines, saveLocalExercises, deletImage, saveLocalRoutines } from '../utils/fileSystem'


const sampleExercise = {
    name: "Contracciones de pecho",
    description: "Levantar una mancueran con el brazo, con la palma de la mano mirando para arriba",
    image: null,
    defaultReps: 10,
    defaultSets: 3,
    restTime: 60
}

const DIR_NAME = 'GymApp'
const IMAGES_DIR_NAME = 'Images'
const EXER_FILE_NAME = 'exercises.json'
const ROUTINES_FILE_NAME = 'routines.json'
const STORAGE_PATH = Paths.document

async function syncExerciseStorage() {
    try {
        const exercises = await getLocalExercises()

        exercises.forEach(async (exercise) => {
            if (!exercise._id) {
                await createExercise(exercise)
            }
        })
        const response = await fetchExercises()
        await saveLocalExercises(response.data)

    } catch (e) {
        console.error('A problem has occurred syncing the storages', e)
    }
}

export async function syncRoutineStorages(){
    const locaRoutines = await getLocalRoutines()
    Promise.all(locaRoutines.map((routine)=>{
        return saveRoutineAPI(routine.day, routine.exercises)
    }))

}

export async function addExercise(exercise) {

    const exercises = await getLocalExercises()

    try {
        const response = await createExercise(exercise)

        if (response.status !== 201) {
            throw new Error(response)
        }

        exercises.push(response.data)
        await saveLocalExercises(exercises)

        return

    } catch (e) {
        console.error('Error creating the online exercise: ', e)

        console.warn('Agregando el ejercicio localmente')

        exercises.push(exercise)
        await saveLocalExercises(exercises)
    }
}

export async function getExercises() {
    try {

        const response = await fetchExercises()

        if (response.status !== 200) {
            throw new Error(`Status error ${response.status}`)
        }

        await syncExerciseStorage()

        return response.data

    } catch (e) {
        //Pedir los ejercicios desde el almacenamiento local
        console.warn('Failed to fecth, online version: ', e)
        const exercises = await getLocalExercises()

        return exercises
    }
}

export async function getRoutine(day) {
    try {
        const response = await fetchRoutine(day)
        return fetchRoutine(day);
    } catch (e) {
        // Return local routine
        console.warn('Failed to fetch online Routine: ', e)
        const routines = await getLocalRoutines()
        return routines
    }
}

export async function test() {
    await saveRoutine('Thursday', [sampleExercise, sampleExercise])
}

export async function saveRoutine(day, exercises) {
    try {
        const response = await saveRoutineAPI(day, exercises)

        //Guarda los cambios de manera local
        const routines = await getLocalRoutines()

        const newRoutines = routines.map((routine) => {
            if (routine.day == day) {
                routine.exercises = exercises
                return routine
            }
            return routine

        })

        await saveLocalRoutines(newRoutines)


    } catch (e) {

        console.warn(`Failed to save online Routine, saving localy: `, e)

        const routines = await getLocalRoutines()

        const newRoutines = routines.map((routine) => {
            if (routine.day == day) {
                routine.exercises = exercises
                return routine
            }
            return routine

        })

        await saveLocalRoutines(newRoutines)

    }
}

export async function deleteExercise(exercise) {
    const exercises = await getLocalExercises()

    try {
        // Intenta eliminar de la API si tiene ID
        if (exercise._id) {
            await deleteExerciseAPI(exercise._id)
        }
    } catch (e) {
        console.warn('Failed to delete exercise from online storage: ', e)
    }

    try {
        // Elimina la imagen si existe
        if (exercise.image) {
            await deletImage(exercise.image)
        }
    } catch (e) {
        console.warn('Failed to delete image: ', e)
    }

    // Elimina del almacenamiento local
    const updatedExercises = exercises.filter(ex => ex.name !== exercise.name)
    await saveLocalExercises(updatedExercises)
}



