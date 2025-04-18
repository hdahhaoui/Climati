# acsim/gpt_commentary.py
import os
import streamlit as st
from openai import OpenAI

# ▶︎ 1. Initialiser le client
client = OpenAI(
    api_key = st.secrets.get("openai_api_key", os.getenv("OPENAI_API_KEY")),
    # DeepSeek utilise une URL OpenAI‑compatible :
    base_url = st.secrets.get("openai_base_url", "https://api.deepseek.com/v1")
    # si tu parles directement à OpenAI, tu peux omettre base_url
)

def commenter_resultats(temp_ext, temp_int_base, conso_base,
                        temp_int_opt, conso_opt, temp_consigne):

    total_base = sum(conso_base)
    total_opt  = sum(conso_opt)
    gain_pct   = ((total_base - total_opt) / total_base * 100) if total_base else 0

    resume = (
        f"Température de consigne : {temp_consigne} °C. "
        f"Conso 24 h baseline : {total_base:.2f} kWh. "
        f"Conso 24 h optimisée : {total_opt:.2f} kWh (‑{gain_pct:.1f} %). "
        f"T° int. baseline min/max : {min(temp_int_base):.1f}/{max(temp_int_base):.1f} °C. "
        f"T° int. optimisée min/max : {min(temp_int_opt):.1f}/{max(temp_int_opt):.1f} °C."
    )

    prompt = (
        "Tu es un expert en efficacité énergétique. "
        "Explique en ≤ 120 mots pourquoi le scénario optimisé consomme moins, "
        "en évaluant l’impact sur le confort. "
        + resume
    )

    try:
        # ▶︎ 2. Nouvelle syntaxe SDK 1.x
        response = client.chat.completions.create(
            model = "deepseek-chat",          # ou gpt-4o, gpt-3.5‑turbo, etc.
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Erreur de génération IA : {e}"
