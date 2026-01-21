# EstherVital Backend API

API REST para la gestión de la estética EstherVital. Construida con **FastAPI** y **PostgreSQL** (Supabase).

## 🚀 Configuración Inicial (Primera vez)

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd esthervital-back
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

```bash
# Windows
.\venv\Scripts\Activate

# Linux/Mac
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

```bash
copy .env.example .env
```

Edita el archivo `.env` con tu `DATABASE_URL` de Supabase.

### 6. Aplicar migraciones

```bash
alembic upgrade head
```

### 7. Iniciar servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en: http://127.0.0.1:8000

---

## 🔄 Actualizar versión existente

Si ya tienes el proyecto configurado y quieres actualizar:

```bash
# 1. Obtener últimos cambios
git pull origin develop

# 2. Activar entorno virtual
.\venv\Scripts\Activate

# 3. Actualizar dependencias (si hay nuevas)
pip install -r requirements.txt

# 4. Aplicar nuevas migraciones (si hay cambios en la BD)
alembic upgrade head

# 5. Iniciar servidor
uvicorn main:app --reload
```

---

## 📖 Documentación API

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

---

## 🛠️ Comandos útiles

| Comando                                            | Descripción                         |
| -------------------------------------------------- | ----------------------------------- |
| `uvicorn main:app --reload`                        | Iniciar servidor en modo desarrollo |
| `alembic revision --autogenerate -m "descripcion"` | Crear nueva migración               |
| `alembic upgrade head`                             | Aplicar migraciones pendientes      |
| `alembic downgrade -1`                             | Revertir última migración           |

---

## 📁 Estructura del proyecto

```
esthervital-back/
├── alembic/              # Migraciones de base de datos
├── shared/               # Código compartido (database.py)
├── users/                # Módulo de usuarios
│   ├── application/      # Casos de uso
│   ├── infrastructure/   # Modelos y repositorios
│   └── presentation/     # Routers y schemas
├── .env.example          # Template de variables de entorno
├── main.py               # Punto de entrada de la aplicación
└── requirements.txt      # Dependencias del proyecto
```

---

## 👥 Flujo de trabajo Git

- **`master`**: Rama de producción (estable)
- **`develop`**: Rama de desarrollo

Siempre trabaja sobre `develop` y crea pull requests hacia `master`.
