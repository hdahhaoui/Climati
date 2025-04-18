# acsim/gpt_commentary.py
import openai
import os

# 1) on cherche d'abord la clé dans st.secrets (Streamlit Cloud)...
try:
    import streamlit as st
    openai.api_key = st.secrets["openai_api_key"]
except Exception:
    # 2) ...sinon dans la variable d'environnement locale
    openai.api_key = os.getenv("OPENAI_API_KEY")

def commenter_resultats(temp_ext, temp_int_base, conso_base,
                        temp_int_opt, conso_opt, temp_consigne):
    total_base = sum(conso_base)
    total_opt = sum(conso_opt)
    gain_pct = ((total_base - total_opt) / total_base * 100.0) if total_base else 0.0

    resume = (
        f"Température de consigne : {temp_consigne} °C. "
        f"Conso 24 h baseline : {total_base:.2f} kWh. "
        f"Conso 24 h optimisée : {total_opt:.2f} kWh. "
        f"Économie : {gain_pct:.1f} %. "
        f"T° int. baseline min/max : {min(temp_int_base):.1f}/{max(temp_int_base):.1f} °C. "
        f"T° int. optimisée min/max : {min(temp_int_opt):.1f}/{max(temp_int_opt):.1f} °C."
    )
    prompt = (
        "Tu es un expert en efficacité énergétique. Explique, en ≤120 mots, pourquoi le "
        "scénario optimisé consomme moins, tout en commentant l'impact sur le confort. "
        + resume
    )

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200,
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur de génération IA : {e}"
