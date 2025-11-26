import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from '../screens/HomeScreen';
import DayDetailScreen from '../screens/DayDetailScreen';
import ExerciseLibraryScreen from '../screens/ExerciseLibraryScreen';
import ExerciseFormScreen from '../screens/ExerciseFormScreen';
import ExecutionScreen from '../screens/ExecutionScreen';

const Stack = createStackNavigator();

const AppNavigator = () => {
    return (
        <NavigationContainer>
            <Stack.Navigator initialRouteName="Home">
                <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'Gym Routine' }} />
                <Stack.Screen name="DayDetail" component={DayDetailScreen} options={({ route }) => ({ title: route.params.day })} />
                <Stack.Screen name="ExerciseLibrary" component={ExerciseLibraryScreen} options={{ title: 'Exercise Library' }} />
                <Stack.Screen name="ExerciseForm" component={ExerciseFormScreen} options={{ title: 'Manage Exercise' }} />
                <Stack.Screen name="Execution" component={ExecutionScreen} options={{ title: 'Workout Mode', headerShown: false }} />
            </Stack.Navigator>
        </NavigationContainer>
    );
};

export default AppNavigator;
