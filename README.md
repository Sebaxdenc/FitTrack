# 🏋️‍♂️ Fitness Tracker App

A mobile application designed for people who want to **train better, eat better, and track their progress in a clear and motivating way**. From beginners to advanced athletes, this project aims to centralize workouts, nutrition, and goals in one place.

---

## 🚀 Project Description

**Fitness Tracker App** is an application to log exercises and daily meals, discover routines and diets from other users, and track physical and nutritional progress over time. The main focus is **motivation**, **personalization**, and an **intuitive user experience**.

Users don’t need to memorize routines, keep notes, or use multiple apps: everything lives here.

---

## 🎯 Main Objectives

* Make it easy to track workout routines from a mobile device
* Help users manage their nutrition and calorie intake
* Motivate through daily goals, rankings, and progress visualization
* Provide relevant content based on body type, sport, or fitness goals
* Encourage community by sharing routines and diets

---

## 👥 User Stories Covered

The application is designed around the following real needs:

* Save workout routines to know exactly what to do at the gym
* Recommendations for sports equipment for beginners
* Access diets and routines created by other users
* Filters by sport, body type, and fitness goals
* Personal profile with history, achievements, and progress
* Daily calorie burn goals with visual feedback
* Quick meal logging with nutritional information
* Caloric balance tracking (deficit or surplus)
* Rankings of top-rated exercises and meals
* Clear, intuitive, and interactive interface

---

## 🧩 Key Features

### 🏋️ Exercise

* Personalized routines
* Filtering by exercise type and sport discipline
* Ranking of top-rated exercises
* Workout tracking

### 🥗 Nutrition

* Database of predefined meals
* Nutritional information (calories, macros)
* Daily calorie intake tracking
* Comparison between consumed vs burned calories

### 📊 Progress & Motivation

* User profile with history
* Achievements and goals
* Daily calorie targets
* Clear progress visualization

### 🌍 Community

* Explore routines and diets from other users
* Rankings based on ratings
* Inspiration when progress stalls

---

## 🧠 Target Audience

* Beginners starting their fitness journey
* Fitness users with aesthetic goals
* Athletes training for performance
* People interested in nutrition and calorie tracking

---

## 🛠️ Project Status

📌 In development

This project is currently in an active design and development phase, following **user-centered design principles** and good UX/UI practices.

---

## 🔧 Backend (Django + Postgres + DRF)

### Modeling

* Users (Django auth)
* Workouts: `WorkoutRoutine` with steps `WorkoutStep`, exercises `Exercise`, tags `Tag`, and user favorites
* Meals and diets: `Meal` (individual recipes), `MealPlan` with items `MealItem`, and user meal favorites

### Main API

* CRUD for tags, exercises, routines, meals, and meal plans
* Visibility filters: unauthenticated users only see public content; authors see their own and public content
* Favorites: endpoints to mark routines and meals
* Authentication: Token or session (configured in DRF)

### Local Quickstart

1. Create environment: `python -m venv .venv && .venv\Scripts\activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`

### With Docker

1. Copy `.env.example` to `.env`
2. Run `docker compose up --build`
3. Docker Compose uses Postgres and applies migrations before starting Gunicorn
4. API available at `http://localhost:8000/api/`

### Migrations

If you modify models:
`python manage.py makemigrations workouts && python manage.py migrate`

### Tests

Test suite pending. Recommended to use `pytest` or `manage.py test` once defined.

---

## 🤝 Contributions

Contributions are welcome.

If you want to contribute ideas, improvements, or code:

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

---

## 📄 License

Please read the license
[IDGAFPL](https://github.com/My2ndAngelic/IDGAFPL)

---

Train with intention. Eat with awareness. Progress with data.
