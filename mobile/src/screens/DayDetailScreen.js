import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Button, FlatList, Modal, TouchableOpacity, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getRoutine, saveRoutine, getExercises } from '../services/storage';


const DayDetailScreen = ({ route, navigation }) => {
    const { day } = route.params;
    const [routine, setRoutine] = useState({ exercises: [] });
    const [allExercises, setAllExercises] = useState([]);
    const [modalVisible, setModalVisible] = useState(false);

    const fetchRoutine = async () => {
        try {
            const response = await getRoutine(day);
            setRoutine(response.data || { exercises: [] });
        } catch (error) {
            if (error.response && error.response.status === 404) {
                setRoutine({ exercises: [] });
            } else {
                console.error(error);
            }
        }
    };

    const fetchAllExercises = async () => {
        try {
            const response = await getExercises();
            setAllExercises(response.data);
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
                <Button title="Test" onPress={getRoutine} />
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
    item: { padding: 15, backgroundColor: 'white', marginBottom: 10, borderRadius: 5, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    name: { fontWeight: 'bold', fontSize: 16 },
    emptyText: { textAlign: 'center', marginTop: 20, fontSize: 16, color: '#666' },
    footer: { marginTop: 20 },
    modalContainer: { flex: 1, padding: 20, marginTop: 50 },
    modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    modalItem: { padding: 15, borderBottomWidth: 1, borderBottomColor: '#eee' },
    modalItemText: { fontSize: 18 },
});

export default DayDetailScreen;

