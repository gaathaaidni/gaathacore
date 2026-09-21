# Placeholder for translations
translations = {
    "en": {
        "menu": "Menu",
        "orders": "Orders",
        "dashboard": "Dashboard"
    },
    "ro": {
        "menu": "Meniu",
        "orders": "Comenzi",
        "dashboard": "Tablou de bord"
    }
}

def t(key, lang="en"):
    return translations.get(lang, {}).get(key, key)
