from pulp import *
import numpy as np
import random
from itertools import combinations
from math import radians, cos, sin, asin, sqrt
import time
import folium
from branca.colormap import LinearColormap

class VRPSolver:
    def __init__(self, coordinates, demandes, nb_vehicules, capacite_max, depot_ville):
        self.coordinates = coordinates
        self.demandes = demandes
        self.nb_vehicules = nb_vehicules
        self.capacite_max = capacite_max
        self.depot_ville = depot_ville
        self.villes = list(demandes.keys())
        self.distances = self._calculer_distances()
        self.temps_execution = 0

    def _calculer_distances(self):
        """Calcule la matrice des distances entre toutes les villes"""
        distances = {}
        villes = list(self.coordinates.keys())
        
        for ville1, ville2 in combinations(villes, 2):
            lat1, lon1 = self.coordinates[ville1]
            lat2, lon2 = self.coordinates[ville2]
            
            # Conversion en radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Formule de Haversine
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Rayon de la Terre en km
            
            distance = c * r
            distances[ville1, ville2] = distance
            distances[ville2, ville1] = distance
            
        return distances

    def _solution_initiale(self):
        """Génère une solution initiale en répartissant les villes de façon équilibrée entre les camions"""
        villes_non_assignees = self.villes.copy()
        solution = [[] for _ in range(self.nb_vehicules)]

        # Initialisation : attribuer une ville à chaque camion
        for i in range(min(self.nb_vehicules, len(villes_non_assignees))):
            ville = villes_non_assignees.pop(0)
            solution[i].append(ville)

        # Répartir les villes restantes
        for ville in villes_non_assignees:
            assigned = False
            while not assigned:
                vehicule = random.randint(0, self.nb_vehicules - 1)
                charge_actuelle = sum(self.demandes[v] for v in solution[vehicule])
                if charge_actuelle + self.demandes[ville] <= self.capacite_max:
                    solution[vehicule].append(ville)
                    assigned = True

        return solution

    def _evaluer_solution(self, solution):
        """Calcule le coût total d'une solution"""
        cout_total = 0
        
        for route in solution:
            if not route:
                continue

            cout_total += self.distances[self.depot_ville, route[0]]
            
            for i in range(len(route) - 1):
                cout_total += self.distances[route[i], route[i+1]]
            
            cout_total += self.distances[route[-1], self.depot_ville]
                
        return cout_total

    def trouver_solution_optimale(self, max_iterations=1000):
        """Exécute l'algorithme pour trouver une solution optimale"""
        debut = time.time()
        
        # Solution initiale
        meilleure_solution = self._solution_initiale()
        cout_meilleur = self._evaluer_solution(meilleure_solution)
        
        # Boucle principale
        for iteration in range(max_iterations):
            # Générer une nouvelle solution aléatoire
            nouvelle_solution = self._solution_initiale()
            
            # Évaluer la nouvelle solution
            cout_nouvelle = self._evaluer_solution(nouvelle_solution)
            
            # Mettre à jour la meilleure solution si nécessaire
            if cout_nouvelle < cout_meilleur:
                meilleure_solution = nouvelle_solution
                cout_meilleur = cout_nouvelle
        
        self.temps_execution = time.time() - debut
        return meilleure_solution, cout_meilleur

def afficher_solution(solution, demandes, distances, depot_ville, temps_execution):
    """Affiche les détails de la solution avec le temps de trajet estimé"""
    vitesse_moyenne = 100 # Vitesse moyenne en km/h
    print("\nSolution trouvée:")
    cout_total = 0

    for i, route in enumerate(solution):
        if not route:
            continue
            
        print(f"\nRoute {i+1}:")
        print(f"  {depot_ville} -> ", end="")
        charge = 0
        distance_route = distances[depot_ville, route[0]]
        
        for j in range(len(route)):
            ville = route[j]
            print(f"{ville} -> ", end="")
            charge += demandes[ville]
            
            if j < len(route) - 1:
                distance_route += distances[ville, route[j+1]]
        
        distance_route += distances[route[-1], depot_ville]
        print(depot_ville)
        
        # Calcul du temps de trajet pour la route
        temps_trajet = distance_route / vitesse_moyenne
        print(f"  Distance: {distance_route:.2f} km")
        print(f"  Charge: {charge} kg")
        print(f"  Temps de trajet: {temps_trajet:.2f} heures")
        cout_total += distance_route
    
    temps_total = cout_total / vitesse_moyenne
    print(f"\nDistance totale: {cout_total:.2f} km")
    print(f"Temps de trajet total: {temps_total:.2f} heures")
    print(f"Temps d'exécution: {temps_execution:.2f} secondes")

def afficher_solution_carte(solution, coordinates, depot_ville, demandes):
    """Affiche la solution sur une carte interactive"""
    france_center = [46.603354, 1.888334]
    m = folium.Map(location=france_center, zoom_start=6)
    
    colors = ['#FF0000', '#0000FF', '#008000', '#FFA500', '#800080']
    
    folium.CircleMarker(
        location=coordinates[depot_ville],
        radius=10,
        color='black',
        fill=True,
        popup=f'Dépôt: {depot_ville}',
        weight=3
    ).add_to(m)
    
    for i, route in enumerate(solution):
        if not route:
            continue
        
        color = colors[i % len(colors)]
        
        folium.PolyLine(
            locations=[coordinates[depot_ville], coordinates[route[0]]],
            color=color,
            weight=2,
            opacity=0.8
        ).add_to(m)
        
        for j, ville in enumerate(route):
            folium.CircleMarker(
                location=coordinates[ville],
                radius=8,
                color=color,
                fill=True,
                popup=f'Ville: {ville}<br>Demande: {demandes[ville]}kg',
                weight=2
            ).add_to(m)
            
            if j < len(route) - 1:
                folium.PolyLine(
                    locations=[coordinates[ville], coordinates[route[j + 1]]],
                    color=color,
                    weight=2,
                    opacity=0.8
                ).add_to(m)
        
        folium.PolyLine(
            locations=[coordinates[route[-1]], coordinates[depot_ville]],
            color=color,
            weight=2,
            opacity=0.8
        ).add_to(m)
    
    legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
        padding: 10px; border: 2px solid grey; border-radius: 5px">
        <h4>Légende</h4>
        <p><span style="color: black;">● </span>Dépôt</p>
    '''
    
    for i, color in enumerate(colors[:len([route for route in solution if route])]):
        legend_html += f'<p><span style="color: {color};">●</span> Route {i + 1}</p>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

if __name__ == "__main__":
    coordinates = {
        "Nancy": (48.6921, 6.1844),
        "Paris": (48.8566, 2.3522),
        "Reims": (49.2583, 4.0317),
        "Orléans": (47.9029, 1.9093),
        "Auxerre": (47.7982, 3.5734),
        "Dijon": (47.3220, 5.0415),
        "Metz": (49.1193, 6.1757)
    }
    
    demandes = {
        "Paris": 150,
        "Reims": 130,
        "Orléans": 140,
        "Auxerre": 110,
        "Dijon": 160,
        "Metz": 120
    }
    
    nb_vehicules = 3
    capacite_max = 500  # kg
    
    print("\nDémarrage de l'optimisation...")
    
    solver = VRPSolver(
        coordinates=coordinates,
        demandes=demandes,
        nb_vehicules=nb_vehicules,
        capacite_max=capacite_max,
        depot_ville="Nancy"
    )
    
    solution, cout_total = solver.trouver_solution_optimale()
    afficher_solution(solution, demandes, solver.distances, "Nancy", solver.temps_execution)
    
    carte = afficher_solution_carte(solution, coordinates, "Nancy", demandes)
    carte.save("solution_final_temps_pulp.html")
    print("\nCarte enregistrée sous 'solution_final_temps_pulp.html'")
