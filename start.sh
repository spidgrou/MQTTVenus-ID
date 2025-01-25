#!/bin/bash

echo "Inizio esecuzione di auto_vrm_id.py"
python3 auto_vrm_id.py
echo "auto_vrm_id.py completato"

echo "Inizio esecuzione di find_ids.py"
python3 find_ids.py
echo "find_ids.py completato"

echo "Esecuzione completata!"