import math
import numpy as np

def profil_temperature_exterieure(n_jours=1, T_min=20.0, T_max=35.0):
    """
    Génère un profil horaire de température extérieure sur n_jours.
    On suppose une journée type avec T_min atteinte à 6h du matin et T_max à 14h-15h.
    Retourne une liste de températures horaire (longueur 24*n_jours).
    """
    profil_journalier = []
    # Définition de quelques points de repère (heures en UTC)
    temp_minuit = T_min + 0.2 * (T_max - T_min)   # un peu plus chaud qu'au minimum
    temp_6h = T_min
    temp_14h = T_max
    temp_23h = temp_minuit  # fin de journée revient proche de la valeur de minuit
    for h in range(24):
        if h < 6:
            # De 0h à 6h: décroît linéairement de temp_minuit à T_min
            T_ext = temp_minuit + (temp_6h - temp_minuit) * (h / 6.0)
        elif h <= 14:
            # De 6h à 14h: augmente linéairement de T_min à T_max
            T_ext = T_min + (T_max - T_min) * ((h - 6) / (14 - 6))
        else:
            # De 14h à 23h: redescend linéairement de T_max à temp_minuit
            T_ext = T_max + (temp_minuit - T_max) * ((h - 14) / (23 - 14))
        profil_journalier.append(round(T_ext, 1))
    return profil_journalier * n_jours

def param_thermiques(surface, hauteur, isolation):
    """
    Calcule les paramètres thermiques de la pièce:
    - UA : coefficient global de déperdition thermique (W/K)
    - C  : capacité thermique effective (J/K)
    """
    volume = surface * hauteur  # volume de la pièce en m3
    # Fixer le coefficient de transmission thermique U (W/m²K) selon l'isolation
    if isolation == "mauvaise":
        U = 3.0
    elif isolation == "bonne":
        U = 1.0
    else:  # "moyenne" par défaut
        U = 2.0
    # Surface d'enveloppe simplifiée (~surface au sol en m2)
    A = surface  
    UA = U * A  # coefficient global (approximation)
    # Capacité thermique (air + mobilier) : on prend l'air plus un facteur multiplicatif
    rho_air = 1.2   # kg/m3 (masse volumique de l'air)
    cp_air = 1005   # J/(kg·K) (capacité thermique massique de l'air)
    masse_air = rho_air * volume  # masse d'air dans la pièce
    C_air = masse_air * cp_air
    C_effectif = 5 * C_air  # facteur 5 pour représenter les masses thermiques (murs, mobilier)
    return UA, C_effectif

def cop_climatiseur(type_clim, T_ext):
    """
    Renvoie le COP (Coefficient de Performance) du climatiseur en fonction de son type et de la température extérieure.
    Modèle simple: COP nominal à 35°C, variation linéaire de ±0.1 par °C d'écart.
    Le COP ne descend pas en dessous de 1.
    """
    if type_clim == "Ancien":
        COP_nominal = 2.5
    elif type_clim == "Haute efficacité":
        COP_nominal = 4.0
    else:  # "Standard"
        COP_nominal = 3.0
    # Variation du COP en fonction de l'écart à 35°C (valeur nominale)
    COP = COP_nominal + 0.1 * (35.0 - T_ext)
    if COP < 1.0:
        COP = 1.0
    return COP

def simuler_jour(surface, hauteur, isolation, temp_consigne, type_clim):
    """
    Simule heure par heure sur 24h les températures intérieure et la consommation électrique
    du climatiseur pour maintenir la température de consigne.
    Retourne trois listes: temp_ext (°C), temp_int (°C) et conso (J par heure).
    """
    # Obtenir le profil extérieur sur 24h (on considère 1 jour)
    temp_ext_profile = profil_temperature_exterieure(n_jours=1)
    UA, C = param_thermiques(surface, hauteur, isolation)
    # Initialisation
    T_int = temp_consigne  # on démarre pile à la consigne
    temp_int_list = []
    conso_list = []
    # Simulation sur 24 heures (pas horaire)
    for h, T_ext in enumerate(temp_ext_profile):
        # 1. Évolution naturelle sans clim pendant 1h (équation différentielle linéarisée)
        # Formule : T_int_noClim = T_ext + (T_int - T_ext) * exp(-Δt/(R*C)), où R = 1/UA, Δt = 3600s
        if UA > 0:
            R = 1.0 / UA
        else:
            R = float('inf')
        # Calcul de la température intérieure après 1h sans clim
        T_int_noClim = T_ext + (T_int - T_ext) * math.exp(-3600.0 / (R * C))
        # 2. Activation du climatiseur si nécessaire pour ne pas dépasser la consigne
        if T_int_noClim > temp_consigne:
            # La pièce se réchaufferait au-delà de la consigne, on refroidit pendant l'heure
            # On ramène la température à la consigne en fin d'heure
            T_int = temp_consigne
            # Calcul de l’énergie à évacuer (en Joules) pour maintenir la consigne
            # ΔT = T_int_noClim - consigne => énergie = C * ΔT
            Q_extraire = (T_int_noClim - temp_consigne) * C
            if Q_extraire < 0:
                Q_extraire = 0
            # Consommation électrique (J) = Q_extraire / COP
            COP = cop_climatiseur(type_clim, T_ext)
            energie_elec = Q_extraire / COP
        else:
            # Pas de refroidissement nécessaire (température reste en dessous de la consigne)
            T_int = T_int_noClim
            Q_extraire = 0.0
            energie_elec = 0.0
        # Stockage des résultats de l'heure
        temp_int_list.append(round(T_int, 1))
        conso_list.append(energie_elec)
    return temp_ext_profile, temp_int_list, conso_list
