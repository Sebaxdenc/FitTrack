import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Button, Image, TouchableOpacity, ScrollView, Modal } from 'react-native';

const ExecutionScreen = ({ route, navigation }) => {
  const { routine } = route.params;

  // Initialize progress state: { exerciseId: currentSet }
  const [progress, setProgress] = useState(() => {
    const initialProgress = {};
    routine.exercises.forEach(ex => {
      initialProgress[ex._id] = 0; // 0 sets completed
    });
    return initialProgress;
  });

  const [activeExercise, setActiveExercise] = useState(null); // The exercise currently being performed
  const [isResting, setIsResting] = useState(false);
  const [timer, setTimer] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (isResting) {
      intervalRef.current = setInterval(() => {
        setTimer((prev) => {
          if (prev <= 1) {
            clearInterval(intervalRef.current);
            setIsResting(false);
            // Increment set for the active exercise
            if (activeExercise) {
              setProgress(prevProgress => {
                const newProgress = { ...prevProgress };
                newProgress[activeExercise._id] = (newProgress[activeExercise._id] || 0) + 1;
                return newProgress;
              });
              setActiveExercise(null); // Close modal/overlay
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [isResting, activeExercise]);

  const handleExercisePress = (exerciseItem) => {
    // Check if already completed
    if (progress[exerciseItem._id] >= exerciseItem.targetSets) return;
    setActiveExercise(exerciseItem);
  };

  const handleFinishSet = () => {
    // Start Rest
    const restDuration = activeExercise.exercise?.restTime || 60;
    setTimer(restDuration);
    setIsResting(true);
  };

  const skipRest = () => {
    setIsResting(false);
    if (activeExercise) {
      setProgress(prevProgress => {
        const newProgress = { ...prevProgress };
        newProgress[activeExercise._id] = (newProgress[activeExercise._id] || 0) + 1;
        return newProgress;
      });
      setActiveExercise(null);
    }
  };

  const addTime = () => {
    setTimer(prev => prev + 10);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Workout Mode</Text>
      </View>

      <ScrollView contentContainerStyle={styles.listContainer}>
        {routine.exercises.map((item) => {
          const setsCompleted = progress[item._id] || 0;
          const isCompleted = setsCompleted >= item.targetSets;

          return (
            <TouchableOpacity
              key={item._id}
              style={[
                styles.card,
                isCompleted && styles.cardCompleted
              ]}
              onPress={() => handleExercisePress(item)}
              disabled={isCompleted}
            >
              <View style={styles.cardContent}>
                <Text style={[styles.exerciseName, isCompleted && styles.textCompleted]}>
                  {item.exercise?.name}
                </Text>
                <View style={styles.statsContainer}>
                  <Text style={[styles.statsText, isCompleted && styles.textCompleted]}>
                    {setsCompleted}/{item.targetSets} Sets
                  </Text>
                  {isCompleted && <Text style={styles.checkmark}>✓</Text>}
                </View>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Active Exercise / Rest Overlay */}
      <Modal visible={!!activeExercise || isResting} animationType="slide" transparent={false}>
        <View style={styles.modalContainer}>
          {isResting ? (
            <View style={styles.timerContainer}>
              <Text style={styles.timerTitle}>Resting...</Text>
              <Text style={styles.timerText}>{timer}s</Text>
              <View style={styles.timerControls}>
                <Button title="+10s" onPress={addTime} />
                <View style={{ width: 20 }} />
                <Button title="Skip Rest" onPress={skipRest} />
              </View>
            </View>
          ) : (
            activeExercise && (
              <View style={styles.activeExerciseContainer}>
                <Text style={styles.activeTitle}>{activeExercise.exercise?.name}</Text>
                {activeExercise.exercise?.image && (
                  <Image
                    source={{ uri: `http://192.168.1.213:5000/${activeExercise.exercise.image}` }}
                    style={styles.activeImage}
                  />
                )}
                <Text style={styles.activeDetails}>
                  Set {progress[activeExercise._id] + 1} of {activeExercise.targetSets}
                </Text>
                <Text style={styles.activeDetails}>
                  Target: {activeExercise.targetReps} Reps
                </Text>
                {
                  activeExercise.exercise?.defaultWeight ? (
                    <Text style={styles.activeDetails}>Weight: {activeExercise.exercise.defaultWeight}</Text>
                  ) : null
                }

                <View style={styles.buttonContainer}>
                  <Button title="Finish Set" onPress={handleFinishSet} />
                  <View style={{ height: 10 }} />
                  <Button title="Cancel" color="red" onPress={() => setActiveExercise(null)} />
                </View>
              </View >
            )
          )}
        </View >
      </Modal >
    </View >
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#121212' }, // Dark background for workout mode
  header: { padding: 20, backgroundColor: '#1f1f1f', alignItems: 'center' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  listContainer: { padding: 20 },
  card: {
    backgroundColor: '#333',
    padding: 20,
    borderRadius: 10,
    marginBottom: 15,
    borderLeftWidth: 5,
    borderLeftColor: '#4caf50'
  },
  cardCompleted: {
    backgroundColor: '#222',
    borderLeftColor: '#888',
    opacity: 0.7
  },
  cardContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  exerciseName: { fontSize: 18, color: '#fff', fontWeight: 'bold', flex: 1 },
  statsContainer: { flexDirection: 'row', alignItems: 'center' },
  statsText: { fontSize: 16, color: '#ccc', marginRight: 10 },
  textCompleted: { textDecorationLine: 'line-through', color: '#888' },
  checkmark: { fontSize: 20, color: '#4caf50', fontWeight: 'bold' },

  // Modal Styles
  modalContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20, backgroundColor: '#fff' },
  timerContainer: { alignItems: 'center' },
  timerTitle: { fontSize: 30, marginBottom: 20 },
  timerText: { fontSize: 60, fontWeight: 'bold', marginBottom: 30 },
  timerControls: { flexDirection: 'row' },

  activeExerciseContainer: { alignItems: 'center', width: '100%' },
  activeTitle: { fontSize: 28, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  activeImage: { width: 300, height: 300, marginBottom: 20, borderRadius: 10 },
  activeDetails: { fontSize: 20, marginBottom: 10 },
  buttonContainer: { marginTop: 30, width: '100%' }
});

export default ExecutionScreen;
