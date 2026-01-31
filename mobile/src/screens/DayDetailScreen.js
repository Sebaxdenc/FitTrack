import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Button, FlatList, Modal, TouchableOpacity, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getRoutine, saveRoutine, getExercises} from '../services/storage';
import { Image } from 'expo-image';


const placeHolderImage = require('../../assets/placeHolder.png')

const DayDetailScreen = ({ route, navigation }) => {
    const { day } = route.params;
    const [routine, setRoutine] = useState({ exercises: [] });
    const [allExercises, setAllExercises] = useState([]);
    const [modalVisible, setModalVisible] = useState(false);

    const fetchRoutine = async () => {
        const response = await getRoutine(day);
        //TODO: Testear la funcion de getRoutine sin y con acceso al backend
        setRoutine(response.data || response);
    };

    const fetchAllExercises = async () => {
        try {
            const exercises = await getExercises();
            setAllExercises(exercises);
        } catch (error) {
            console.error(error);
        }
    };

    useFocusEffect(
        useCallback(() => {
            fetchRoutine();
            fetchAllExercises();
        }, [day])
    );

    const addExerciseToRoutine = async (exercise) => {
        const newExercise = {
            exercise: exercise._id,
            targetReps: exercise.defaultReps,
            targetSets: exercise.defaultSets,
            order: routine.exercises.length
        };

        const updatedExercises = [...routine.exercises, newExercise];

        try {
            await saveRoutine(day, updatedExercises);
            setModalVisible(false);
            fetchRoutine(); // Refresh to get populated data
        } catch (error) {
            console.error(error);
            Alert.alert('Error', 'Failed to add exercise');
        }
    };

    const removeExercise = async (index) => {
        const updatedExercises = [...routine.exercises];
        updatedExercises.splice(index, 1);

        try {
            await saveRoutine(day, updatedExercises);
            fetchRoutine();
        } catch (error) {
            console.error(error);
            Alert.alert('Error', 'Failed to remove exercise');
        }
    };

    const renderExerciseItem = ({ item, index }) => (
        <View style={styles.item}>
            <Text style={styles.name}>{item.exercise?.name || 'Unknown Exercise'}</Text>
            <Image
                source={item.exercise?.image || placeHolderImage}
                style={styles.image}
                onError={(error) => console.warn(error)}
            />

            <Text>{item.targetSets} sets x {item.targetReps} reps</Text>
            <Button title="Remove" onPress={() => removeExercise(index)} color="red" />
        </View>
    );

    return (
        <View style={styles.container}>
            <FlatList
                data={routine.exercises}
                keyExtractor={(item, index) => index.toString()}
                renderItem={renderExerciseItem}
                ListEmptyComponent={<Text style={styles.emptyText}>No exercises for this day</Text>}
            />

            <View style={styles.footer}>
                <Button title="Add Exercise" onPress={() => setModalVisible(true)} />
                <View style={{ height: 10 }} />
                <Button
                    title="Start Workout"
                    onPress={() => navigation.navigate('Execution', { day, routine })}
                    disabled={routine.exercises.length === 0}
                />
            </View>

            <Modal visible={modalVisible} animationType="slide">
                <View style={styles.modalContainer}>
                    <Text style={styles.modalTitle}>Select Exercise</Text>
                    <FlatList
                        data={allExercises}
                        keyExtractor={(item) => item._id}
                        renderItem={({ item }) => (
                            <TouchableOpacity style={styles.modalItem} onPress={() => addExerciseToRoutine(item)}>
                                <Text style={styles.modalItemText}>{item.name}</Text>
                                <Image
                                    source={item.image || placeHolderImage}
                                    style={{ marginStart: 30, width: 60, height: 60, borderRadius: 15 }}
                                    onError={(error) => console.warn(error)}
                                />
                            </TouchableOpacity>
                        )}
                    />
                    <Button title="Cancel" onPress={() => setModalVisible(false)} color="red" />
                </View>
            </Modal>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20 },
    image: { width: 120, height: 60, borderRadius: 15, backgroundColor: '#fffad0ff' },
    item: {
        padding: 15,
        backgroundColor: 'white', 
        marginBottom: 10, 
        borderRadius: 5, 
        flexDirection: 'row', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexWrap:'wrap',
        rowGap: 20
    },
    name: { fontWeight: 'bold', fontSize: 16 },
    emptyText: { textAlign: 'center', marginTop: 20, fontSize: 16, color: '#666' },
    footer: { marginTop: 20 },
    modalContainer: { flex: 1, padding: 20, marginTop: 50 },
    modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    modalItem: { padding: 15, borderBottomWidth: 1, borderBottomColor: '#eee', flexDirection: 'row', justifyContent:'space-between' },
    modalItemText: { fontSize: 18 },
});

export default DayDetailScreen;

