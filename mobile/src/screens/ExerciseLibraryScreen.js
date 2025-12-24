import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Button, FlatList, Image, TouchableOpacity, Pressable } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getExercises } from '../services/storage';

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

    useFocusEffect(
        useCallback(() => {
            fetchExercises();
        }, [])
    );

    const renderItem = ({ item }) => (
        <TouchableOpacity
            style={styles.item}
            onPress={() => navigation.navigate('ExerciseForm', { exercise: item })}
        >
            {item.image && (
                <Image
                    source={{ uri: `http://192.168.1.213:5000/${item.image}` }}
                    style={styles.thumbnail}
                />
            )}
            <View style={styles.info}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.details}>{item.defaultSets} sets x {item.defaultReps} reps {item.defaultWeight ? `@ ${item.defaultWeight}` : ''}</Text>
            </View>
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            <Button title="Add New Exercise" onPress={() => navigation.navigate('ExerciseForm')} />
            <Button title="Test" onPress={getExercises}/>
            <FlatList
                data={exercises}
                keyExtractor={(item) => item._id}
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
});

export default ExerciseLibraryScreen;
