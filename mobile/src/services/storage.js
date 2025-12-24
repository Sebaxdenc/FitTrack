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
const EXER_FILE_NAME = 'exercises.json'

async function syncStorages() {
    try {
        const exercises = await getLocalExercises()

        const promisesArr = exercises.map(async(exercise) => {

            if (!exercise._id) {
                const onlineExercise = await createExercise(exercise)
                return onlineExercise
            }
            return exercise
        })


        await Promise.all(promisesArr)
            .then(async(data) => {

                const newExercises = data.map((fetchData)=>{
                    if(!fetchData.data){
                        return fetchData
                    }
                    return fetchData.data
                })
                
                await saveLocalExercises(newExercises)
            })
            .catch((error)=>{
                console.error(error)
                throw new Error(error)
            })


    } catch (e) {
        console.error('A problem has occurred syncing the storages', e)
    }
}

async function getExerFile() {

    try {
        const directory = new Directory(Paths.cache, DIR_NAME)
        let exerFile;

        if (!directory.exists) {
            directory.create()
            exerFile = directory.createFile(EXER_FILE_NAME, 'Application/jso')
            const jsonString = JSON.stringify([sampleExercise], undefined, 0)
            exerFile.write(jsonString)
            return []
        }
        exerFile = directory.createFile(EXER_FILE_NAME, 'Application/jso')

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
        if(bytes.length === 0){
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

    console.warn('Agregando de manera manual el ejercicio')

    exercises.push(exercise)
    await saveLocalExercises(exercises)

}

//Hacer que los ejercicios se puedan pedir sin conexion
export async function getExercises() {
    try{

        const response = await fetchExercises()
        
        if(response.status !== 200){
            throw new Error(`Status erro ${response.status}`)            
        }
        
        await syncStorages()   

        return response.data
        
    }catch(e){  
        //Pedir los ejercicios desde el almacenamiento local
        const exercises = await getLocalExercises()
        
        return exercises
    }
}