import { Directory, Paths, File} from 'expo-file-system'

const DIR_NAME = 'GymApp'
const IMAGES_DIR_NAME = 'Images'
const EXER_FILE_NAME = 'exercises.json'
const ROUTINES_FILE_NAME = 'routines.json'
const STORAGE_PATH = Paths.document

//Exercises File manipulations
export async function getExerFile() {

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
        exerFile = directory.createFile(EXER_FILE_NAME, 'Application/json');
        return exerFile
    } catch (e) {
        console.error('Error getting the exerFile: ', e)
        throw new Error(e)
    }

}

export async function getLocalExercises() {
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

export async function saveLocalExercises(newExercises) {
    try {

        const exerFile = await getExerFile()

        exerFile.write(JSON.stringify(newExercises, undefined, 0))


    } catch (error) {
        console.error('Error saving in local exercises:', error)
    }
}

//Routines File manipulations
export async function getRoutinesFile() {

    try {
        const directory = new Directory(STORAGE_PATH, DIR_NAME)
        let routinesFile;

        if (!directory.exists) {
            directory.create()
            routinesFile = directory.createFile(ROUTINES_FILE_NAME, 'Application/jso')
            const jsonString = JSON.stringify([], undefined, 0)
            routinesFile.write(jsonString)
            return []
        }
        routinesFile = directory.createFile(ROUTINES_FILE_NAME, 'Application/json');
        return routinesFile
    } catch (e) {
        console.error('Error getting the exerFile: ', e)
        throw new Error(e)
    }

}

export async function getLocalRoutines() {
    try {
        const routinesFile = await getRoutinesFile()
        const decoder = new TextDecoder('utf-8')
        const bytes = await routinesFile.bytes()

        //Archivo vacio
        if (bytes.length === 0) {
            await saveLocalRoutines([])
            return []
        }


        const routines = JSON.parse(decoder.decode(bytes), undefined, 0)

        //Si se guarda algo diferente a un arreglo
        if (!Array.isArray(routines)) {
            console.error('Se corrompio el almacenamiento')

            //Crear un arreglo vacio y lo retorna
            await saveLocalRoutines([])
            return []
        }

        return routines
    } catch (error) {
        console.error('Error reading local exercises:', error)
        return []
    }
}

export async function saveLocalRoutines(newRoutines) {
    try {

        const routinesFile = await getRoutinesFile()

        routinesFile.write(JSON.stringify(newRoutines, undefined, 0))


    } catch (error) {
        console.error('Error saving in local exercises:', error)
    }
}

//Esta funcion recibe 
export async function createImagecopy(uri) {
    try {

        if (!uri) {
            throw new Error('Uri required')
        }

        const {base} = Paths.parse(uri)

        const imageFile = new File(uri)

        const imagesDirectory = new Directory(STORAGE_PATH, IMAGES_DIR_NAME)
        if(!imagesDirectory.exists){
            imagesDirectory.create()
        }

        const imageCopy = new File(imagesDirectory, base)
        
        if(!imageCopy.exists){
            imageFile.copy(imageCopy)
            return imageCopy.uri
        }
        
        return imageCopy.uri

    } catch (e) {
        console.error('Error creating an image copy: ', e)
    }
}

export async function deletImage(uri) {
    try {

        if (!uri) {
            throw new Error('Uri required')
        }

        const imageFile = new File(uri)

        imageFile.delete()

    } catch (e) {
        console.error('Error deleting the image: ', e)
    }
}