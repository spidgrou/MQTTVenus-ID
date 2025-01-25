#!/bin/bash

echo "Inizio Ricerca Seriale Venus"
python3 /data/MQTTVenus-ID/auto_vrm_id.py
echo "auto_vrm_id.py completato"

echo "Inizio Ricerca Solar IDs"
python3 /data/MQTTVenus-ID/find_ids.py
echo "find_ids.py completato"

echo "Esecuzione completata!"