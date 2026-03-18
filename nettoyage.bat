@echo off
echo NETTOYAGE DU DOSSIER
echo ====================

echo.
echo Suppression des anciens graphiques...
del analyse_complete.png
del analyse_transactions.png

echo.
echo Suppression des fichiers de donnees brutes...
del transactions_seulement.txt
del fichier_complet.txt

echo.
echo Suppression des anciens scripts...
del analyse_transactions.py
del etl_final.py
del extraire_transactions.py
del lire_tout.py

echo.
echo ====================
echo NETTOYAGE TERMINE
echo.
echo Fichiers conserves :
dir *.sql
dir *.csv
dir *.txt
dir *.png
dir *.py
echo ====================
pause