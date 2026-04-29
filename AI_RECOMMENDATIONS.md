# Recomendaciones de IA - Documentación

## Descripción General

Se ha agregado una nueva funcionalidad de **Recomendaciones Personalizadas basadas en IA** que utiliza ChatGPT para analizar las estadísticas del usuario y proporcionar sugerencias de entrenamiento, nutrición y recuperación.

## Características

- 🤖 **Botón de IA**: Ubicado en la sección "Recomendaciones personalizadas" de la página de estadísticas
- 📊 **Análisis en tiempo real**: Las recomendaciones se generan basándose en datos de los últimos 7 días
- 💾 **Integración con estadísticas**: Utiliza automáticamente todos los datos de entrenamiento y nutrición del usuario
- ⚡ **Respuestas rápidas**: Usa ChatGPT 3.5 Turbo para respuestas veloces y precisas

## Instalación

### 1. Instalar Dependencias

La librería `openai` ya ha sido agregada a `requirements.txt`. Para instalar:

```bash
pip install -r requirements.txt
```

### 2. Configurar Variable de Entorno

Debes tener una clave API de OpenAI. Obtén la tuya en: https://platform.openai.com/api-keys

Copia el archivo `.env.example` a `.env` (si no lo has hecho):
```bash
cp .env.example .env
```

Agrega tu clave API de OpenAI en el archivo `.env`:
```
OPENAI_API_KEY=sk-tu-clave-aqui
```

### 3. Verificar Permisos de API

Se necesita tener acceso a la API de `gpt-3.5-turbo`. Verifica que tu cuenta de OpenAI:
- Tiene créditos disponibles o una suscripción activa
- Tiene habilitado el acceso a la API
- Ha aceptado los términos de uso

## Estructura de la Implementación

### Backend

#### Vista API (`workouts/views.py`)
- **Clase**: `AIRecommendationsView`
- **Método**: `POST /api/ai/recommendations/`
- **Autenticación**: Requiere usuario autenticado
- **Entrada**: JSON con estadísticas del usuario
- **Salida**: JSON con recomendaciones

#### Servicio (`workouts/services.py`)
- **Función**: `get_ai_recommendations(stats_data)`
- **Responsabilidad**: Comunicarse con OpenAI API
- **Parámetros**: Diccionario con datos de estadísticas
- **Retorna**: String con recomendaciones en español

### Frontend

#### Template (`templates/dashboard/stats.html`)
- **Elemento HTML**: Sección de recomendaciones personalizadas
- **Botón**: "Obtener recomendaciones" con icono 🤖
- **Display**: Contenedor para mostrar recomendaciones, loading y errores
- **JavaScript**: Manejo de eventos y llamadas AJAX

## URLs

### Endpoint API
- **URL**: `/api/ai/recommendations/`
- **Método**: POST
- **Autenticación**: Requerida (Token o Session)
- **CORS**: Solo acepta desde el mismo dominio

## Datos Enviados al Endpoint

```json
{
  "workouts_last_7": 5,
  "workouts_last_30": 20,
  "total_workouts": 150,
  "avg_duration_minutes": 45.5,
  "total_duration_hours": 112.5,
  "avg_calories_burned_7d": 450,
  "avg_calories_consumed_7d": 2000,
  "current_streak": 7,
  "goal_completion_rate": 85.5,
  "total_routines": 3,
  "total_goals": 50,
  "scheduled_days": 5
}
```

## Datos Retornados por el Endpoint

### Respuesta Exitosa (200 OK)
```json
{
  "success": true,
  "recommendations": "• Aumenta tu frecuencia de entrenamiento a 6 días por semana...\n• Considera una dieta con más proteína..."
}
```

### Respuesta de Error (400/500)
```json
{
  "success": false,
  "error": "OPENAI_API_KEY no está configurada en las variables de entorno"
}
```

## Manejo de Errores

El sistema implementa varios niveles de manejo de errores:

1. **Variable de Entorno Faltante**: Retorna error 400 si `OPENAI_API_KEY` no está configurada
2. **Error de API**: Retorna error 500 si hay problemas con OpenAI
3. **Error de Red**: Mensaje amigable en el frontend si hay problemas de conectividad
4. **Validación**: El endpoint verifica que el usuario esté autenticado

## Limitaciones y Consideraciones

- ⏱️ **Tiempo de respuesta**: Las recomendaciones pueden tardar 2-5 segundos
- 💰 **Costo**: Cada recomendación consume créditos de la API de OpenAI (~0.01-0.05 USD)
- 🔒 **Privacidad**: Las estadísticas se envían a OpenAI para procesamiento
- 📊 **Idioma**: Las recomendaciones se generan siempre en español
- 🔄 **Frecuencia**: Se recomienda no hacer más de 1-2 llamadas por usuario por día

## Customización

### Cambiar el Modelo de IA
En `workouts/services.py`, modifica la línea del modelo:
```python
model="gpt-4",  # O cualquier otro modelo disponible
```

### Ajustar el Prompt
El prompt se define en `get_ai_recommendations()`. Puedes modificar el contenido y tono de las recomendaciones editando la variable `prompt`.

### Cambiar la Temperatura
La temperatura controla la creatividad de las respuestas:
```python
temperature=0.7,  # Entre 0 (determinístico) y 1 (creativo)
```

## Testing

Para probar la funcionalidad en desarrollo:

1. Asegúrate de tener una clave API de OpenAI válida
2. Navega a la página de estadísticas (`/dashboard/stats/`)
3. Haz clic en el botón "Obtener recomendaciones"
4. Verifica que las recomendaciones aparecen correctamente

## Troubleshooting

### Error: "OPENAI_API_KEY no está configurada"
- Verifica que existe el archivo `.env` en la raíz del proyecto
- Asegúrate de haber agregado `OPENAI_API_KEY=sk-...` en el archivo
- Reinicia el servidor Django

### Error: "Error al obtener recomendaciones de IA"
- Verifica la clave API en https://platform.openai.com/account/api-keys
- Comprueba que tu cuenta de OpenAI tiene créditos disponibles
- Revisa los logs del servidor para más detalles

### Recomendaciones lentas o tiempos de espera
- OpenAI puede ser lento en momentos de alta carga
- Intenta de nuevo unos segundos después
- Considera usar un modelo más rápido como `gpt-3.5-turbo`

## Seguridad

- Las recomendaciones solo son accesibles para usuarios autenticados
- Se valida el token CSRF en todas las peticiones
- La clave API de OpenAI se almacena solo en variables de entorno (no en código)
- Los datos de estadísticas no se guardan en OpenAI, solo se usan para la solicitud

## Próximas Mejoras Sugeridas

- [ ] Guardar historial de recomendaciones
- [ ] Permitir regenerar recomendaciones (agregar opciones de tema)
- [ ] Implementar feedback del usuario
- [ ] Cache de recomendaciones por usuario
- [ ] Soporte para múltiples idiomas
- [ ] Análisis de tendencias a largo plazo
