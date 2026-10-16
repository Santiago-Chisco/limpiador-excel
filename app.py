"""Limpiador de Excel - interfaz visual con Streamlit.

Ejecutar:  streamlit run app.py
"""
import hmac
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

import cleaner

st.set_page_config(page_title="Limpiador de Excel", page_icon="🧹", layout="wide")


def require_login() -> None:
    """Pide usuario y contraseña si APP_PASSWORD está definida (uso en la nube)."""
    password = os.environ.get("APP_PASSWORD")
    if not password:
        return  # sin contraseña configurada (uso local): no pide login
    user = os.environ.get("APP_USER", "admin")
    if st.session_state.get("autenticado"):
        return
    st.title("🔒 Limpiador de Excel")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        ok = st.form_submit_button("Entrar")
    if ok:
        if hmac.compare_digest(u, user) and hmac.compare_digest(p, password):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()


require_login()
st.title("🧹 Limpiador de Excel")
st.caption("Sube tu archivo, elimina filas vacías y duplicados, y descarga el resultado limpio.")

# ------------------------------------------------------------ opciones
with st.sidebar:
    st.header("⚙️ Opciones de limpieza")
    strip_text = st.checkbox("Quitar espacios sobrantes en textos", value=True)
    drop_empty_rows = st.checkbox("Eliminar filas vacías", value=True)
    drop_empty_cols = st.checkbox("Eliminar columnas vacías", value=True)
    drop_duplicates = st.checkbox("Eliminar duplicados", value=True)
    keep = st.radio(
        "Al haber duplicados conservar",
        options=["first", "last"],
        format_func=lambda x: "La primera aparición" if x == "first" else "La última aparición",
        disabled=not drop_duplicates,
    )
    include_removed = st.checkbox(
        "Incluir hojas con los duplicados eliminados", value=False, disabled=not drop_duplicates
    )

tab_clean, tab_damaged = st.tabs(["📂 Limpiar archivo", "⚠️ Excel dañados"])

# ------------------------------------------------------------ pestaña limpiar
with tab_clean:
    uploaded = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xlsm", "xls", "csv"])

    if uploaded is not None:
        file_bytes = uploaded.getvalue()

        try:
            sheets = cleaner.read_workbook(file_bytes, uploaded.name)
        except cleaner.DamagedFileError as exc:
            saved = cleaner.save_damaged(file_bytes, uploaded.name, str(exc))
            st.error(f"❌ El archivo **{uploaded.name}** está dañado y no se puede procesar.")
            st.caption(f"Motivo: {exc}")
            st.warning(f"Se guardó automáticamente en la carpeta `{saved.parent}/` ({saved.name}).")
        else:
            st.success(f"✅ Archivo leído correctamente: {len(sheets)} hoja(s).")

            result_bytes, summary = cleaner.clean_workbook(
                sheets,
                include_removed=include_removed,
                strip_text=strip_text,
                drop_empty_rows=drop_empty_rows,
                drop_empty_cols=drop_empty_cols,
                drop_duplicates=drop_duplicates,
                keep=keep,
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Filas vacías eliminadas", int(summary["filas_vacias_eliminadas"].sum()))
            c2.metric("Duplicados eliminados", int(summary["duplicados_eliminados"].sum()))
            c3.metric("Filas finales", int(summary["filas_finales"].sum()))

            st.subheader("Resumen por hoja")
            st.dataframe(summary, use_container_width=True, hide_index=True)

            st.subheader("Vista previa (archivo limpio)")
            import io

            import pandas as pd

            cleaned_sheets = pd.read_excel(io.BytesIO(result_bytes), sheet_name=None)
            sheet_names = [n for n in cleaned_sheets if not n.startswith("Dup_")]
            chosen = st.selectbox("Hoja", sheet_names)
            st.dataframe(cleaned_sheets[chosen].head(200), use_container_width=True)

            stem = Path(uploaded.name).stem
            st.download_button(
                "⬇️ Descargar Excel limpio",
                data=result_bytes,
                file_name=f"{stem}_limpio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

            st.divider()
            st.caption("¿El archivo se abrió pero está corrupto o incorrecto? Guárdalo manualmente:")
            if st.button("🗂️ Marcar como dañado y guardar"):
                saved = cleaner.save_damaged(file_bytes, uploaded.name, "Marcado manualmente por el usuario")
                st.info(f"Guardado en `{saved.parent}/{saved.name}`")

# ------------------------------------------------------------ pestaña dañados
with tab_damaged:
    st.subheader("Archivos dañados guardados")
    st.caption(f"Se guardan en la carpeta `{cleaner.DAMAGED_DIR}/` junto a un registro con el motivo.")

    items = cleaner.list_damaged()
    if not items:
        st.info("Aún no hay archivos dañados guardados.")
    else:
        for i, item in enumerate(items):
            col_info, col_dl, col_del = st.columns([6, 2, 1])
            col_info.markdown(
                f"**{item['nombre']}**  \n{item['fecha']} · {item['tamano_kb']} KB"
                + (f"  \n_Motivo: {item['motivo']}_" if item["motivo"] else "")
            )
            col_dl.download_button(
                "⬇️ Descargar",
                data=item["ruta"].read_bytes(),
                file_name=item["nombre"],
                key=f"dl_{i}",
            )
            if col_del.button("🗑️", key=f"del_{i}", help="Eliminar este archivo"):
                cleaner.delete_damaged(item["ruta"])
                st.rerun()
            st.divider()

st.sidebar.caption(f"Actualizado: {datetime.now():%Y-%m-%d %H:%M}")
