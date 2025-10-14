-- =============================
-- TABLAS PARA RECONOCIMIENTO FACIAL
-- Ejecutar como administrador de MySQL
-- =============================

USE laboratorio_sistema;

-- Crear tabla para almacenar datos faciales
CREATE TABLE IF NOT EXISTS usuarios_facial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id VARCHAR(20) NOT NULL,
    encoding_facial LONGTEXT NOT NULL,
    imagen_referencia LONGBLOB,
    calidad_imagen DECIMAL(5,2) DEFAULT 0.0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    notas TEXT,
    
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_activo (activo),
    INDEX idx_fecha_registro (fecha_registro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla para logs de registro facial
CREATE TABLE IF NOT EXISTS logs_registro_facial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id VARCHAR(20) NOT NULL,
    accion ENUM('registro', 'actualizacion', 'eliminacion', 'intento_fallido') NOT NULL,
    detalle TEXT,
    calidad_imagen DECIMAL(5,2),
    ip_origen VARCHAR(45),
    user_agent TEXT,
    exitoso BOOLEAN DEFAULT FALSE,
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_accion (accion),
    INDEX idx_fecha_evento (fecha_evento),
    INDEX idx_exitoso (exitoso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verificar creación
SELECT 'Tablas de reconocimiento facial creadas exitosamente' as mensaje;
SELECT COUNT(*) as usuarios_facial_count FROM usuarios_facial;
SELECT COUNT(*) as logs_facial_count FROM logs_registro_facial;
