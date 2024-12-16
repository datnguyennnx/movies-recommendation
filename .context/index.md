---
module-name: "Movies Recommender"
description: "An AI-powered movie recommendation system that leverages machine learning and natural language processing to provide personalized movie suggestions."
related-modules:
  - name: Backend (recommender-be)
    path: ./recommender-be
  - name: Frontend (recommender-ui)
    path: ./recommender-ui
architecture:
  style: "Microservices with Decoupled Frontend and Backend"
  components:
    - name: "Backend Service"
      description: "Python-based backend handling recommendation logic, data processing, and AI interactions"
    - name: "Frontend Service"
      description: "Next.js React application providing user interface and interactions"
    - name: "Database"
      description: "PostgreSQL with pgvector for vector-based movie recommendations"
  patterns:
    - name: "Microservices"
      usage: "Separate backend and frontend services for scalability and independent deployment"
    - name: "AI-Powered Recommendations"
      usage: "Utilize machine learning models to generate personalized movie recommendations"
---

# Movies Recommender Project Overview

## Project Purpose
The Movies Recommender is an intelligent movie recommendation system that uses advanced AI techniques to suggest personalized movie recommendations based on user preferences, viewing history, and contextual understanding.

## Key Features
- AI-powered movie recommendations
- Natural language interaction for movie discovery
- Machine learning-based suggestion engine
- User-friendly web interface

## Technical Architecture
The project is structured as a microservices architecture with two primary components:

1. **Backend (recommender-be)**
   - Language: Python
   - Key Technologies:
     * FastAPI for web framework
     * SQLAlchemy for database ORM
     * pgvector for vector-based recommendations
     * LLM Model for recommendation generation

2. **Frontend (recommender-ui)**
   - Language: TypeScript
   - Framework: Next.js
   - Key Features:
     * Responsive design
     * Real-time chat interface
     * Authentication
     * Interactive recommendation display

## Deployment
- Containerized using Docker
- Docker Compose for local development
- Supports easy scaling and deployment

## Development Principles
- Modular architecture
- AI-first approach
- Emphasis on personalization
- Continuous improvement of recommendation algorithms
