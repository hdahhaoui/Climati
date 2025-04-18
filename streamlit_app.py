import streamlit as st
import pandas as pd
from acsim import simulation, optimization, gpt_commentary

st.set_page_config(page_title="Simulation Énergétique Climatisation", layout="centered")

st.title("🔆 Outil de simulation énergétique d'un climatiseur")

# --- Entrée des paramètres par l'utilisateur ---
st.sidebar.header("Paramètres de la pièce et du climatiseur")
surface = st.sidebar.number_input("Surface de la pièce (m²)", min_value=5.0, max_value=500.0, value=20.0)
hauteur = st.sidebar.number_input("Hauteur sous plafond (m)", min_value=2.0, max_value=5.0, value=2.5)
isolation = st.sidebar.selectbox("Niveau d'isolation", options=["mauvaise", "moyenne", "bonne"], index=1)
temp_consigne = st.sidebar.number_input("Température de consigne (°C)", min_value=16.0, max_value=30.0, value=24.0)
type_clim = st.sidebar.selectbox("Type de climatiseur", options=["Standard", "Ancien", "Haute efficacité"], index=0)
optimiser = st.sidebar.checkbox("Activer l'optimisation intelligente", value=True)

st.sidebar.markdown("Réglez les paramètres puis lancez la simulation.")

# --- Lancement de la simulation à la demande ---
if st.sidebar.button("Lancer la simulation"):
    # Simulation baseline (sans optimisation)
    outside_t, inside_base, cons_base = simulation.simuler_jour(surface, hauteur, isolation, temp_consigne, type_clim)
    # Simulation optimisée (avec stratégie d'utilisation optimale)
    if optimiser:
        outside_t, inside_opt, cons_opt = optimization.simuler_jour_optimise(surface, hauteur, isolation, temp_consigne, type_clim)
    else:
        # Si pas d'optimisation, l'optimisé est identique au baseline
        inside_opt = inside_base.copy()
        cons_opt = cons_base.copy()

    # Préparation des données pour graphiques
    heures = list(range(len(outside_t)))
    # Créer DataFrame pour températures
    df_temp = pd.DataFrame({
        "Heure": heures,
        "Température extérieure (°C)": outside_t,
        "Température intérieure - Baseline (°C)": inside_base,
        "Température intérieure - Optimisée (°C)": inside_opt
    }).set_index("Heure")
    # Créer DataFrame pour consommations (convertir J en kWh pour chaque heure)
    # cons_base et cons_opt sont en Joules par heure
    cons_base_kWh = [q / 3_600_000 for q in cons_base]
    cons_opt_kWh = [q / 3_600_000 for q in cons_opt]
    df_conso = pd.DataFrame({
        "Heure": heures,
        "Consommation électrique - Baseline (kWh)": cons_base_kWh,
        "Consommation électrique - Optimisée (kWh)": cons_opt_kWh
    }).set_index("Heure")

    # Affichage des graphiques comparatifs
    st.subheader("Températures intérieure vs extérieure")
    st.line_chart(df_temp)

    st.subheader("Consommation horaire du climatiseur")
    st.line_chart(df_conso)

    # Affichage des bilans
    total_base = sum(cons_base_kWh)
    total_opt = sum(cons_opt_kWh)
    econ = (total_base - total_opt) / total_base * 100 if total_base > 0 else 0.0
    st.markdown(f"**Consommation totale sur 24h - Baseline :** {total_base:.2f} kWh")
    st.markdown(f"**Consommation totale sur 24h - Optimisée :** {total_opt:.2f} kWh")
    st.markdown(f"**Économie d'énergie réalisée :** {econ:.1f} %")

    # Génération du commentaire par IA (si clé API fournie)
    if "openai_api_key" in st.secrets:
        commentaire = gpt_commentary.commenter_resultats(outside_t, inside_base, cons_base_kWh, inside_opt, cons_opt_kWh, temp_consigne)
        st.subheader("Commentaire intelligent sur les résultats")
        st.write(commentaire)
    else:
        st.info("Ajoutez une clé API OpenAI dans les secrets Streamlit pour obtenir un commentaire IA sur les résultats.")
