# 🏋️‍♂️ Fitness Tracker App

Una aplicación móvil pensada para personas que quieren **entrenar mejor, comer mejor y ver su progreso de forma clara y motivadora**. Desde principiantes hasta deportistas avanzados, este proyecto busca centralizar rutinas, nutrición y metas en un solo lugar.

---

## 🚀 Descripción del proyecto

**Fitness Tracker App** es una aplicación para registrar ejercicios y comidas diarias, descubrir rutinas y dietas de otros usuarios, y hacer seguimiento del progreso físico y nutricional a lo largo del tiempo. El enfoque principal es la **motivación**, la **personalización** y una **experiencia de usuario intuitiva**.

El usuario no necesita memorizar rutinas, llevar papeles ni usar múltiples apps: todo vive aquí 📱

---

## 🎯 Objetivos principales

* Facilitar el seguimiento de rutinas de ejercicio desde el celular
* Ayudar a los usuarios a mantener el control de su alimentación y calorías
* Motivar mediante metas diarias, rankings y visualización de progreso
* Ofrecer contenido relevante según el tipo de cuerpo, deporte u objetivo físico
* Fomentar la comunidad compartiendo rutinas y dietas

---

## 👥 Historias de usuario cubiertas

La aplicación está diseñada en torno a las siguientes necesidades reales:

* 📋 Guardar rutinas de ejercicio para saber exactamente qué hacer en el gimnasio
* 🏃‍♀️ Recomendaciones de implementos deportivos para usuarios principiantes
* 🍽️ Acceso a dietas y rutinas creadas por otros usuarios
* 🎯 Filtros por deporte, tipo de cuerpo y objetivo físico
* 👤 Perfil personal con historial, logros y progreso acumulado
* 🔥 Objetivos diarios de quema de calorías con feedback visual
* 🥗 Registro rápido de comidas con información nutricional
* ⚖️ Control del balance calórico (déficit o superávit)
* ⭐ Rankings de ejercicios y comidas mejor valoradas
* 🧭 Interfaz intuitiva, clara e interactiva

---

## 🧩 Funcionalidades clave

### 🏋️ Ejercicio

* Rutinas personalizadas
* Filtro por tipo de ejercicio y disciplina deportiva
* Ranking de ejercicios mejor valorados
* Registro de entrenamientos

### 🥗 Nutrición

* Base de datos de comidas predeterminadas
* Información nutricional (calorías, macros)
* Control diario de ingesta calórica
* Comparación entre calorías consumidas vs quemadas

### 📊 Progreso y motivación

* Perfil de usuario con historial
* Logros y metas alcanzadas
* Objetivos diarios de calorías
* Visualización clara del progreso

### 🌍 Comunidad

* Explorar rutinas y dietas de otros usuarios
* Rankings basados en valoraciones
* Inspiración cuando el progreso se estanca

---

## 🧠 Público objetivo

* Personas que recién comienzan a entrenar
* Usuarios fitness con metas estéticas
* Deportistas que entrenan por rendimiento
* Personas interesadas en nutrición y control calórico

---

## 🛠️ Estado del proyecto

📌 En desarrollo

Este proyecto se encuentra en una fase activa de diseño y construcción, siguiendo principios de **desarrollo centrado en el usuario** y buenas prácticas de UX/UI.

---

## 🔧 Backend (Django + Postgres + DRF)

### Modelado
- Usuarios (auth de Django)
- Rutinas: `WorkoutRoutine` con pasos `WorkoutStep`, ejercicios `Exercise`, etiquetas `Tag`, y favoritos por usuario
- Comidas y dietas: `Meal` (recetas individuales), `MealPlan` con ítems `MealItem`, favoritos de comidas por usuario

### API principal
- CRUD de etiquetas, ejercicios, rutinas, comidas y planes de comida
- Filtros de visibilidad: los no autenticados solo ven contenido público; los autores ven lo propio y lo público
- Favoritos: endpoints para marcar rutinas y comidas
- Autenticación: Token o sesión (configurado en DRF)

### Quickstart local
1. Crea tu entorno: `python -m venv .venv && .venv\Scripts\activate`
2. Instala dependencias: `pip install -r requirements.txt`
3. Copia variables: `cp .env.example .env`
4. Ejecuta migraciones: `python manage.py migrate`
5. Arranca servidor: `python manage.py runserver`

### Con Docker
1. `cp .env.example .env`
2. `docker compose up --build`
3. API disponible en `http://localhost:8000/api/`

### Migraciones
Si cambias modelos: `python manage.py makemigrations workouts && python manage.py migrate`

### Tests
Pendiente agregar suite. Recomendado usar `pytest` o `manage.py test` cuando se definan.


## 🤝 Contribuciones

Las contribuciones son bienvenidas 🙌

Si deseas aportar ideas, mejoras o código:

1. Haz un fork del repositorio
2. Crea una rama con tu feature
3. Envía un Pull Request

---

## 📄 Licencia
Por favor leer la licencia
[IDGAFPL](https://github.com/My2ndAngelic/IDGAFPL)

---

💪 *Entrena con intención. Come con conciencia. Progresa con datos.*
