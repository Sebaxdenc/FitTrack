# FitTrack
Aplicación para registrar tus ejercicios y comidas diarias

1. Yo como usuario que se ejercita me gustaria tener la rutina de mis ejercicios en mi celular para saber exactamente qué hacer en el gimnasio sin tener que memorizarlo o llevar papeles.
2. Yo como usuario principiante quiero poder ver recomendaciones de implementos deportivos desde la aplicación.
3. Yo como usuario principiante quiero poder ver dietas y rutinas de otros usuarios para obtener nuevas ideas cuando me sienta estancado.
4. Yo como usuario deportista, quiero filtrar tipos de ejercicios y comidas específicos para mi deporte, para enfocar mi entrenamiento en el rendimiento de mi disciplina.
5. Yo como usuario orientado a metas quiero poder tener mi propio perfil donde guarde mis logros, ejercicios y comidas para visualizar mi historial y progreso acumulado.
6. Yo como usuario interesado en la nutrición quiero tener objetivos diarios de quema de calorias para motivarme visualmente a completarlos cada día.
7. Yo como usuario interesado en la nutrición quiero ver comidas predeterminadas con su información nutricional, para registrar lo que como rápidamente sabiendo cuántas calorías tiene.
8. Yo como usuario interesado en la nutrición, quiero llevar un control de mi alimentación diaria y su gasto energético, para asegurar que estoy cumpliendo con mi balance calórico (déficit o superávit).
9. Yo como usuario fitness, quiero filtrar ejercicios y comidas por el tipo de cuerpo u objetivo físico que busco, para recibir solo información relevante para mi meta estética.
10. Yo como usuario, quiero una interfaz intuitiva e interactiva, para navegar por la aplicación sin frustraciones y tener una buena experiencia de uso.
11. Yo como usuario, quiero ver un ranking de los ejercicios y comidas mejor valorados, para elegir las opciones que han sido más efectivas para la comunidad.

## Arquitectura

El backend esta en node con express, todavia no hay que cambiarlo. El front esta con un marco de trabajo de expo, que usa el marco de trabajo de react native, que usa el marco de trabajo de react. No usamos para nada docker. La aplicacion funciona con internet(conectada al backend) y sin internet(no conectada al backend) para esto en la carpeta de mobile/src/services hay funciones para que la aplicacion tenga un almacenamiento local y cuando se conecte a la nube se sincronicen los almacenamientos.

Cualquier duda me preguntan, todavia no comenzamos a tocar codigo pero al menos para que se vayan familiarizando con el arbol de archivos