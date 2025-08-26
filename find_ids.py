import paho.mqtt.client as mqtt
import time
import re
import json
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, SERIAL_FILE, TIMEOUT
import os

found_ids = set()
battery_mon_id = None
start_time = 0
OUTPUT_FILE = "IDs.json"

def load_vrm_id():
    """Carica il VRM ID dal file serial.json."""
    try:
        with open(SERIAL_FILE, 'r') as f:
            data = json.load(f)
            return data['serial']['vrm_id']
    except FileNotFoundError:
        print(f"Errore: File {SERIAL_FILE} non trovato. Assicurati di aver eseguito ask_vrmid.py o auto_vrmid.py.")
        exit(1)
    except json.JSONDecodeError:
      print(f"Errore: File {SERIAL_FILE} contiene un JSON non valido.")
      exit(1)
    except KeyError:
        print(f"Errore: Struttura del file {SERIAL_FILE} non valida.")
        exit(1)

# Carica il VRM ID
vrm_id = load_vrm_id()

# Costruisci il topic e l'espressione regolare dinamici
MQTT_TOPIC = f"N/{vrm_id}/solarcharger/+/DeviceInstance" #topic per i regolatori solari
ID_REGEX = r"N\/" + re.escape(vrm_id) + r"\/solarcharger\/(\d+)\/DeviceInstance" # Regex per estrarre gli ID dei regolatori
BATTERY_TOPIC = f"N/{vrm_id}/system/0/Batteries" #topic per il BatteryMonitor
WAKE_UP_TOPIC = f"R/{vrm_id}/system/0/Serial"  # topic per svegliare il sistema

# Funzione callback per la connessione
def on_connect(client, userdata, flags, rc):
    print(f"Connesso con codice risultato {rc}")
    client.subscribe(MQTT_TOPIC)
    # Non ci si sottoscrive subito al topic del Battery Monitor

# Funzione callback per la ricezione dei messaggi
def on_message(client, userdata, msg):
    global start_time
    global battery_mon_id

    if re.match(ID_REGEX, msg.topic):
        match = re.search(ID_REGEX, msg.topic)
        if match:
            id = int(match.group(1))
            if not found_ids:
                # Se è il primo ID trovato, inizializza start_time
                start_time = time.time()
            found_ids.add(id)  # Aggiungi l'ID anche se è già presente nel set
            print(f"ID regolatore solare trovato: {id}")

def look_for_battery_monitor(client):
    """Funzione per cercare il Battery Monitor dopo che la ricerca dei regolatori è finita."""
    global battery_mon_id

    def on_battery_message(client, userdata, msg):
        """Callback per la ricezione di messaggi sul topic del Battery Monitor."""
        global battery_mon_id
        try:
            payload = json.loads(msg.payload.decode())
            if payload.get('value') and len(payload['value']) > 0 and payload['value'][0].get('instance'):
                battery_mon_id = payload['value'][0]['instance']
                print(f"Battery Monitor ID trovato: {battery_mon_id}")
            else:
                print("Formato dati BatteryMonitor non valido, oppure battery_mon_id non trovato.")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Errore durante l'elaborazione del messaggio BatteryMonitor: {e}")

    # Si sottoscrive al topic del Battery Monitor
    client.subscribe(BATTERY_TOPIC)
    # Imposta la callback per i messaggi del Battery Monitor
    client.message_callback_add(BATTERY_TOPIC, on_battery_message)

    # Attende un breve periodo per la ricezione di eventuali messaggi
    time.sleep(5)  # Attendi 5 secondi

    # Rimuove la callback e si disiscrive dal topic
    client.message_callback_remove(BATTERY_TOPIC)
    client.unsubscribe(BATTERY_TOPIC)

# Funzione per salvare i dati su file JSON
def save_to_json(ids, battery_mon_id):
    try:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r+') as f:
                try:
                    existing_data = json.load(f)
                    existing_data['solar_ids'] = list(ids)
                    if battery_mon_id:
                        existing_data['battery_mon_id'] = battery_mon_id
                    f.seek(0)
                    json.dump(existing_data, f, indent=4)
                    f.truncate()
                    print(f"ID salvati in {OUTPUT_FILE}")
                except json.JSONDecodeError:
                    print(f"Il file {OUTPUT_FILE} esiste ma contiene un JSON non valido, verra sovrascritto")
                    data = {"solar_ids": list(ids)}
                    if battery_mon_id:
                        data["battery_mon_id"] = battery_mon_id
                    with open(OUTPUT_FILE, 'w') as f:
                        json.dump(data, f, indent=4)
                    print(f"ID salvati in {OUTPUT_FILE}")
        else:
            data = {"solar_ids": list(ids)}
            if battery_mon_id:
                data["battery_mon_id"] = battery_mon_id
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"ID salvati in {OUTPUT_FILE}")

    except Exception as e:
        print(f"Errore durante il salvataggio del file JSON: {e}")

# Creazione del client MQTT
#client = mqtt.Client()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

# Impostazione delle credenziali se presenti
if MQTT_USERNAME and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Connessione al broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Avvio del loop di rete (non bloccante)
client.loop_start()

# "Sveglia" il sistema Victron pubblicando un messaggio
client.publish(WAKE_UP_TOPIC, "")
print(f"Messaggio di 'wake-up' inviato su {WAKE_UP_TOPIC}")

# Inizializza il timeout assoluto per la ricerca dei regolatori solari
absolute_timeout = time.time() + TIMEOUT

# Attendi che il timeout assoluto scada per i regolatori solari
while True:
    remaining_time = absolute_timeout - time.time()
    if remaining_time <= 0:
        print("Timeout assoluto scaduto per i regolatori solari. Terminazione in corso...")
        break

    # Stampa il countdown solo se sono stati trovati degli ID
    if found_ids:
        print(f"Tempo rimanente per la ricerca dei regolatori solari: {int(remaining_time)} secondi", end='\r')

    time.sleep(1)  # Aggiorna il countdown ogni secondo

# Cerca il Battery Monitor
look_for_battery_monitor(client)

# Salvataggio dei dati e terminazione
save_to_json(found_ids, battery_mon_id)
client.disconnect()
while client.is_connected():
    time.sleep(0.1)
print("Programma terminato")
