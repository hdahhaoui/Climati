import openai

def commenter_resultats(temp_ext, temp_int_base, conso_base, temp_int_opt, conso_opt, temp_consigne):
    """
    Appelle l'API OpenAI pour générer un commentaire analysant les résultats de simulation.
    Retourne une chaîne de caractères en français.
    """
    # Préparation du message à envoyer à l'API
    total_base = sum(conso_base)
    total_opt = sum(conso_opt)
    gain_pct = 0.0
    if total_base > 0:
        gain_pct = (total_base - total_opt) / total_base * 100.0
    # Construire une synthèse des résultats en français pour le prompt
    resume = (
        f"Température de consigne: {temp_consigne} °C. "
        f"Consommation sur 24h (baseline): {total_base:.2f} kWh. "
        f"Consommation sur 24h (optimisée): {total_opt:.2f} kWh. "
        f"Économie réalisée: {gain_pct:.1f} %. "
        f"Températures intérieures baseline min/max: {min(temp_int_base):.1f}/{max(temp_int_base):.1f} °C. "
        f"Températures intérieures optimisées min/max: {min(temp_int_opt):.1f}/{max(temp_int_opt):.1f} °C."
    )
    prompt = (
        "Tu es un expert en énergie et en climatisation. Analyse les résultats de simulation suivants et commente les différences entre le scénario baseline et optimisé, en expliquant l'impact sur le confort et la consommation. "
        + resume
    )
    try:
        # Appel à l'API OpenAI (modèle GPT-3.5-turbo)
        reponse = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        commentaire = reponse.choices[0].message.content.strip()
    except Exception as e:
        commentaire = "Impossible de générer le commentaire automatique (erreur API)."
    return commentaire
