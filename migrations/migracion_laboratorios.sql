-- ============================================================
-- MIGRACIÓN SISTEMA DE LABORATORIOS - CENTRO MINERO SENA
-- Ejecutar como administrador de MySQL
-- ============================================================

USE laboratorio_sistema;

-- 1. CREAR TABLA LABORATORIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS laboratorios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('laboratorio', 'aula', 'taller', 'almacen') NOT NULL DEFAULT 'laboratorio',
    ubicacion VARCHAR(200),
    capacidad_estudiantes INT DEFAULT 0,
    area_m2 DECIMAL(8,2),
    responsable VARCHAR(100),
    telefono_contacto VARCHAR(20),
    email_contacto VARCHAR(100),
    horario_disponible JSON,
    equipamiento_especializado TEXT,
    normas_seguridad TEXT,
    estado ENUM('activo', 'mantenimiento', 'inactivo') NOT NULL DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    notas TEXT,
    
    INDEX idx_codigo (codigo),
    INDEX idx_tipo (tipo),
    INDEX idx_estado (estado),
    INDEX idx_responsable (responsable)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. INSERTAR LABORATORIOS POR DEFECTO
-- ============================================================
INSERT IGNORE INTO laboratorios 
(codigo, nombre, tipo, ubicacion, capacidad_estudiantes, area_m2, responsable, equipamiento_especializado, normas_seguridad)
VALUES 
('LAB-QUI-001', 'Laboratorio de Química General', 'laboratorio', 'Edificio A - Piso 2', 25, 80.0, 'Instructor de Química', 'Campanas extractoras, balanzas analíticas, espectrofotómetros', 'Uso obligatorio de bata, gafas y guantes. Prohibido comer o beber.'),
('LAB-QUI-002', 'Laboratorio de Química Analítica', 'laboratorio', 'Edificio A - Piso 2', 20, 75.0, 'Instructor de Química Analítica', 'Cromatógrafos, espectrometría de masas, HPLC', 'Área de alta precisión. Acceso restringido a personal autorizado.'),
('LAB-MIN-001', 'Laboratorio de Mineralogía', 'laboratorio', 'Edificio B - Piso 1', 30, 90.0, 'Instructor de Mineralogía', 'Microscopios petrográficos, difractómetros de rayos X', 'Manejo cuidadoso de muestras minerales. Uso de mascarillas.'),
('LAB-MET-001', 'Laboratorio de Metalurgia', 'laboratorio', 'Edificio C - Piso 1', 15, 120.0, 'Instructor de Metalurgia', 'Hornos de fusión, equipos de fundición, análisis térmico', 'Área de alta temperatura. Equipo de protección completo obligatorio.'),
('AULA-001', 'Aula de Química Teórica', 'aula', 'Edificio A - Piso 1', 40, 60.0, 'Coordinador Académico', 'Proyector, sistema audiovisual, modelos moleculares', 'Aula estándar. Mantener orden y limpieza.'),
('TALL-001', 'Taller de Preparación de Muestras', 'taller', 'Edificio B - Sótano', 12, 50.0, 'Técnico de Laboratorio', 'Molinos, tamices, prensas, equipos de trituración', 'Área de ruido. Uso obligatorio de protección auditiva.'),
('ALM-001', 'Almacén de Reactivos', 'almacen', 'Edificio A - Sótano', 0, 40.0, 'Almacenista', 'Estanterías especializadas, sistema de ventilación, alarmas', 'Acceso restringido. Control de temperatura y humedad.');

-- 3. MODIFICAR TABLA INVENTARIO
-- ============================================================
-- Verificar si la columna existe antes de agregarla
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'inventario' 
     AND COLUMN_NAME = 'laboratorio_id') = 0,
    'ALTER TABLE inventario ADD COLUMN laboratorio_id INT NOT NULL DEFAULT 1 AFTER id',
    'SELECT "Columna laboratorio_id ya existe en inventario" as mensaje'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Crear índice si no existe
CREATE INDEX IF NOT EXISTS idx_inventario_laboratorio_id ON inventario (laboratorio_id);

-- 4. MODIFICAR TABLA EQUIPOS
-- ============================================================
-- Verificar si la columna existe antes de agregarla
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'equipos' 
     AND COLUMN_NAME = 'laboratorio_id') = 0,
    'ALTER TABLE equipos ADD COLUMN laboratorio_id INT NOT NULL DEFAULT 1 AFTER id',
    'SELECT "Columna laboratorio_id ya existe en equipos" as mensaje'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Crear índice si no existe
CREATE INDEX IF NOT EXISTS idx_equipos_laboratorio_id ON equipos (laboratorio_id);

-- 5. MIGRAR DATOS EXISTENTES
-- ============================================================
-- Mapear ubicaciones a laboratorios para inventario
UPDATE inventario 
SET laboratorio_id = CASE 
    WHEN LOWER(ubicacion) LIKE '%lab química%' OR LOWER(ubicacion) LIKE '%laboratorio a%' THEN 1
    WHEN LOWER(ubicacion) LIKE '%analítica%' OR LOWER(ubicacion) LIKE '%laboratorio b%' THEN 2
    WHEN LOWER(ubicacion) LIKE '%mineralogía%' OR LOWER(ubicacion) LIKE '%mineral%' THEN 3
    WHEN LOWER(ubicacion) LIKE '%metalurgia%' OR LOWER(ubicacion) LIKE '%metal%' THEN 4
    WHEN LOWER(ubicacion) LIKE '%aula%' THEN 5
    WHEN LOWER(ubicacion) LIKE '%taller%' THEN 6
    WHEN LOWER(ubicacion) LIKE '%almacén%' OR LOWER(ubicacion) LIKE '%almacen%' THEN 7
    ELSE 1
END
WHERE laboratorio_id = 1;

-- Mapear ubicaciones a laboratorios para equipos
UPDATE equipos 
SET laboratorio_id = CASE 
    WHEN LOWER(ubicacion) LIKE '%lab química%' OR LOWER(ubicacion) LIKE '%laboratorio a%' THEN 1
    WHEN LOWER(ubicacion) LIKE '%analítica%' OR LOWER(ubicacion) LIKE '%laboratorio b%' THEN 2
    WHEN LOWER(ubicacion) LIKE '%mineralogía%' OR LOWER(ubicacion) LIKE '%mineral%' THEN 3
    WHEN LOWER(ubicacion) LIKE '%metalurgia%' OR LOWER(ubicacion) LIKE '%metal%' THEN 4
    WHEN LOWER(ubicacion) LIKE '%aula%' THEN 5
    WHEN LOWER(ubicacion) LIKE '%taller%' THEN 6
    WHEN LOWER(ubicacion) LIKE '%almacén%' OR LOWER(ubicacion) LIKE '%almacen%' THEN 7
    ELSE 1
END
WHERE laboratorio_id = 1;

-- 6. CREAR RESTRICCIONES DE CLAVE FORÁNEA
-- ============================================================
-- FK para inventario (solo si no existe)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'inventario' 
     AND CONSTRAINT_NAME = 'fk_inventario_laboratorio') = 0,
    'ALTER TABLE inventario ADD CONSTRAINT fk_inventario_laboratorio FOREIGN KEY (laboratorio_id) REFERENCES laboratorios(id) ON DELETE RESTRICT ON UPDATE CASCADE',
    'SELECT "FK inventario -> laboratorios ya existe" as mensaje'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- FK para equipos (solo si no existe)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
     WHERE TABLE_SCHEMA = DATABASE() 
     AND TABLE_NAME = 'equipos' 
     AND CONSTRAINT_NAME = 'fk_equipos_laboratorio') = 0,
    'ALTER TABLE equipos ADD CONSTRAINT fk_equipos_laboratorio FOREIGN KEY (laboratorio_id) REFERENCES laboratorios(id) ON DELETE RESTRICT ON UPDATE CASCADE',
    'SELECT "FK equipos -> laboratorios ya existe" as mensaje'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 7. CREAR VISTAS ÚTILES
-- ============================================================
-- Vista resumen por laboratorio
CREATE OR REPLACE VIEW vista_resumen_laboratorios AS
SELECT 
    l.id,
    l.codigo,
    l.nombre,
    l.tipo,
    l.ubicacion,
    l.estado,
    COUNT(DISTINCT e.id) as total_equipos,
    COUNT(DISTINCT i.id) as total_items_inventario,
    COUNT(DISTINCT CASE WHEN e.estado = 'disponible' THEN e.id END) as equipos_disponibles,
    COUNT(DISTINCT CASE WHEN i.cantidad_actual <= i.cantidad_minima THEN i.id END) as items_stock_bajo,
    SUM(DISTINCT i.cantidad_actual * IFNULL(i.costo_unitario, 0)) as valor_total_inventario
FROM laboratorios l
LEFT JOIN equipos e ON l.id = e.laboratorio_id
LEFT JOIN inventario i ON l.id = i.laboratorio_id
GROUP BY l.id, l.codigo, l.nombre, l.tipo, l.ubicacion, l.estado;

-- Vista inventario detallado
CREATE OR REPLACE VIEW vista_inventario_detallado AS
SELECT 
    l.codigo as laboratorio_codigo,
    l.nombre as laboratorio_nombre,
    l.tipo as laboratorio_tipo,
    i.id as item_id,
    i.nombre as item_nombre,
    i.categoria,
    i.cantidad_actual,
    i.cantidad_minima,
    i.unidad,
    i.ubicacion as ubicacion_especifica,
    i.proveedor,
    i.costo_unitario,
    (i.cantidad_actual * IFNULL(i.costo_unitario, 0)) as valor_total,
    CASE 
        WHEN i.cantidad_actual <= i.cantidad_minima THEN 'CRÍTICO'
        WHEN i.cantidad_actual <= i.cantidad_minima * 1.5 THEN 'BAJO'
        ELSE 'NORMAL'
    END as nivel_stock,
    DATE_FORMAT(i.fecha_vencimiento, '%Y-%m-%d') as fecha_vencimiento
FROM laboratorios l
INNER JOIN inventario i ON l.id = i.laboratorio_id
WHERE l.estado = 'activo'
ORDER BY l.codigo, i.categoria, i.nombre;

-- Vista equipos por laboratorio
CREATE OR REPLACE VIEW vista_equipos_laboratorio AS
SELECT 
    l.codigo as laboratorio_codigo,
    l.nombre as laboratorio_nombre,
    l.tipo as laboratorio_tipo,
    e.id as equipo_id,
    e.nombre as equipo_nombre,
    e.tipo as equipo_tipo,
    e.estado as equipo_estado,
    e.ubicacion as ubicacion_especifica,
    DATE_FORMAT(e.ultima_calibracion, '%Y-%m-%d') as ultima_calibracion,
    DATE_FORMAT(e.proximo_mantenimiento, '%Y-%m-%d') as proximo_mantenimiento,
    CASE 
        WHEN e.proximo_mantenimiento <= CURDATE() THEN 'VENCIDO'
        WHEN e.proximo_mantenimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'PRÓXIMO'
        ELSE 'VIGENTE'
    END as estado_mantenimiento
FROM laboratorios l
INNER JOIN equipos e ON l.id = e.laboratorio_id
WHERE l.estado = 'activo'
ORDER BY l.codigo, e.tipo, e.nombre;

-- 8. OTORGAR PERMISOS AL USUARIO DE APLICACIÓN
-- ============================================================
-- Otorgar permisos sobre las nuevas tablas y vistas
GRANT SELECT, INSERT, UPDATE, DELETE ON laboratorios TO 'laboratorio_prod'@'localhost';
GRANT SELECT ON vista_resumen_laboratorios TO 'laboratorio_prod'@'localhost';
GRANT SELECT ON vista_inventario_detallado TO 'laboratorio_prod'@'localhost';
GRANT SELECT ON vista_equipos_laboratorio TO 'laboratorio_prod'@'localhost';

-- 9. MOSTRAR RESUMEN
-- ============================================================
SELECT 'MIGRACIÓN COMPLETADA EXITOSAMENTE' as estado;

SELECT 
    'Laboratorios creados' as concepto,
    COUNT(*) as cantidad
FROM laboratorios
UNION ALL
SELECT 
    'Items de inventario migrados' as concepto,
    COUNT(*) as cantidad
FROM inventario WHERE laboratorio_id > 0
UNION ALL
SELECT 
    'Equipos migrados' as concepto,
    COUNT(*) as cantidad
FROM equipos WHERE laboratorio_id > 0;

-- Mostrar distribución por laboratorio
SELECT 
    l.codigo,
    l.nombre,
    COUNT(DISTINCT e.id) as equipos,
    COUNT(DISTINCT i.id) as items_inventario
FROM laboratorios l
LEFT JOIN equipos e ON l.id = e.laboratorio_id
LEFT JOIN inventario i ON l.id = i.laboratorio_id
GROUP BY l.id, l.codigo, l.nombre
ORDER BY l.codigo;
