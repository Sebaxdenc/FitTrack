import { Directory, Paths, File} from 'expo-file-system'
import { createExercise, getExercises as fetchExercises } from './api';
import {getLocalExercises, saveLocalExercises} from '../utils/fileSystem'

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

async function syncStorages() {
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

        await syncStorages()

        return response.data

    } catch (e) {
        //Pedir los ejercicios desde el almacenamiento local
        console.warn('Failed to fecth, online version: ', e)
        const exercises = await getLocalExercises()

        return exercises
    }
}



