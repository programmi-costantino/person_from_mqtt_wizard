import voluptuous as vol
import paho.mqtt.client as paho_mqtt
from paho.mqtt.enums import CallbackAPIVersion
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_NAME, CONF_IS_REMOTE_BROKER, CONF_BROKER, CONF_PORT, 
    CONF_USERNAME, CONF_PASSWORD, CONF_TOPIC, CONF_LAT_KEY, CONF_LON_KEY, DEFAULT_PORT, 
    DEFAULT_LAT_KEY, DEFAULT_LON_KEY
)

def test_mqtt_connection(broker, port, user, pwd):
    """Validazione broker remoto (paho-mqtt 2.x)."""
    client = paho_mqtt.Client(CallbackAPIVersion.VERSION1) 
    if user:
        client.username_pw_set(user, pwd)
    try:
        client.connect(broker, port, keepalive=5)
        client.disconnect()
        return True
    except Exception:
        return False

class PersonMQTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.tracker_data = {}

    async def async_step_user(self, user_input=None):
        """Primo step: Nome, Topic e Scelta Broker."""
        if user_input is not None:
            self.tracker_data.update(user_input)
            if user_input.get(CONF_IS_REMOTE_BROKER):
                return await self.async_step_remote()
            return await self.async_step_keys()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="MQTT Person Tracker"): str,
                vol.Required(CONF_TOPIC): str,
                vol.Optional(CONF_IS_REMOTE_BROKER, default=False): bool,
            })
        )

    async def async_step_remote(self, user_input=None):
        """Secondo step (condizionale): Credenziali Remote."""
        errors = {}
        if user_input is not None:
            success = await self.hass.async_add_executor_job(
                test_mqtt_connection,
                user_input[CONF_BROKER],
                user_input.get(CONF_PORT, DEFAULT_PORT),
                user_input.get(CONF_USERNAME),
                user_input.get(CONF_PASSWORD)
            )
            if success:
                self.tracker_data.update(user_input)
                return await self.async_step_keys()
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="remote",
            data_schema=vol.Schema({
                vol.Required(CONF_BROKER): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
            }),
            errors=errors
        )

    async def async_step_keys(self, user_input=None):
        """Terzo step: Configurazione JSON Keys."""
        if user_input is not None:
            self.tracker_data.update(user_input)
            return self.async_create_entry(
                title=self.tracker_data[CONF_NAME], 
                data=self.tracker_data
            )

        return self.async_show_form(
            step_id="keys",
            data_schema=vol.Schema({
                vol.Required(CONF_LAT_KEY, default=DEFAULT_LAT_KEY): str,
                vol.Required(CONF_LON_KEY, default=DEFAULT_LON_KEY): str,
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PersonMQTTOptionsFlowHandler(config_entry)

class PersonMQTTOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options_data = {}

    async def async_step_init(self, user_input=None):
        current_config = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            self.options_data.update(user_input)
            if user_input.get(CONF_IS_REMOTE_BROKER):
                return await self.async_step_remote()
            return self.async_create_entry(title="", data=self.options_data)
        
        schema = {
            vol.Required(CONF_TOPIC, default=current_config.get(CONF_TOPIC)): str,
            vol.Required(CONF_LAT_KEY, default=current_config.get(CONF_LAT_KEY, DEFAULT_LAT_KEY)): str,
            vol.Required(CONF_LON_KEY, default=current_config.get(CONF_LON_KEY, DEFAULT_LON_KEY)): str,
            vol.Optional(CONF_IS_REMOTE_BROKER, default=current_config.get(CONF_IS_REMOTE_BROKER, False)): bool,
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))

    async def async_step_remote(self, user_input=None):
        errors = {}
        current_config = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            success = await self.hass.async_add_executor_job(
                test_mqtt_connection,
                user_input[CONF_BROKER],
                user_input.get(CONF_PORT, DEFAULT_PORT),
                user_input.get(CONF_USERNAME),
                user_input.get(CONF_PASSWORD)
            )
            if success:
                self.options_data.update(user_input)
                return self.async_create_entry(title="", data=self.options_data)
            errors["base"] = "cannot_connect"

        schema = {
            vol.Required(CONF_BROKER, default=current_config.get(CONF_BROKER, "")): str,
            vol.Required(CONF_PORT, default=current_config.get(CONF_PORT, DEFAULT_PORT)): int,
        }
        if current_config.get(CONF_USERNAME) is not None:
            schema[vol.Optional(CONF_USERNAME, default=current_config.get(CONF_USERNAME))] = str
        else:
            schema[vol.Optional(CONF_USERNAME)] = str
        
        if current_config.get(CONF_PASSWORD) is not None:
            schema[vol.Optional(CONF_PASSWORD, default=current_config.get(CONF_PASSWORD))] = str
        else:
            schema[vol.Optional(CONF_PASSWORD)] = str

        return self.async_show_form(step_id="remote", data_schema=vol.Schema(schema), errors=errors)
