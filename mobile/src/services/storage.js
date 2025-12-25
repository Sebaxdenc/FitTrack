import { Directory, Paths } from 'expo-file-system'
import { createExercise, getExercises as fetchExercises } from './api';

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
const STORAGE_PATH = Paths.cache

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

async function getExerFile() {

    try {
        const directory = new Directory(STORAGE_PATH, DIR_NAME)
        let exerFile;

        if (!directory.exists) {
            directory.create()
            exerFile = directory.createFile(EXER_FILE_NAME, 'Application/jso')
            const jsonString = JSON.stringify([sampleExercise], undefined, 0)
            exerFile.write(jsonString)
            return []
        }
        exerFile = directory.createFile(EXER_FILE_NAME, 'Application/json')

        return exerFile
    } catch (e) {
        console.error('Error getting the exerFile: ', e)
        throw new Error(e)
    }

}

async function saveLocalExercises(newExercises) {
    try {

        const exerFile = await getExerFile()

        exerFile.write(JSON.stringify(newExercises, undefined, 0))


    } catch (error) {
        console.error('Error saving in local exercises:', error)
    }
}

async function getLocalExercises() {
    try {
        const exerFile = await getExerFile()
        const decoder = new TextDecoder('utf-8')
        const bytes = await exerFile.bytes()

        //Archivo vacio
        if (bytes.length === 0) {
            await saveLocalExercises([sampleExercise])
            return [sampleExercise]
        }


        const exercises = JSON.parse(decoder.decode(bytes), undefined, 0)

        if (!Array.isArray(exercises)) {
            console.error('Se corrompio el almacenamiento')
            const recoveryExercises = []
            await saveLocalExercises(recoveryExercises)
            return recoveryExercises
        }


        return exercises
    } catch (error) {
        console.error('Error reading local exercises:', error)
        return []
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
    }

    console.warn('Agregando el ejercicio localmente')

    exercises.push(exercise)
    await saveLocalExercises(exercises)

}

//Hacer que los ejercicios se puedan pedir sin conexion
export async function getExercises() {
    try {

        const response = await fetchExercises()

        if (response.status !== 200) {
            throw new Error(`Status erro ${response.status}`)
        }

        await syncStorages()

        return response.data

    } catch (e) {
        //Pedir los ejercicios desde el almacenamiento local
        console.log('Failed to fecth, local version-> ', JSON.stringify(await getLocalExercises(), undefined, 2))
        const exercises = await getLocalExercises()

        return exercises
    }
}

export async function createImagecopy(uri) {
    try {

        if(!uri){
            throw new Error('Uri required')
        }

        const {dir, base} = Paths.parse(uri)

        const oldDirectory = new Directory(Paths.join('file://',dir))
        const newDirectory = new Directory(STORAGE_PATH, IMAGES_DIR_NAME)
        //TODO: Probar para ver si la creacion de archivos va hacia donde debe(Linea 177)-> const newDirectory = new Directory(Paths.join(STORAGE_PATH, IMAGES_DIR_NAME))
        console.log(newDirectory)
        
        if(!oldDirectory.exists){
            throw new Error('No existe el directorio en el cache, donde estas las imagenes seleccionadas')
        }

        if (!newDirectory.exists) {
            newDirectory.create()
        }

        const imageFile = oldDirectory.createFile(base)

        const newImageFile = newDirectory.createFile(Paths.join(IMAGES_DIR_NAME, base))
        
        console.log(newImageFile)



    } catch (e) {
        console.error('Error creating an image copy: ', e)
    }
}

export async function deletImage(uri) {
    try {


        const {base} = Paths.parse(uri)

        const directory = new Directory(STORAGE_PATH, IMAGES_DIR_NAME)

        if(!directory.exists){
            directory.create()
            throw new Error('Empty Image Directory')
        }
        
        const imageFile = directory.createFile()
        
        if(!imageFile.exists){
            throw new Error('The image doesnt exists')
        }

        imageFile.delete()


    } catch (e) {
        console.error(e)
    }
}