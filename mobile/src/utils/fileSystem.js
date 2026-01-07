import { Directory, Paths, File} from 'expo-file-system'

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
            console.log(imageCopy)
            return imageCopy.uri
        }
        
        return imageCopy.uri

    } catch (e) {
        console.error('Error creating an image copy: ', e)
    }
}

export async function deletImage(uri) {
    try {

        const { base } = Paths.parse(uri)

        const directory = new Directory(STORAGE_PATH, IMAGES_DIR_NAME)

        if (!directory.exists) {
            directory.create()
            throw new Error('Empty Image Directory')
        }

        const imageFile = directory.createFile()

        if (!imageFile.exists) {
            throw new Error('The image doesnt exists')
        }

        imageFile.delete()


    } catch (e) {
        console.error(e)
    }
}