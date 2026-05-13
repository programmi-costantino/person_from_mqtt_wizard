from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

PLATFORMS = ["device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup dell'integrazione da una config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Salva le configurazioni (unendo dati iniziali e opzioni modificate)
    config = {**entry.data, **entry.options}
    hass.data[DOMAIN][entry.entry_id] = config

    # Registra un listener per ricaricare l'integrazione se le opzioni cambiano
    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload di una config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Ricarica l'integrazione quando le opzioni cambiano."""
    await hass.config_entries.async_reload(entry.entry_id)
