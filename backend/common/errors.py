import json

class ValidationError(Exception):
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class NotFoundError(Exception):
    def __init__(self, resource_type, resource_id):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = f"{resource_type} no encontrado: {resource_id}"
        super().__init__(self.message)

def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            from common.response import response
            return response(400, {"error": e.message, "field": e.field})
        except NotFoundError as e:
            from common.response import response
            return response(404, {"error": e.message})
        except Exception as e:
            import traceback
            traceback.print_exc()
            from common.response import response
            return response(500, {"error": str(e)})
    return wrapper

def validate_status_change(new_status, current_status):
    valid_statuses = ["pendiente", "en_proceso", "resuelto", "cerrado"]
    if new_status not in valid_statuses:
        raise ValidationError(f"Estado inválido: {new_status}")
    
    # Validaciones básicas de transición
    if current_status == "cerrado" and new_status != "cerrado":
        raise ValidationError("No se puede cambiar el estado de un incidente cerrado")

