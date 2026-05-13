from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = ["device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura l'integrazione all'avvio o alla creazione tramite UI."""
    hass.data.setdefault(DOMAIN, {})
    
    # Uniamo i dati iniziali con le eventuali opzioni modificate dall'utente
    config_data = dict(entry.data)
    if entry.options:
        config_data.update(entry.options)
        
    hass.data[DOMAIN][entry.entry_id] = config_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Registra un listener per ricaricare se l'utente cambia le Opzioni
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuove l'integrazione."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Ricarica l'integrazione se vengono modificate le impostazioni."""
    await hass.config_entries.async_reload(entry.entry_id)