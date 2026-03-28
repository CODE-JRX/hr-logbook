@echo off
conda activate tf
mysql -u root -p hrmo_elog_db ^< scripts\migrate_pds_schema.sql
pause

