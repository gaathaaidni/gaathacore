# Industry Rule Templates

Status: PARTIALLY IMPLEMENTED.

Templates are configuration-driven in `apps/api/src/templates/industry-rule-templates.json`. They define generic rule structures and required model capabilities. PPE, behavior, smoke/fire, and unattended-luggage templates are capability-gated and must not be presented as active detections unless a loaded model supports those classes.
