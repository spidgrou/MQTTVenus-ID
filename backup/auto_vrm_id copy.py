import paho.mqtt.client as mqtt
import json
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, SERIAL_FILE
import time
import os # Importiamo il modulo os


def get_and_save_vrm_id():
    """Si connette al server MQTT, ottiene il VRM ID e lo salva nel file serial.json."""

    def on_connect(client, userdata, flags, rc):
        """Funzione callback per la connessione."""
        print(f"Connesso con codice risultato {rc}")
        client.subscribe("N/+/system/0/Serial")  # Ci sottoscriviamo al topic con wildcard

    def on_message(client, userdata, msg):
        """Funzione callback per la ricezione dei messaggi."""
        try:
            payload = msg.payload.decode()  # Decodifica il payload da byte a stringa
            vrm_id = json.loads(payload)['value']  # Estrae il VRM ID dall'oggetto JSON
            print(f"VRM ID ricevuto: {vrm_id}")
            save_vrm_id_to_json(vrm_id)  # salviamo l'id
            client.disconnect()  # ci disconnettiamo dopo la ricezione
        except Exception as e:
            print(f"Errore durante l'elaborazione del messaggio: {e}")

    def save_vrm_id_to_json(vrm_id, filename=SERIAL_FILE):
        """Salva il VRM ID nel file JSON."""
        data = {"serial": {"vrm_id": vrm_id}}
        try:
            if os.path.exists(filename):
                # Se il file esiste, lo apriamo in modalità lettura, carichiamo i dati esistenti, li aggiorniamo e li salviamo
                with open(filename, 'r+') as f:  # lettura e scrittura
                    try:
                        existing_data = json.load(f)
                        existing_data['serial']['vrm_id'] = vrm_id  # Sovrascrive il vecchio valore con il nuovo
                        f.seek(0)  # riporta la testina di lettura all'inizio del file
                        json.dump(existing_data, f, indent=4)  # sovrascrive il file con i dati modificati
                        f.truncate()  # tronca il file se i dati nuovi sono più piccoli dei vecchi
                        print(f"VRM ID aggiornato nel file {filename}")
                    except json.JSONDecodeError:  # il file esiste ma il contenuto non è valido
                        print(f"Il file {filename} esiste ma contiene un JSON non valido, verra sovrascritto")
                        with open(filename, 'w') as f:  # sovrascrive il file con i dati nuovi
                            json.dump(data, f, indent=4)
                        print(f"VRM ID salvato in {filename}")
            else:
                # Se il file non esiste, lo creiamo
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"VRM ID salvato in {filename}")
        except Exception as e:
            print(f"Errore durante la gestione del file JSON: {e}")

    # Creazione del client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Impostazione delle credenziali se presenti
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # Connessione al broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Avvio del loop di rete (non bloccante)
    client.loop_forever()


if __name__ == "__main__":
    get_and_save_vrm_id()