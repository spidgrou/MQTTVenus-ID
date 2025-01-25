wget -qO - https://github.com/spidgrou/MQTTVenus-ID/archive/refs/tags/latest.tar.gz | tar -xzf - -C /data
mv -f /data/MQTTVenus-ID-latest /data/MQTTVenus-ID
chmod +x /data/MQTTVenus-ID/start.sh
cd /data/MQTTVenus-ID
./start.sh
rm -r /data/MQTTVenus-ID