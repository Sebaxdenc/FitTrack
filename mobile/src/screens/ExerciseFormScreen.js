import React, { useState, useEffect, createContext } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Image, ScrollView, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { createExercise, updateExercise } from '../services/api';
import { addExercise, createImagecopy, deletImage } from '../services/storage';


const ExerciseFormScreen = ({ route, navigation }) => {
    const exerciseToEdit = route.params?.exercise;
    const [name, setName] = useState(exerciseToEdit?.name || '');
    const [description, setDescription] = useState(exerciseToEdit?.description || '');
    const [defaultReps, setDefaultReps] = useState(exerciseToEdit?.defaultReps?.toString() || '10');
    const [defaultSets, setDefaultSets] = useState(exerciseToEdit?.defaultSets?.toString() || '3');
    const [defaultWeight, setDefaultWeight] = useState(exerciseToEdit?.defaultWeight || '');
    const [restTime, setRestTime] = useState(exerciseToEdit?.restTime?.toString() || '60');
    const [image, setImage] = useState(exerciseToEdit?.image ? exerciseToEdit.image : null);

    const pickImage = async () => {
        let result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
            allowsEditing: true,
            aspect: [4, 3],
            quality: 1,
        });


        if (!result.canceled) {
            setImage(result.assets[0].uri);
        }
    };

    const handleSave = async () => {
        if (!name) {
            Alert.alert('Error', 'Name is required');
            return;
        }

        //Crea una copia de la imagen en el almacenamiento de la aplicacion
        //Y guarda la ruta al almacenamiento local
        const localURI = await createImagecopy(image)

        const data = {
            name,
            description,
            defaultReps: parseInt(defaultReps),
            defaultSets: parseInt(defaultSets),
            defaultWeight,
            restTime: parseInt(restTime),
            image: localURI,
        };


        try {
            if (exerciseToEdit) {
                //TODO: Esta funcion deberia poder hacer actualizaciones sin internet y cuando se posible subirlas
                await updateExercise(exerciseToEdit._id, data);
            } else {
                await addExercise(data);
            }
            navigation.goBack();
        } catch (error) {
            console.error(error);
            Alert.alert('Error', 'Failed to save exercise');
        }
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.label}>Name</Text>
            <TextInput style={styles.input} value={name} onChangeText={setName} />

            <Text style={styles.label}>Description</Text>
            <TextInput style={styles.input} value={description} onChangeText={setDescription} multiline />

            <Text style={styles.label}>Reps</Text>
            <TextInput style={styles.input} value={defaultReps} onChangeText={setDefaultReps} keyboardType="numeric" />

            <Text style={styles.label}>Sets</Text>
            <TextInput style={styles.input} value={defaultSets} onChangeText={setDefaultSets} keyboardType="numeric" />

            <Text style={styles.label}>Weight</Text>
            <TextInput style={styles.input} value={defaultWeight} onChangeText={setDefaultWeight} />

            <Text style={styles.label}>Rest Time (seconds)</Text>
            <TextInput style={styles.input} value={restTime} onChangeText={setRestTime} keyboardType="numeric" />

            <View style={{ height: 20 }} />

            <Button title="Pick an image from camera roll" onPress={pickImage} />
            {image && <Image source={{ uri: image }} style={styles.image} />}

            <View style={styles.buttonContainer}>
                <Button title="Save Exercise" onPress={handleSave} />
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { padding: 20 },
    label: { fontSize: 16, fontWeight: 'bold', marginTop: 10 },
    input: { borderWidth: 1, borderColor: '#ccc', padding: 10, borderRadius: 5, marginTop: 5, backgroundColor: 'white' },
    image: { width: 200, height: 200, marginTop: 10, alignSelf: 'center' },
    buttonContainer: { marginTop: 20 },
});

export default ExerciseFormScreen;
