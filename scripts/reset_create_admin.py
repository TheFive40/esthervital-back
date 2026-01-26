"""
Script para resetear la base de datos y crear usuario administrador
Ejecutar desde la carpeta esthervital-back con el virtualenv activado:
    python scripts/reset_create_admin.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from passlib.context import CryptContext
from shared.database import engine, SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_database():
    """Limpia todas las tablas en el orden correcto respetando foreign keys"""
    
    db = SessionLocal()
    
    try:
        print("🗑️  Limpiando base de datos...")
        
        # Orden de eliminación respetando FK
        tables_to_clear = [
            "imagenes_sesion",
            "sesiones_tratamiento",
            "tratamientos",
            "documentos",  # Nombre correcto de la tabla
            "historiales_clinicos",  # Nombre correcto
            "citas",
            "pacientes",
            "usuarios"
        ]
        
        for table in tables_to_clear:
            try:
                db.execute(text(f"DELETE FROM {table}"))
                db.commit()  # Commit after each successful delete
                print(f"   ✓ Tabla {table} limpiada")
            except Exception as e:
                db.rollback()  # Rollback failed transaction
                # Try to continue with other tables
                print(f"   ⚠ Tabla {table}: tabla no existe o ya vacía")
        
        print("✅ Base de datos limpiada\n")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error limpiando BD: {e}")
        raise
    finally:
        db.close()


def setup_roles():
    """Asegura que los roles estén correctamente configurados"""
    
    db = SessionLocal()
    
    try:
        print("👥 Configurando roles...")
        
        # Verificar/crear rol Administrador
        db.execute(text("""
            INSERT INTO roles (id_rol, nombre_rol, descripcion)
            VALUES (1, 'Administrador', 'Acceso completo al sistema, incluyendo gestión de usuarios y configuraciones.')
            ON CONFLICT (id_rol) DO UPDATE SET 
                nombre_rol = 'Administrador',
                descripcion = 'Acceso completo al sistema, incluyendo gestión de usuarios y configuraciones.'
        """))
        print("   ✓ Rol Administrador configurado")
        
        # Verificar/crear rol Empleado
        db.execute(text("""
            INSERT INTO roles (id_rol, nombre_rol, descripcion)
            VALUES (2, 'Empleado', 'Acceso a pacientes, citas, tratamientos e historiales clínicos.')
            ON CONFLICT (id_rol) DO UPDATE SET 
                nombre_rol = 'Empleado',
                descripcion = 'Acceso a pacientes, citas, tratamientos e historiales clínicos.'
        """))
        print("   ✓ Rol Empleado configurado")
        
        db.commit()
        print("✅ Roles configurados\n")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error configurando roles: {e}")
        raise
    finally:
        db.close()


def create_admin_user():
    """Crea el usuario administrador principal"""
    
    db = SessionLocal()
    
    # Datos del administrador
    admin_data = {
        "nombre": "Esther",
        "apellido": "Vital",
        "email": "esthervital@gmail.com",
        "password": "Admin123!",  # Contraseña más corta
        "id_rol": 1
    }
    
    try:
        print("👤 Creando usuario administrador...")
        print(f"   Email: {admin_data['email']}")
        print(f"   Password: {admin_data['password']}")
        
        # Generar hash de la contraseña usando bcrypt directamente
        import bcrypt
        password_bytes = admin_data['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        
        # Insertar usuario
        db.execute(text("""
            INSERT INTO usuarios (nombre, apellido, email, password, estado, primer_login, id_rol, fecha_creacion)
            VALUES (:nombre, :apellido, :email, :password, 'Activo', false, :id_rol, NOW())
        """), {
            "nombre": admin_data["nombre"],
            "apellido": admin_data["apellido"],
            "email": admin_data["email"],
            "password": hashed_password,
            "id_rol": admin_data["id_rol"]
        })
        
        db.commit()
        print("✅ Usuario administrador creado\n")
        
        print("=" * 50)
        print("🎉 CONFIGURACIÓN COMPLETADA")
        print("=" * 50)
        print(f"\n📧 Email: {admin_data['email']}")
        print(f"🔑 Password: {admin_data['password']}")
        print("\n⚠️  IMPORTANTE: Si usas Supabase Auth, también debes crear")
        print("   este usuario en Authentication > Users con las mismas credenciales.")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creando admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🏥 EstherVital - Reset y Creación de Admin")
    print("=" * 50 + "\n")
    
    confirm = input("⚠️  Esto ELIMINARÁ todos los datos. ¿Continuar? (si/no): ")
    
    if confirm.lower() != "si":
        print("Operación cancelada.")
        sys.exit(0)
    
    print()
    
    reset_database()
    setup_roles()
    create_admin_user()
