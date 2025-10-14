-- Agregar columna equipo_id a la tabla equipos si no existe

-- Verificar si la columna existe
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'laboratorio_sistema' 
  AND TABLE_NAME = 'equipos' 
  AND COLUMN_NAME = 'equipo_id';

-- Si no existe, agregarla
ALTER TABLE equipos 
ADD COLUMN IF NOT EXISTS equipo_id VARCHAR(50) UNIQUE AFTER id;

-- Actualizar registros existentes que no tengan equipo_id
UPDATE equipos 
SET equipo_id = CONCAT('EQ_', UPPER(SUBSTRING(MD5(CONCAT(id, nombre)), 1, 8)))
WHERE equipo_id IS NULL OR equipo_id = '';

-- Verificar
SELECT id, equipo_id, nombre FROM equipos LIMIT 5;
