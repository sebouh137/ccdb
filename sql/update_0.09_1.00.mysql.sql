ALTER TABLE `users` ADD COLUMN `isDeleted` TINYINT(1) NOT NULL DEFAULT 0  AFTER `info`;
UPDATE schemaVersions SET schemaVersion=4 WHERE id=1;

