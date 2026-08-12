"""
Générateur de grille 100x100 réaliste pour le modèle Wildfire (murf85)
=======================================================================
Paramètres inspirés de map_1.json :
  - fuelModelNumber : type de végétation (modèle BehavePlus)
  - windDirection   : direction du vent (degrés)
  - windSpeed       : vitesse du vent (km/h)
  - elevation       : altitude (m) — varie progressivement (pas aléatoire)
  - ignited         : cellule en feu au départ
  - coordonnées UTM zone 18N (Ottawa/Gatineau)

LANCEMENT :
    python generate_map_100x100.py
Résultat : map_100x100.json (à placer dans ~/wildfire/config/)
"""

import json
import math
import random

# ============================================================
# PARAMETRES GLOBAUX (identiques à map_1.json)
# ============================================================
WIND_DIRECTION = 270        # vent d'ouest (270°) → pousse le feu vers l'est
WIND_SPEED     = 15         # km/h — vent modéré
CELL_SIZE      = 30         # mètres par cellule (résolution standard)
GRID_SIZE      = 100        # 100 x 100 cellules

# Coordonnées UTM 18N du coin bas-gauche (région Ottawa/Gatineau générique)
X_ORIGIN = 470000.0
Y_ORIGIN = 5098000.0

# Foyer initial : 3 cellules au centre-haut de la grille
IGNITION_CELLS = [(50, 75), (51, 75), (50, 76)]

# ============================================================
# MODÈLES DE COMBUSTIBLE (BehavePlus fuel models)
# ============================================================
# Ces codes correspondent aux types de végétation réels :
#   1  = herbes courtes et champ cultivé
#   2  = herbes et broussailles
#   5  = broussailles jeunes
#   8  = forêt de feuillus dense (fermée) — dominant dans Gatineau
#   9  = forêt de feuillus (litière dense)
#   10 = forêt de conifères (épinettes, pins)
#   91 = eau / plan d'eau (incombustible)
#   98 = roche / terrain nu (incombustible)
FUEL_FORET_FEUILLUS   = 8    # forêt principale
FUEL_FORET_CONIFERES  = 10   # zones plus élevées
FUEL_BROUSSAILLES     = 5    # lisière de forêt
FUEL_HERBES           = 2    # clairières
FUEL_EAU              = 91   # rivière / lac
FUEL_ROCHE            = 98   # sommet rocheux

# ============================================================
# GÉNÉRATION DU TERRAIN (élévation réaliste)
# ============================================================
def generer_elevation(rows, cols):
    """
    Génère un terrain réaliste avec :
    - Une colline principale au centre-nord
    - Une vallée (rivière) au sud-ouest
    - Des variations douces (pas de sauts brusques)
    
    Méthode : somme de plusieurs fonctions gaussiennes (collines)
    + bruit de Perlin simplifié pour les micro-variations
    """
    elev = [[0.0] * cols for _ in range(rows)]

    # --- Collines principales ---
    collines = [
        # (centre_x, centre_y, amplitude, largeur)
        (50, 70, 120.0, 25),    # colline principale au centre-nord
        (75, 80,  80.0, 20),    # colline secondaire nord-est
        (25, 75,  60.0, 18),    # colline nord-ouest
        (60, 40,  40.0, 15),    # petite élévation centre
        (30, 30,  30.0, 12),    # légère bosse sud-ouest
    ]

    # --- Vallée (rivière) : dépression diagonale sud-ouest → centre ---
    def vallee(x, y):
        # Axe de la vallée : ligne de (0,0) à (40,30)
        ax, ay = 40, 30
        # Distance perpendiculaire à cet axe
        longueur = math.sqrt(ax**2 + ay**2)
        dist = abs(ay * x - ax * y) / longueur
        # Dépression de -30m sur 10 cellules de large
        return -30.0 * max(0, 1 - (dist / 10.0) ** 2)

    for row in range(rows):
        for col in range(cols):
            z = 200.0  # altitude de base (200m)

            # Ajouter les collines (gaussiennes)
            for cx, cy, amp, largeur in collines:
                dist2 = (col - cx)**2 + (row - cy)**2
                z += amp * math.exp(-dist2 / (2 * largeur**2))

            # Ajouter la vallée
            z += vallee(col, row)

            # Légère pente générale nord → sud (-0.5m par cellule)
            z -= (rows - row) * 0.5

            # Micro-variations (bruit simple pseudo-aléatoire mais lisse)
            # On utilise sin/cos pour un bruit déterministe (reproductible)
            bruit = (
                3.0 * math.sin(col * 0.3) * math.cos(row * 0.2) +
                2.0 * math.sin(col * 0.7 + row * 0.5) +
                1.0 * math.cos(col * 1.1 - row * 0.8)
            )
            z += bruit

            elev[row][col] = round(max(50.0, z), 2)

    return elev


# ============================================================
# GÉNÉRATION DU TYPE DE COMBUSTIBLE (basé sur élévation + position)
# ============================================================
def choisir_fuel(row, col, elevation, elev_min, elev_max):
    """
    Règle réaliste de végétation selon l'altitude et la position :
    - Zones basses (<120m) près de la vallée → eau / herbes
    - Zones moyennes (120-250m) → forêt feuillus (dominant)
    - Zones hautes (>250m) → forêt conifères + roche au sommet
    - Lisières (bord de grille) → broussailles
    """
    # Vallée (zone basse, sud-ouest) → eau ou herbes
    ax, ay = 40, 30
    longueur = math.sqrt(ax**2 + ay**2)
    dist_vallee = abs(ay * col - ax * row) / longueur

    if dist_vallee < 5 and elevation < 180:
        return FUEL_EAU          # rivière

    if dist_vallee < 10 and elevation < 200:
        return FUEL_HERBES        # berges / prairies

    # Sommet rocheux
    if elevation > 320:
        return FUEL_ROCHE

    # Zones élevées → conifères
    if elevation > 270:
        return FUEL_FORET_CONIFERES

    # Lisières de grille → broussailles
    if row < 5 or row > 94 or col < 5 or col > 94:
        return FUEL_BROUSSAILLES

    # Clairières (zones plates à basse altitude)
    if elevation < 220 and (row % 15 < 2 or col % 18 < 2):
        return FUEL_HERBES

    # Par défaut : forêt feuillus (Gatineau)
    return FUEL_FORET_FEUILLUS


# ============================================================
# GÉNÉRATION DE LA GRILLE COMPLÈTE
# ============================================================
def generer_grille():
    print("Génération du terrain 100x100...")
    elev = generer_elevation(GRID_SIZE, GRID_SIZE)

    # Calcul min/max pour la normalisation du fuel
    toutes_elevations = [elev[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    elev_min = min(toutes_elevations)
    elev_max = max(toutes_elevations)
    print(f"Élévation : min={elev_min:.1f}m, max={elev_max:.1f}m")

    # Vérification : différence max entre cellules voisines
    diff_max = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if col + 1 < GRID_SIZE:
                diff = abs(elev[row][col] - elev[row][col+1])
                diff_max = max(diff_max, diff)
            if row + 1 < GRID_SIZE:
                diff = abs(elev[row][col] - elev[row+1][col])
                diff_max = max(diff_max, diff)
    print(f"Différence max entre cellules voisines : {diff_max:.2f}m")

    # Construction des cellules
    cellules = []
    nb_ignitions = 0
    nb_eau = 0
    nb_foret = 0

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = X_ORIGIN + col * CELL_SIZE
            y = Y_ORIGIN + row * CELL_SIZE
            z = elev[row][col]
            fuel = choisir_fuel(row, col, z, elev_min, elev_max)
            ignited = (col, row) in IGNITION_CELLS

            # Compter les statistiques
            if ignited:
                nb_ignitions += 1
            if fuel == FUEL_EAU:
                nb_eau += 1
            if fuel in (FUEL_FORET_FEUILLUS, FUEL_FORET_CONIFERES):
                nb_foret += 1

            cellule = {
                "state": {
                    "fuelModelNumber": fuel,
                    "windDirection":   WIND_DIRECTION,
                    "windSpeed":       WIND_SPEED,
                    "x":               round(x, 1),
                    "y":               round(y, 1),
                    "elevation":       z,
                    "ignited":         ignited
                }
            }
            cellules.append(cellule)

    print(f"Cellules générées : {len(cellules)}")
    print(f"  Forêt         : {nb_foret} cellules ({nb_foret/100:.1f}%)")
    print(f"  Eau/rivière   : {nb_eau} cellules")
    print(f"  Foyers initiaux : {nb_ignitions} cellules")

    return cellules


# ============================================================
# STRUCTURE JSON FINALE (format map_1.json)
# ============================================================
def generer_json(cellules):
    return {
        "grid": {
            "width":     GRID_SIZE,
            "height":    GRID_SIZE,
            "cell_size": CELL_SIZE
        },
        "simulation": {
            "wind_direction": WIND_DIRECTION,
            "wind_speed":     WIND_SPEED,
            "description":    "Grille 100x100 - Forêt générique avec relief (Ottawa region)"
        },
        "cells": cellules
    }


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    random.seed(42)  # reproductible

    cellules = generer_grille()
    data = generer_json(cellules)

    # Sauvegarder le JSON
    nom_fichier = "map_100x100.json"
    with open(nom_fichier, 'w') as f:
        json.dump(data, f, indent=2)

    taille = len(json.dumps(data)) / 1024
    print(f"\nFichier généré : {nom_fichier} ({taille:.0f} Ko)")
    print(f"Copie sur le serveur : scp {nom_fichier} momo@devssim.carleton.ca:~/wildfire/config/")
    print(f"\nLancement : ./bin/wildfire config/map_100x100.json output_100x100.csv \"2025-04-28 10:30:00\"")
