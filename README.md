## Arquitectura

El backend esta en node con express, todavia no hay que cambiarlo. El front esta con un marco de trabajo de expo, que usa el marco de trabajo de react native, que usa el marco de trabajo de react. No usamos para nada docker. La aplicacion funciona con internet(conectada al backend) y sin internet(no conectada al backend) para esto en la carpeta de mobile/src/services hay funciones para que la aplicacion tenga un almacenamiento local y cuando se conecte a la nube se sincronicen los almacenamientos.

Cualquier duda me preguntan, todavia no comenzamos a tocar codigo pero al menos para que se vayan familiarizando con el arbol de archivos
