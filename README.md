# 🧹 Limpiador de Excel

Aplicación visual en Python (Streamlit) para limpiar archivos Excel.

## Qué hace
- Sube archivos `.xlsx`, `.xlsm`, `.xls` o `.csv`.
- Elimina **filas y columnas vacías** (incluye celdas con solo espacios).
- Elimina **filas duplicadas** (conserva la primera o la última).
- Procesa **todas las hojas** del libro.
- Descarga el resultado como `nombre_limpio.xlsx`.
- Si el archivo está **dañado**, se guarda automáticamente en `excel_danados/` con el motivo.
  También hay un botón para marcar manualmente un archivo como dañado.
- La pestaña **⚠️ Excel dañados** permite ver, descargar o eliminar esos archivos.

## Instalación y uso (VS Code / terminal)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
streamlit run app.py
```
Se abrirá en el navegador en http://localhost:8501

## Estructura
- `app.py` – interfaz visual
- `cleaner.py` – lógica de limpieza y gestión de dañados
- `excel_danados/` – se crea sola al guardar el primer archivo dañado
