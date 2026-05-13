"""Test the MqttPersonTracker entity."""
import json
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.person_from_mqtt_wizard.const import (
    CONF_IS_REMOTE_BROKER,
    CONF_LAT_KEY,
    CONF_LON_KEY,
    CONF_NAME,
    CONF_TOPIC,
    DOMAIN,
)


async def test_entity_ha_broker(hass: HomeAssistant, mqtt_mock) -> None:
    """Test entity creation and state update with HA broker."""
    config = {
        CONF_NAME: "Test HA Tracker",
        CONF_TOPIC: "test/location",
        CONF_IS_REMOTE_BROKER: False,
        CONF_LAT_KEY: "lat",
        CONF_LON_KEY: "lon",
    }

    # Create a config entry
    config_entry = hass.config_entries.async_create_entry(
        DOMAIN, data=config, title="Test HA Tracker"
    )
    config_entry.add_to_hass(hass)

    # Setup the integration
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check if the entity is created
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get("device_tracker.test_ha_tracker")
    assert entry is not None

    # Check initial state
    state = hass.states.get("device_tracker.test_ha_tracker")
    assert state.state == "unknown"

    # Simulate an MQTT message
    payload = json.dumps({"lat": 41.9, "lon": 12.5})
    hass.helpers.mqtt.async_fire_mqtt_message(hass, "test/location", payload)
    await hass.async_block_till_done()

    # Check updated state
    state = hass.states.get("device_tracker.test_ha_tracker")
    assert state.attributes.get("latitude") == 41.9
    assert state.attributes.get("longitude") == 12.5


async def test_entity_remote_broker(hass: HomeAssistant) -> None:
    """Test entity creation with a remote broker."""
    config = {
        CONF_NAME: "Test Remote Tracker",
        CONF_TOPIC: "test/location",
        CONF_IS_REMOTE_BROKER: True,
        CONF_LAT_KEY: "lat",
        CONF_LON_KEY: "lon",
        "broker": "1.2.3.4",
        "port": 1883,
    }

    config_entry = hass.config_entries.async_create_entry(
        DOMAIN, data=config, title="Test Remote Tracker"
    )
    config_entry.add_to_hass(hass)

    with patch("paho.mqtt.client.Client") as mock_client:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert mock_client.return_value.connect.called