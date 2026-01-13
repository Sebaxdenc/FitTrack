import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Button, FlatList, TouchableOpacity, Pressable, Alert } from 'react-native';
import {Image} from 'expo-image'
import { useFocusEffect } from '@react-navigation/native';
import { getExercises, deleteExercise } from '../services/storage';

const ExerciseLibraryScreen = ({ navigation }) => {
    const [exercises, setExercises] = useState([]);

    const fetchExercises = async () => {
        try {
            const exercises = await getExercises();
            setExercises(exercises);
        } catch (error) {
            console.error(error);
        }
    };

    const handleDeleteExercise = (exercise) => {
        Alert.alert(
            "Eliminar ejercicio",
            `¿Estás seguro de que deseas eliminar "${exercise.name}"?`,
            [
                { text: "Cancelar", onPress: () => {}, style: "cancel" },
                {
                    text: "Eliminar",
                    onPress: async () => {
                        try {
                            await deleteExercise(exercise);
                            fetchExercises();
                        } catch (error) {
                            console.error(error);
                            Alert.alert("Error", "No se pudo eliminar el ejercicio");
                        }
                    },
                    style: "destructive"
                }
            ]
        );
    };

    useFocusEffect(
        useCallback(() => {
            fetchExercises();
        }, [])
    );

    const renderItem = ({ item }) => {
        return (
            <TouchableOpacity
                style={styles.item}
                onPress={() => navigation.navigate('ExerciseForm', { exercise: item })}
            >
                {item.image && (
                    <Image
                        source={{ uri: item.image }}
                        style={styles.thumbnail}
                        onError={(error) => console.warn(error)}
                    />
                )}
                <View style={styles.info}>
                    <Text style={styles.name}>{item.name}</Text>
                    <Text style={styles.details}>{item.defaultSets} sets x {item.defaultReps} reps {item.defaultWeight ? `@ ${item.defaultWeight}` : ''}</Text>
                </View>
                <Pressable
                    style={styles.deleteButton}
                    onPress={() => handleDeleteExercise(item)}
                >
                    <Text style={styles.deleteButtonText}>Eliminar</Text>
                </Pressable>
            </TouchableOpacity>
        )
    }

    return (
        <View style={styles.container}>
            <Button title="Add New Exercise" onPress={() => navigation.navigate('ExerciseForm')} />
            <FlatList
                data={exercises}
                keyExtractor={(item) => item.name}
                renderItem={renderItem}
                contentContainerStyle={styles.list}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, padding: 10 },
    list: { marginTop: 10 },
    item: { flexDirection: 'row', padding: 10, backgroundColor: 'white', marginBottom: 10, borderRadius: 5, elevation: 1, alignItems: 'center' },
    thumbnail: { width: 50, height: 50, borderRadius: 25, marginRight: 10, backgroundColor: '#eee' },
    info: { flex: 1 },
    name: { fontSize: 16, fontWeight: 'bold' },
    details: { color: '#666' },
    deleteButton: { backgroundColor: '#ff4444', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 5, justifyContent: 'center', alignItems: 'center' },
    deleteButtonText: { color: 'white', fontSize: 14, fontWeight: 'bold' },
});

export default ExerciseLibraryScreen;
