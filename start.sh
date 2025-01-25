#!/bin/bash

echo "Inizio Ricerca Seriale Venus"
python3 auto_vrm_id.py
echo "auto_vrm_id.py completato"

echo "Inizio Ricerca Solar IDs"
python3 find_ids.py
echo "find_ids.py completato"

echo "Esecuzione completata!"