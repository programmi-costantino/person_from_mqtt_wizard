import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN, CONF_BROKER, CONF_PORT, CONF_TOPIC, 
    CONF_LAT_KEY, CONF_LON_KEY, DEFAULT_PORT, 
    DEFAULT_LAT_KEY, DEFAULT_LON_KEY
)

class PersonMQTTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gestisce il setup iniziale."""
        if user_input is not None:
            return self.async_create_entry(title=f"MQTT Tracker ({user_input[CONF_BROKER]})", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_BROKER): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_TOPIC): str,
            vol.Optional(CONF_LAT_KEY, default=DEFAULT_LAT_KEY): str,
            vol.Optional(CONF_LON_KEY, default=DEFAULT_LON_KEY): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PersonMQTTOptionsFlowHandler(config_entry)


class PersonMQTTOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gestisce le opzioni modificabili dopo la configurazione."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Pre-popola il form con le opzioni salvate o i dati iniziali
        options = self.config_entry.options
        data = self.config_entry.data

        schema = vol.Schema({
            vol.Required(CONF_BROKER, default=options.get(CONF_BROKER, data.get(CONF_BROKER))): str,
            vol.Required(CONF_PORT, default=options.get(CONF_PORT, data.get(CONF_PORT))): int,
            vol.Required(CONF_TOPIC, default=options.get(CONF_TOPIC, data.get(CONF_TOPIC))): str,
            vol.Required(CONF_LAT_KEY, default=options.get(CONF_LAT_KEY, data.get(CONF_LAT_KEY))): str,
            vol.Required(CONF_LON_KEY, default=options.get(CONF_LON_KEY, data.get(CONF_LON_KEY))): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
