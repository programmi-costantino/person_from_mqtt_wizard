import json
import logging
import paho.mqtt.client as mqtt
from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_BROKER, CONF_PORT, CONF_TOPIC, CONF_LAT_KEY, CONF_LON_KEY

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
        self._attr_name = "MQTT Person Tracker"
        self._latitude = None
        self._longitude = None
        self._client = None

    async def async_added_to_hass(self):
        """Connettiti a MQTT quando l'entità viene aggiunta a HA."""
        broker = self._config.get(CONF_BROKER)
        port = self._config.get(CONF_PORT)
        topic = self._config.get(CONF_TOPIC)

        self._client = mqtt.Client()
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
        """Gestisce i messaggi MQTT in arrivo ed estrae le coordinate."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
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
        if self._client:
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
