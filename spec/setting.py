specs = [
    {
        "spec_id": "smst-app",
        "display_name": "SMST Application",
        "description": "blabla",
        "container": {
            "image": "smst_app:1.1b0",
            "port": 3838,
            "network": "local-net",
            "internal": True
        }
    },
    {
        "spec_id": "smst-app-2",
        "display_name": "SMST Application 2",
        "description": "blabla",
        "container": {
            "image": "smst_app:1.1b0",
            "port": 3838,
            "env": {
                "PREVIEW": 1
            }
        }
    }
]
