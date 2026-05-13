"""Test the Person from MQTT Wizard config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, setup
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.person_from_mqtt_wizard.const import (
    CONF_BROKER,
    CONF_IS_REMOTE_BROKER,
    CONF_LAT_KEY,
    CONF_LON_KEY,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TOPIC,
    CONF_USERNAME,
    DOMAIN,
)


async def test_form_ha_broker(hass: HomeAssistant) -> None:
    """Test we get the form and can create an entry with HA broker."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # Step 1: User input (using HA broker)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Test Tracker",
            CONF_TOPIC: "test/location",
            CONF_IS_REMOTE_BROKER: False,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "keys"

    # Step 2: Keys input
    with patch(
        "custom_components.person_from_mqtt_wizard.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_LAT_KEY: "latitude", CONF_LON_KEY: "longitude"},
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Test Tracker"
    assert result3["data"] == {
        CONF_NAME: "Test Tracker",
        CONF_TOPIC: "test/location",
        CONF_IS_REMOTE_BROKER: False,
        CONF_LAT_KEY: "latitude",
        CONF_LON_KEY: "longitude",
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize("connection_works", [True, False])
async def test_form_remote_broker(hass: HomeAssistant, connection_works: bool) -> None:
    """Test the flow for a remote broker with success and failure."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Step 1: User input (selecting remote broker)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Remote Tracker",
            CONF_TOPIC: "remote/location",
            CONF_IS_REMOTE_BROKER: True,
        },
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "remote"

    # Step 2: Remote broker credentials
    with patch(
        "custom_components.person_from_mqtt_wizard.config_flow.test_mqtt_connection",
        return_value=connection_works,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_BROKER: "1.2.3.4",
                CONF_PORT: 1883,
                CONF_USERNAME: "user",
                CONF_PASSWORD: "pwd",
            },
        )
        await hass.async_block_till_done()

    if not connection_works:
        assert result3["type"] == FlowResultType.FORM
        assert result3["step_id"] == "remote"
        assert result3["errors"] == {"base": "cannot_connect"}
        return

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "keys"

    # Step 3: Keys input
    with patch(
        "custom_components.person_from_mqtt_wizard.async_setup_entry",
        return_value=True,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_LAT_KEY: "lat", CONF_LON_KEY: "lon"},
        )
        await hass.async_block_till_done()

    assert result4["type"] == FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Remote Tracker"
    assert result4["data"][CONF_BROKER] == "1.2.3.4"


async def test_options_flow(hass: HomeAssistant, config_entry) -> None:
    """Test the options flow."""
    # Load the integration
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Open options flow
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Change options
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_TOPIC: "new/topic", CONF_LAT_KEY: "new_lat"},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_TOPIC] == "new/topic"
    assert config_entry.options[CONF_LAT_KEY] == "new_lat"