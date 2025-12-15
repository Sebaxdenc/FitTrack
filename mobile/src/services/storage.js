import { Directory, Paths } from 'expo-file-system'
//En todos las modificaciones tengo que leer el archivo para obtener el objeto
//Las modificaciones del objeto tienen que ser hechas atravez de las funciones
//Las consultas de los objetos de igual manera tiene que ser hechas atravez de las funciones


const getExercisesFile = () => {
    const directory = new Directory(Paths.document, 'GymApp');

    if (!directory.exists) {
        directory.create();
    }

    return directory.createFile('exercises.json', 'application/json');
}

const saveExercises = (objectContent) => {
    const exerFile = getExercisesFile();    
    
    //Overwrites the entire file
    exerFile.write(JSON.stringify(objectContent))
}

const getExercisesObject = (exercise) => {
    const exerFile = getExercisesFile();    
    const decoder = new TextDecoder('utf-8')
    const jsonString = decoder.decode(exerFile.bytesSync())        
    return JSON.parse(jsonString)

}


const addExercise = (exercise) => { 

    const exercises = getExercisesObject()
    exercises.push(exercise)

    saveExercises(exercises)

}

const deleteExercise = (id) => {
    const exercises = getExercisesObject()
    const newExercises = exercises.map((exercise)=>{
        if(exercise.id !== id){
            return exercise
        }
    })  

    saveExercises(newExercises)
}

const updateExercise = (id, newExercise) => {
    const exercises = getExercisesObject()
    const newExercises = exercises.map((exercise)=>{
        if(exercise.id === id){
            return newExercise
        }
        return exercise
    })  

    saveExercises(newExercises)
}








