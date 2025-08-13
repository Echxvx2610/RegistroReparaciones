from app import app, db
from config import Config
import webbrowser

# Cargar configuración
app.config.from_object(Config)

# implementacion de base de datos pendiente
# iinicializar la base de datos
# db.init_app(app)

# Crear las tablas si no existen
# with app.app_context():
#     db.create_all()

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000/")
    app.run()
