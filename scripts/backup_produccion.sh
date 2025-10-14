#!/bin/bash
# Script de respaldo de producción
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/laboratorio/respaldos"
DB_NAME="laboratorio_sistema"
DB_USER="laboratorio_prod"
# Se espera DB_PASSWORD en entorno
mysqldump -u $DB_USER -p$DB_PASSWORD --single-transaction --routines --triggers $DB_NAME > $BACKUP_DIR/diarios/backup_$DATE.sql
gzip $BACKUP_DIR/diarios/backup_$DATE.sql
find $BACKUP_DIR/diarios -name "*.sql.gz" -mtime +30 -delete
echo "$(date): Respaldo completado - backup_$DATE.sql.gz" >> $BACKUP_DIR/../logs/sistema/respaldos.log
