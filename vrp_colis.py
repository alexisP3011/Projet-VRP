import math
from functools import lru_cache
import random
from copy import deepcopy

random.seed(5)


from villes_de_france import villes_poids_colis

# villes_france = villes_poids_colis()

def formater_cycle(route, villes):
    """
    Formate une route en un dictionnaire avec les coordonnees au format demande
    """
    cycle = {}
    for ville in route:
        coords = villes[ville]
        cycle[ville] = (coords["longitude"], coords["latitude"], coords["poids_colis"])
    return cycle

def afficher_solution_formatee(routes, villes):
    """
    Formate les routes en trois cycles distincts et retourne les dictionnaires correspondants
    
    Args:
        routes: Liste des routes à formater
        villes: Dictionnaire des coordonnées des villes
        
    Returns:
        tuple: Trois dictionnaires représentant les cycles (cycle1, cycle2, cycle3)
    """
    cycles = []
    
    # Création des cycles
    for route in routes:
        cycle = formater_cycle(route, villes)
        cycles.append(cycle)
    
    # S'assurer qu'il y a exactement 3 cycles
    while len(cycles) < 3:
        cycles.append({})  # Ajouter des dictionnaires vides si nécessaire
    
    # Retourner les trois premiers cycles
    return cycles[0], cycles[1], cycles[2]

def formater_cycle(route, villes):
    """
    Formate une route en dictionnaire
    
    Args:
        route: Liste des villes formant une route
        villes: Dictionnaire des coordonnées des villes
        
    Returns:
        dict: Dictionnaire avec les villes et leurs coordonnées
    """
    cycle = {}
    for ville in route:
        cycle[ville] = villes[ville]
    return cycle




def distance_haversine(ville1, ville2, villes):
    R = 6371.0  # Rayon terre
    
    lat1, lon1 = villes[ville1]["latitude"], villes[ville1]["longitude"]
    lat2, lon2 = villes[ville2]["latitude"], villes[ville2]["longitude"]
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def calculer_distance_totale_vrp(routes, villes):
    distance_totale = 0
    for route in routes:
        for i in range(len(route) - 1):
            distance_totale += distance_haversine(route[i], route[i+1], villes)
    return distance_totale

def generer_solution_initiale_vrp(villes, nb_camions):
    villes_list = list(villes.keys())
    villes_list.remove("Nancy")  # enlver Nancy car c'est le dépôt
    
    # Initialiser les routes vides pour chaque camion
    routes = [["Nancy"] for _ in range(nb_camions)]
    
    # Distribuer les villes aléatoirement entre les camions
    villes_restantes = villes_list.copy()
    while villes_restantes:
        # camion aléatoire
        camion = random.randint(0, nb_camions - 1)
        # Choisir une ville aléatoire
        if villes_restantes:
            ville = random.choice(villes_restantes)
            routes[camion].append(ville)
            villes_restantes.remove(ville)
    
    # Ajouter Nancy à la fin de chaque route
    for route in routes:
        route.append("Nancy")
    
    return routes


def calculer_centre_gravite(route, villes):
    """
    Calcule le centre de gravité d'une route (moyenne des coordonnées)
    """
    if len(route) <= 2:  # Si la route ne contient que Nancy (début et fin)
        return villes["Nancy"]["latitude"], villes["Nancy"]["longitude"]
        
    latitudes = [villes[ville]["latitude"] for ville in route[1:-1]]  # Exclure Nancy
    longitudes = [villes[ville]["longitude"] for ville in route[1:-1]]
    
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)


def distance_ville_route(ville, route, villes):
    """
    Calcule la distance minimale entre une ville et n'importe quelle ville d'une route
    """
    if len(route) <= 2:  # Si la route ne contient que Nancy
        return 0
        
    min_distance = float('inf')
    for ville_route in route[1:-1]:  # Exclure Nancy
        dist = distance_haversine(ville, ville_route, villes)
        min_distance = min(min_distance, dist)
    return min_distance

def evaluer_pertinence_clustering(routes, ville, route_source, route_dest, villes):
    """
    Évalue si le déplacement d'une ville vers une autre route est pertinent
    selon des critères de clustering
    """
    # centres de gravité actuels
    cg_source = calculer_centre_gravite(route_source, villes)
    cg_dest = calculer_centre_gravite(route_dest, villes)
    
    # calcul des distances de la ville aux centres de gravité
    ville_lat, ville_lon = villes[ville]["latitude"], villes[ville]["longitude"]
    
    # Distance au centre de gravité de la route source
    dist_source = math.sqrt((ville_lat - cg_source[0])**2 + (ville_lon - cg_source[1])**2)
    
    # Distance au centre de gravité de la route destination
    dist_dest = math.sqrt((ville_lat - cg_dest[0])**2 + (ville_lon - cg_dest[1])**2)
    
    # Distance minimale aux villes de la route destination
    dist_min_dest = distance_ville_route(ville, route_dest, villes)
    
    # Critères de clustering
    SEUIL_DISTANCE = 200  # km
    
    
    return (dist_dest < dist_source and dist_min_dest < SEUIL_DISTANCE)

def generer_voisinage_vrp_clustering(routes, villes,minimum_voisin):
    voisins = []
    nb_voisins = min(minimum_voisin, len(routes) * len(routes[0]) * 2)
    
    for _ in range(nb_voisins):
        type_mouvement = random.choice(['intra', 'inter', 'insertion'])
        nouveau_voisin = deepcopy(routes)
        
        if type_mouvement == 'intra':
            # Échange intra-route (inchangé)
            route_idx = random.randint(0, len(routes) - 1)
            route = nouveau_voisin[route_idx]
            if len(route) > 3:
                i = random.randint(1, len(route) - 2)
                j = random.randint(1, len(route) - 2)
                while i == j:
                    j = random.randint(1, len(route) - 2)
                route[i], route[j] = route[j], route[i]
        
        elif type_mouvement == 'inter':
            # Échange inter-routes avec vérification clustering
            if len(routes) > 1:
                r1 = random.randint(0, len(routes) - 1)
                r2 = random.randint(0, len(routes) - 1)
                while r1 == r2:
                    r2 = random.randint(0, len(routes) - 1)
                
                if len(nouveau_voisin[r1]) > 2 and len(nouveau_voisin[r2]) > 2:
                    i = random.randint(1, len(nouveau_voisin[r1]) - 2)
                    j = random.randint(1, len(nouveau_voisin[r2]) - 2)
                    
                    # Vérifier si l'échange est pertinent selon le clustering
                    ville1 = nouveau_voisin[r1][i]
                    ville2 = nouveau_voisin[r2][j]
                    
                    if (evaluer_pertinence_clustering(routes, ville1, nouveau_voisin[r1], nouveau_voisin[r2], villes) or
                        evaluer_pertinence_clustering(routes, ville2, nouveau_voisin[r2], nouveau_voisin[r1], villes)):
                        nouveau_voisin[r1][i], nouveau_voisin[r2][j] = nouveau_voisin[r2][j], nouveau_voisin[r1][i]
        
        else:  # insertion
            # Déplacement avec vérification clustering
            if len(routes) > 1:
                r1 = random.randint(0, len(routes) - 1)
                r2 = random.randint(0, len(routes) - 1)
                while r1 == r2:
                    r2 = random.randint(0, len(routes) - 1)
                
                if len(nouveau_voisin[r1]) > 3:
                    pos1 = random.randint(1, len(nouveau_voisin[r1]) - 2)
                    ville = nouveau_voisin[r1][pos1]
                    
                    # Vérifier si le déplacement est pertinent selon le clustering
                    if evaluer_pertinence_clustering(routes, ville, nouveau_voisin[r1], nouveau_voisin[r2], villes):
                        ville_deplacee = nouveau_voisin[r1].pop(pos1)
                        pos2 = random.randint(1, len(nouveau_voisin[r2]) - 1)
                        nouveau_voisin[r2].insert(pos2, ville_deplacee)
        
        if nouveau_voisin not in voisins:
            voisins.append(nouveau_voisin)
    
    return voisins

def recherche_tabou_vrp_clustering(villes, nb_camions, max_iterations, taille_liste_tabou,minimum_voisin):
    # Même fonction que recherche_tabou_vrp mais utilisant generer_voisinage_vrp_clustering
    solution_courante = generer_solution_initiale_vrp(villes, nb_camions)
    meilleure_solution = deepcopy(solution_courante)
    meilleure_distance = calculer_distance_totale_vrp(solution_courante, villes)
    
    liste_tabou = []
    iterations_sans_amelioration = 0
    
    for iteration in range(max_iterations):
        voisins = generer_voisinage_vrp_clustering(solution_courante, villes,minimum_voisin)  
        meilleur_voisin = None
        meilleure_distance_voisin = float('inf')
        
        for voisin in voisins:
            distance_voisin = calculer_distance_totale_vrp(voisin, villes)
            mouvement = tuple(tuple(route[1:-1]) for route in voisin)
            
            if mouvement not in liste_tabou or distance_voisin < meilleure_distance:
                if distance_voisin < meilleure_distance_voisin:
                    meilleur_voisin = voisin
                    meilleure_distance_voisin = distance_voisin
        
        if meilleur_voisin is None:
            continue
        
        solution_courante = deepcopy(meilleur_voisin)
        
        if meilleure_distance_voisin < meilleure_distance:
            meilleure_solution = deepcopy(meilleur_voisin)
            meilleure_distance = meilleure_distance_voisin
            iterations_sans_amelioration = 0
        else:
            iterations_sans_amelioration += 1
        
        mouvement = tuple(tuple(route[1:-1]) for route in meilleur_voisin)
        liste_tabou.append(mouvement)
        if len(liste_tabou) > taille_liste_tabou:
            liste_tabou.pop(0)
        
        if iterations_sans_amelioration > 50:
            break
    
    return meilleure_solution, meilleure_distance


# def afficher_solution_vrp(routes, distance_totale):
#     print(f"\nDistance totale pour tous les camions : {distance_totale:.2f} km")
#     print("\nItinéraires par camion :")
#     for i, route in enumerate(routes):
#         distance_route = sum(distance_haversine(route[j], route[j+1], villes_france) 
#                            for j in range(len(route)-1))
#         print(f"\nCamion {i+1} (Distance : {distance_route:.2f} km):")
#         print(' -> '.join(route))




#cycle1, cycle2, cycle3 = afficher_solution_formatee(meilleure_solution, villes_france)  #prendre le resultat pour le geopanda

# print("cycle1 = ", cycle1,"\n")
# print("cycle2 = ", cycle2,"\n")
# print("cycle3 = ", cycle3,"\n")
