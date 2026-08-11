-- Apache AGE doit être installé avant les autres extensions : sa création
-- matérialise le schéma ag_catalog référencé par le search_path du serveur.
-- Le chemin d'amorçage exclut volontairement les schémas encore inexistants.
SET search_path = public, pg_catalog;
CREATE EXTENSION IF NOT EXISTS age;
