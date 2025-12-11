# ONLY - Sistema de Gestión de E-commerce y Logística 🇨🇴

Bienvenido al repositorio oficial del equipo de desarrollo para la transformación digital de **Tiendas ONLY**. Este proyecto simula la estructura, gestión y despliegue de código para la plataforma de ventas online y gestión de inventario.

## Metodología de Trabajo (Agile & GitHub Flow)

Para garantizar una entrega continua y ordenada, hemos implementado una metodología híbrida (Scrum/Kanban) utilizando las herramientas nativas de GitHub.

### 1. Estimación con Planning Poker 
Utilizamos un sistema de etiquetado (Labels) basado en tallas de ropa (acorde a la temática de la tienda) para estimar la complejidad de cada *Issue*:

* `size: XS` (Extra Small): Tareas triviales (ej. corregir un texto).
* `size: S` (Small): Tareas rápidas (< 2 horas).
* `size: M` (Medium): Tareas estándar (medio día de trabajo).
* `size: L` (Large): Funcionalidades complejas (1-2 días).
* `size: XL` (Extra Large): Módulos enteros que requieren subdivisión.

### 2. Gestión de Tablero (Projects) 
Gestionamos el flujo de trabajo en **GitHub Projects** con las siguientes columnas de estado:
* **Backlog:** Historias de usuario pendientes.
* **In Progress:** Tareas en desarrollo activo (WIP limitado).
* **In Review:** Pull Requests abiertos esperando revisión de pares.
* **Done:** Código fusionado (merged) a la rama principal.

> **Nota:** Cada miembro tiene asignadas actualmente 5 tareas activas o planificadas para este Sprint.

### 3. Estrategia de Ramas (Branching Strategy) 
Mantenemos la integridad del código mediante ramas independientes para cada funcionalidad:
* `main`: Producción (estable).
* `develop`: Integración.
* `feature/nombre-funcionalidad`: Ramas de trabajo individual.

---

## Roadmap y Planificación Temporal

El proyecto se visualiza a través de un **Roadmap** que prioriza las entregas:
1.  **Q1 (Done):** Configuración inicial, estructura de BD y maquetación básica (Tareas de baja complejidad o base).
2.  **Q2 (In Progress):** Lógica de negocio y conexión de API.
3.  **Q3 (Backlog):** Funcionalidades avanzadas, reportes y optimización (Tareas de mayor complejidad o futuras).

---

