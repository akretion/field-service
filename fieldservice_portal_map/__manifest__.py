{
    "name": "Field Service Portal Map Integration",
    "version": "18.0.1.1.0",
    "category": "Services/Field Service",
    "summary": "Ajoute un bouton de vue Carte basé sur la géolocalisation des fsm.location",
    "depends": ["fieldservice_portal", "web_leaflet_lib"],
    "data": [
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "fieldservice_portal_map/static/src/js/fsm_portal_map.js",
        ],
    },
    "license": "AGPL-3",
    "installable": True,
}
