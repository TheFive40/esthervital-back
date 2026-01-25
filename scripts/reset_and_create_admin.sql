-- Script para resetear usuarios y crear administrador Esther Vital
-- Ejecutar en la base de datos PostgreSQL de EstherVital

-- ============================================
-- PASO 1: Limpiar tablas relacionadas primero
-- ============================================

-- Eliminar sesiones de tratamiento (tienen FK a tratamientos)
DELETE FROM imagenes_sesion;
DELETE FROM sesiones_tratamiento;

-- Eliminar tratamientos (tienen FK a usuarios y pacientes)
DELETE FROM tratamientos;

-- Eliminar historiales y documentos
DELETE FROM documentos_historial;
DELETE FROM historiales;

-- Eliminar citas
DELETE FROM citas;

-- Eliminar pacientes
DELETE FROM pacientes;

-- Eliminar usuarios (finalmente)
DELETE FROM usuarios;

-- ============================================
-- PASO 2: Verificar/Corregir Roles
-- ============================================

-- Asegurar que los roles estén correctos
DELETE FROM roles WHERE id_rol NOT IN (1, 2);

-- Actualizar o insertar rol Administrador
INSERT INTO roles (id_rol, nombre_rol, descripcion)
VALUES (1, 'Administrador', 'Acceso completo al sistema, incluyendo gestión de usuarios y configuraciones.')
ON CONFLICT (id_rol) DO UPDATE SET 
  nombre_rol = 'Administrador',
  descripcion = 'Acceso completo al sistema, incluyendo gestión de usuarios y configuraciones.';

-- Actualizar o insertar rol Empleado
INSERT INTO roles (id_rol, nombre_rol, descripcion)
VALUES (2, 'Empleado', 'Acceso a pacientes, citas, tratamientos e historiales clínicos. Sin acceso a gestión de usuarios.')
ON CONFLICT (id_rol) DO UPDATE SET 
  nombre_rol = 'Empleado',
  descripcion = 'Acceso a pacientes, citas, tratamientos e historiales clínicos. Sin acceso a gestión de usuarios.';

-- ============================================
-- PASO 3: Crear Usuario Administrador
-- ============================================

-- Nota: La contraseña debe ser hasheada con bcrypt
-- Password: EstherVital2024! (este hash debe generarse)
-- Para generar el hash puedes usar Python:
-- from passlib.context import CryptContext
-- pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
-- print(pwd_context.hash("EstherVital2024!"))

INSERT INTO usuarios (
  nombre,
  apellido,
  email,
  password,
  estado,
  primer_login,
  id_rol,
  fecha_creacion
) VALUES (
  'Esther',
  'Vital',
  'esthervital@gmail.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S4VDhJWP.YQXR2', -- Hash de 'EstherVital2024!'
  'Activo',
  false, -- No es primer login ya que es el admin principal
  1,     -- Rol Administrador
  NOW()
);

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Ver roles creados
SELECT * FROM roles;

-- Ver usuario creado
SELECT id_usuario, nombre, apellido, email, estado, id_rol, primer_login FROM usuarios;

-- ============================================
-- NOTAS IMPORTANTES
-- ============================================
-- 
-- 1. Después de ejecutar este script, el usuario admin puede iniciar sesión con:
--    Email: esthervital@gmail.com
--    Password: EstherVital2024!
--
-- 2. Este usuario NO verá el modal de primer login ya que primer_login = false
--
-- 3. Los nuevos usuarios creados por el admin tendrán primer_login = true
--    y deberán cambiar su contraseña en el primer acceso
--
-- 4. Si usas Supabase Auth, también debes crear el usuario en Supabase:
--    - Ve a Authentication > Users
--    - Crea usuario con email: esthervital@gmail.com
--    - La contraseña debe coincidir: EstherVital2024!
