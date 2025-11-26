import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Dimensions, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect } from '@react-navigation/native';
import { useFonts, Inter_400Regular, Inter_700Bold } from '@expo-google-fonts/inter';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const { width } = Dimensions.get('window');
const CARD_WIDTH = (width - 60) / 2;

const HomeScreen = ({ navigation }) => {
    const [lastWorkoutDay, setLastWorkoutDay] = useState(null);
    const [fontsLoaded] = useFonts({
        Inter_400Regular,
        Inter_700Bold,
    });

    // Get current day name
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });

    useFocusEffect(
        useCallback(() => {
            loadLastWorkout();
        }, [])
    );

    const loadLastWorkout = async () => {
        try {
            const day = await AsyncStorage.getItem('lastWorkoutDay');
            if (day) setLastWorkoutDay(day);
        } catch (e) {
            console.error(e);
        }
    };

    const handleDayPress = async (day) => {
        try {
            await AsyncStorage.setItem('lastWorkoutDay', day);
            setLastWorkoutDay(day);
            navigation.navigate('DayDetail', { day });
        } catch (e) {
            console.error(e);
        }
    };

    if (!fontsLoaded) {
        return <View />;
    }

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Text style={styles.headerTitle}>Weekly Schedule</Text>
                <View style={styles.grid}>
                    {DAYS.map((day, index) => {
                        const isToday = day === today;
                        const isLastWorkout = day === lastWorkoutDay;

                        // Subtle color difference for last workout
                        const gradientColors = isLastWorkout
                            ? ['#5e72e4', '#825ee4'] // Lighter/Different purple/blue
                            : ['#2dce89', '#2dcecc']; // Default Teal/Greenish (Modern)

                        // Or stick to the requested "Subtle difference" on the original blue theme
                        // Let's use a premium dark theme approach as requested "Modern"
                        const cardColors = isLastWorkout
                            ? ['#4c669f', '#3b5998', '#192f6a'] // Original Blue (Active)
                            : ['#2c3e50', '#34495e', '#2c3e50']; // Dark Grey (Inactive)

                        const scaleValue = new Animated.Value(1);

                        const onPressIn = () => {
                            Animated.spring(scaleValue, {
                                toValue: 0.95,
                                useNativeDriver: true,
                            }).start();
                        };

                        const onPressOut = () => {
                            Animated.spring(scaleValue, {
                                toValue: 1,
                                useNativeDriver: true,
                            }).start();
                        };

                        return (
                            <TouchableOpacity
                                key={day}
                                activeOpacity={1}
                                onPressIn={onPressIn}
                                onPressOut={onPressOut}
                                onPress={() => handleDayPress(day)}
                                style={styles.cardContainer}
                            >
                                <Animated.View style={{ transform: [{ scale: scaleValue }] }}>
                                    <LinearGradient
                                        colors={cardColors}
                                        style={[styles.card, isLastWorkout && styles.cardActive]}
                                    >
                                        <Text style={styles.dayText}>{day}</Text>
                                        <Text style={styles.subtitle}>
                                            {isToday ? "Today" : "View Routine"}
                                        </Text>
                                        {isLastWorkout && <View style={styles.activeIndicator} />}
                                    </LinearGradient>
                                </Animated.View>
                            </TouchableOpacity>
                        )
                    })}
                </View>
            </ScrollView>

            <TouchableOpacity
                style={styles.fab}
                onPress={() => navigation.navigate('ExerciseLibrary')}
            >
                <Text style={styles.fabText}>+</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f4f5f7' },
    scrollContent: { padding: 20, paddingBottom: 100 },
    headerTitle: { fontFamily: 'Inter_700Bold', fontSize: 32, marginBottom: 25, color: '#172b4d' },
    grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
    cardContainer: { marginBottom: 20 },
    card: {
        width: CARD_WIDTH,
        height: CARD_WIDTH * 1.2, // Taller cards
        borderRadius: 20,
        padding: 20,
        justifyContent: 'space-between',
        elevation: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 5,
    },
    cardActive: {
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.3)'
    },
    dayText: { fontFamily: 'Inter_700Bold', fontSize: 22, color: 'white' },
    subtitle: { fontFamily: 'Inter_400Regular', fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 5 },
    activeIndicator: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#4fd69c', // Green dot
        alignSelf: 'flex-end'
    },
    fab: {
        position: 'absolute',
        bottom: 30,
        right: 30,
        width: 65,
        height: 65,
        borderRadius: 32.5,
        backgroundColor: '#5e72e4',
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 8,
        shadowColor: '#5e72e4',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.4,
        shadowRadius: 5,
    },
    fabText: { fontFamily: 'Inter_400Regular', fontSize: 35, color: 'white', marginTop: -4 },
});

export default HomeScreen;
