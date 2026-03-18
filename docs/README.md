# Projet ETL - Smart Personal Finance Wallet

## Description
Ce projet realise l'ETL (Extract, Transform, Load) des donnees de transactions
pour l'application de gestion financiere personnelle.

## Architecture
- `src/extract/` : Extraction des donnees du fichier SQL
- `src/transform/` : Nettoyage et classification
- `src/load/` : Sauvegarde des resultats
- `src/visualization/` : Creation des graphiques
- `data/` : Fichier source SQL
- `output/` : Resultats generes

## Execution
```bash
python run.py