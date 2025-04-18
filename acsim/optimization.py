import math
from acsim import simulation

def simuler_jour_optimise(surface, hauteur, isolation, temp_consigne, type_clim):
    """
    Simule heure par heure sur 24h en optimisant l'usage du climatiseur pour réduire la consommation.
    On permet un léger sur-refroidissement anticipé (jusqu'à 2°C en dessous de la consigne) 
    pour profiter des heures plus favorables (température extérieure plus basse, COP plus élevé).
    Retourne les listes: temp_ext (°C), temp_int_opt (°C) et conso_opt (J par heure).
    """
    # On récupère le profil extérieur (même hypothèse que la simulation de base)
    temp_ext_profile = simulation.profil_temperature_exterieure(n_jours=1)
    UA, C = simulation.param_thermiques(surface, hauteur, isolation)
    R = 1.0 / UA if UA > 0 else float('inf')
    # États discrets possibles pour l'écart de température intérieure par rapport à la consigne (sur-refroidissement)
    # X = consigne - T_int. X=0 correspond à pile la consigne, X=2 correspond à T_int = consigne - 2°C (plus froid)
    X_values = [0.0, 0.5, 1.0, 1.5, 2.0]
    n_heures = len(temp_ext_profile)
    n_etats = len(X_values)
    # Tables pour programmation dynamique
    cout = [[math.inf] * n_etats for _ in range(n_heures + 1)]
    precedent = [[None] * n_etats for _ in range(n_heures + 1)]
    action = [[None] * n_etats for _ in range(n_heures)]
    # État initial (début 0h) : on part à la consigne (écart 0)
    idx_X0 = X_values.index(0.0)
    cout[0][idx_X0] = 0.0

    # Phase de calcul DP
    for h in range(n_heures):
        T_ext = temp_ext_profile[h]
        COP = simulation.cop_climatiseur(type_clim, T_ext)
        for j, X in enumerate(X_values):
            if cout[h][j] == math.inf:
                continue
            # Température intérieure réelle en début d'heure h
            T_int_debut = temp_consigne - X
            # Évolution sans clim sur 1h
            T_no_clim_fin = T_ext + (T_int_debut - T_ext) * math.exp(-3600.0 / (R * C))
            # Cas 1 : On n'utilise le climatiseur qu'en cas de dépassement (stratégie "baseline/clamp")
            # Température intérieure en fin d'heure si on se contente de maintenir la consigne max
            if T_no_clim_fin > temp_consigne:
                T_fin_1 = temp_consigne
            else:
                T_fin_1 = T_no_clim_fin
            # Vérification du confort minimum (on n'autorise pas de descendre sous consigne-2°C)
            if T_fin_1 < temp_consigne - 2.0:
                T_fin_1 = temp_consigne - 2.0
            X_fin_1 = temp_consigne - T_fin_1
            # Index de l'état discret final le plus proche
            j_fin_1 = min(range(n_etats), key=lambda k: abs(X_values[k] - X_fin_1))
            # Énergie de refroidissement nécessaire (J) pour atteindre T_fin_1
            Q_refroidir = 0.0
            if T_no_clim_fin > T_fin_1:
                # Il a fallu extraire de la chaleur
                Q_refroidir = (T_no_clim_fin - T_fin_1) * C
            # Consommation électrique correspondante (J)
            energie_elec = Q_refroidir / COP
            # Mise à jour du coût
            if cout[h][j] + energie_elec < cout[h+1][j_fin_1]:
                cout[h+1][j_fin_1] = cout[h][j] + energie_elec
                precedent[h+1][j_fin_1] = j
                action[h][j_fin_1] = "clamp"

            # Cas 2 : On force un sur-refroidissement supplémentaire de 0.5°C (si possible)
            if T_fin_1 > temp_consigne - 2.0:
                # On cible 0.5°C de moins que T_fin_1 (sans descendre sous -2°C du setpoint)
                T_cible = max(T_fin_1 - 0.5, temp_consigne - 2.0)
                X_cible = temp_consigne - T_cible
                j_fin_2 = min(range(n_etats), key=lambda k: abs(X_values[k] - X_cible))
                # Energie totale à extraire pour atteindre T_cible
                Q_refroidir2 = Q_refroidir + (T_fin_1 - T_cible) * C
                energie_elec2 = Q_refroidir2 / COP
                if cout[h][j] + energie_elec2 < cout[h+1][j_fin_2]:
                    cout[h+1][j_fin_2] = cout[h][j] + energie_elec2
                    precedent[h+1][j_fin_2] = j
                    action[h][j_fin_2] = "surrefroid"

    # Recherche de l'état final optimal (après 24h)
    j_final = min(range(n_etats), key=lambda k: cout[n_heures][k])
    # Reconstruction du chemin optimal d'états X
    X_path = [None] * (n_heures + 1)
    X_path[n_heures] = X_values[j_final]
    j_courant = j_final
    for h in range(n_heures, 0, -1):
        j_prec = precedent[h][j_courant]
        X_path[h-1] = X_values[j_prec] if j_prec is not None else 0.0
        j_courant = j_prec

    # Simulation finale détaillée pour récupérer températures intérieures et conso réelle par heure
    temp_int_opt = []
    conso_opt = []
    T_int = temp_consigne - X_path[0]  # température initiale réelle
    for h in range(n_heures):
        T_ext = temp_ext_profile[h]
        # Température intérieure cible en fin d'heure (selon X_path calculé)
        T_cible_fin = temp_consigne - X_path[h+1]
        # Température sans clim sur l'heure
        T_no_clim_fin = T_ext + (T_int - T_ext) * math.exp(-3600.0 / (R * C))
        # Calcul de l'énergie à extraire réellement pour atteindre T_cible_fin
        if T_no_clim_fin > T_cible_fin:
            Q_extract = (T_no_clim_fin - T_cible_fin) * C
        else:
            Q_extract = 0.0
        # Met à jour la température intérieure en fin d'heure
        T_int = T_cible_fin if T_no_clim_fin > T_cible_fin else T_no_clim_fin
        temp_int_opt.append(round(T_int, 1))
        # Consommation électrique correspondante
        if Q_extract > 0:
            COP = simulation.cop_climatiseur(type_clim, T_ext)
            conso_opt.append(Q_extract / COP)
        else:
            conso_opt.append(0.0)
    return temp_ext_profile, temp_int_opt, conso_opt
