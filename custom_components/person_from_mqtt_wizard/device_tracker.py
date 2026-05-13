import json
import logging
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.components import mqtt as ha_mqtt
from .const import DOMAIN, CONF_NAME, CONF_IS_REMOTE_BROKER, CONF_BROKER, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_TOPIC, CONF_LAT_KEY, CONF_LON_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the device tracker platform."""
    config = hass.data[DOMAIN][entry.entry_id]
    tracker = MqttPersonTracker(hass, config, entry.entry_id)
    async_add_entities([tracker], True)

class MqttPersonTracker(TrackerEntity):
    """Rappresentazione di un Device Tracker aggiornato via MQTT."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str):
        self.hass = hass
        self._config = config
        self._attr_unique_id = f"mqtt_tracker_{entry_id}"
        self._attr_name = config.get(CONF_NAME, "MQTT Person Tracker")
        self._latitude = None
        self._longitude = None
        self._client = None
        self._unsub_mqtt = None
        self._is_remote_broker = config.get(CONF_IS_REMOTE_BROKER, False)

    async def async_added_to_hass(self):
        """Connettiti a MQTT quando l'entità viene aggiunta a HA."""
        topic = self._config.get(CONF_TOPIC)

        if not self._is_remote_broker:
            _LOGGER.info("Utilizzo il broker MQTT nativo di Home Assistant per il topic: %s", topic)
            
            @callback
            def message_received(msg):
                """Callback per il broker MQTT nativo."""
                self._process_payload(msg.payload)

            self._unsub_mqtt = await ha_mqtt.async_subscribe(
                self.hass, topic, message_received
            )
        else:
            broker = self._config.get(CONF_BROKER)
            port = self._config.get(CONF_PORT)
            user = self._config.get(CONF_USERNAME)
            pwd = self._config.get(CONF_PASSWORD)
            _LOGGER.info("Utilizzo il broker MQTT remoto (%s:%s) per il topic: %s", broker, port, topic)

            self._client = mqtt.Client(CallbackAPIVersion.VERSION1)
            if user:
                self._client.username_pw_set(user, pwd)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message

            # Esegui la connessione MQTT in un thread separato per non bloccare l'async loop di HA
            await self.hass.async_add_executor_job(
                self._connect_mqtt, broker, port
            )
            self._client.loop_start()

    def _connect_mqtt(self, broker, port):
        try:
            self._client.connect(broker, port, 60)
        except Exception as e:
            _LOGGER.error("Errore di connessione MQTT: %s", e)

    def _on_connect(self, client, userdata, flags, rc):
        topic = self._config.get(CONF_TOPIC)
        _LOGGER.info("Connesso al broker MQTT, mi iscrivo a: %s", topic)
        client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        """Callback per il broker MQTT remoto (paho-mqtt)."""
        payload_str = msg.payload.decode("utf-8")
        self._process_payload(payload_str)

    def _process_payload(self, payload_str):
        """Gestisce i messaggi MQTT in arrivo ed estrae le coordinate (usato da entrambi i broker)."""
        try:
            payload = json.loads(payload_str)
            lat_key = self._config.get(CONF_LAT_KEY)
            lon_key = self._config.get(CONF_LON_KEY)

            if lat_key in payload and lon_key in payload:
                self._latitude = float(payload[lat_key])
                self._longitude = float(payload[lon_key])
                
                # Segnala a HA di aggiornare lo stato (thread-safe dal momento che siamo in un callback MQTT)
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
            else:
                _LOGGER.warning("Chiavi %s o %s non trovate nel payload JSON", lat_key, lon_key)
        except json.JSONDecodeError:
            _LOGGER.error("Payload non valido: non è un JSON")
        except ValueError:
            _LOGGER.error("Latitudine o longitudine non validi nel JSON")

    async def async_will_remove_from_hass(self):
        """Disconnetti MQTT quando l'entità viene rimossa o ricaricata."""
        if not self._is_remote_broker and self._unsub_mqtt:
            self._unsub_mqtt()
        elif self._is_remote_broker and self._client:
            self._client.loop_stop()
            self._client.disconnect()

    @property
    def source_type(self):
        return SourceType.GPS

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude
